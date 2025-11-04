# Token Control System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement intelligent Keepa token control to prevent API exhaustion through guard decorators and business-level action costs.

**Architecture:** Three-layer system with centralized TOKEN_COSTS registry, FastAPI guard decorator with dependency injection, and enhanced KeepaService for balance checking. Uses pre-execution validation with graceful degradation.

**Tech Stack:** FastAPI, Python decorators, async/await, pytest, existing KeepaService infrastructure

---

## Phase 1: Core Infrastructure

### Task 1: Create Token Costs Registry

**Files:**
- Create: `backend/app/core/token_costs.py`

**Step 1: Write the failing test**

```python
# backend/tests/core/test_token_costs.py
import pytest
from app.core.token_costs import TOKEN_COSTS, CRITICAL_THRESHOLD, WARNING_THRESHOLD

def test_token_costs_structure():
    """TOKEN_COSTS has correct structure with all required fields"""
    assert "surprise_me" in TOKEN_COSTS
    action = TOKEN_COSTS["surprise_me"]
    assert "cost" in action
    assert "description" in action
    assert "endpoint_type" in action
    assert isinstance(action["cost"], int)

def test_thresholds_defined():
    """Safety thresholds are properly defined"""
    assert CRITICAL_THRESHOLD == 20
    assert WARNING_THRESHOLD == 100
    assert CRITICAL_THRESHOLD < WARNING_THRESHOLD
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/core/test_token_costs.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.core.token_costs'"

**Step 3: Write minimal implementation**

```python
# backend/app/core/token_costs.py
"""
Keepa Token Cost Registry
Defines business-level action costs and safety thresholds
"""
from typing import TypedDict

class ActionCost(TypedDict):
    cost: int
    description: str
    endpoint_type: str

TOKEN_COSTS: dict[str, ActionCost] = {
    "surprise_me": {
        "cost": 50,
        "description": "Generate random niche via bestsellers",
        "endpoint_type": "single"
    },
    "niche_discovery": {
        "cost": 150,
        "description": "Discover 3 niches (3x bestsellers)",
        "endpoint_type": "composite"
    },
    "manual_search": {
        "cost": 10,
        "description": "Manual product search with filters",
        "endpoint_type": "single"
    },
    "product_lookup": {
        "cost": 1,
        "description": "Single ASIN analysis",
        "endpoint_type": "single"
    },
    "auto_sourcing_job": {
        "cost": 200,
        "description": "Full AutoSourcing discovery run",
        "endpoint_type": "batch"
    },
}

CRITICAL_THRESHOLD = 20
WARNING_THRESHOLD = 100
SAFE_THRESHOLD = 200
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/core/test_token_costs.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
cd .worktrees/feature/token-control
git add backend/app/core/token_costs.py backend/tests/core/test_token_costs.py
git commit -m "feat(core): add TOKEN_COSTS registry with business action costs

Centralized definition of Keepa token costs per business action.
Includes safety thresholds (CRITICAL=20, WARNING=100).
Decouples business logic from Keepa API internals.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: Add can_perform_action to KeepaService

**Files:**
- Modify: `backend/app/services/keepa_service.py`
- Create: `backend/tests/services/test_keepa_token_control.py`

**Step 1: Write the failing test**

```python
# backend/tests/services/test_keepa_token_control.py
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.keepa_service import KeepaService
from app.core.token_costs import TOKEN_COSTS

@pytest.mark.asyncio
async def test_can_perform_action_sufficient_tokens():
    """can_perform_action returns True when balance sufficient"""
    keepa = KeepaService(api_key="test_key")
    keepa.check_api_balance = AsyncMock(return_value=100)

    can_proceed, balance, needed = await keepa.can_perform_action("product_lookup")

    assert can_proceed is True
    assert balance == 100
    assert needed == 1

@pytest.mark.asyncio
async def test_can_perform_action_insufficient_tokens():
    """can_perform_action returns False when balance insufficient"""
    keepa = KeepaService(api_key="test_key")
    keepa.check_api_balance = AsyncMock(return_value=10)

    can_proceed, balance, needed = await keepa.can_perform_action("surprise_me")

    assert can_proceed is False
    assert balance == 10
    assert needed == 50

@pytest.mark.asyncio
async def test_can_perform_action_below_critical_threshold():
    """can_perform_action blocks all actions when below critical threshold"""
    keepa = KeepaService(api_key="test_key")
    keepa.check_api_balance = AsyncMock(return_value=5)

    can_proceed, balance, needed = await keepa.can_perform_action("product_lookup")

    assert can_proceed is False
    assert balance == 5
    assert needed == 1

@pytest.mark.asyncio
async def test_can_perform_action_unknown_action():
    """can_perform_action raises ValueError for unknown action"""
    keepa = KeepaService(api_key="test_key")

    with pytest.raises(ValueError, match="Unknown action"):
        await keepa.can_perform_action("invalid_action")
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/services/test_keepa_token_control.py -v`
Expected: FAIL with "AttributeError: 'KeepaService' object has no attribute 'can_perform_action'"

**Step 3: Write minimal implementation**

Add this method to `backend/app/services/keepa_service.py` (after existing methods):

```python
async def can_perform_action(self, action: str) -> tuple[bool, int, int]:
    """
    Check if we have sufficient tokens for a business action.

    Args:
        action: Business action name from TOKEN_COSTS

    Returns:
        Tuple of (can_proceed, balance_available, tokens_required)

    Example:
        can_proceed, balance, needed = await keepa.can_perform_action("surprise_me")
        if not can_proceed:
            raise InsufficientTokensError(balance, needed, "surprise_me")
    """
    from ..core.token_costs import TOKEN_COSTS, CRITICAL_THRESHOLD

    action_config = TOKEN_COSTS.get(action)
    if not action_config:
        raise ValueError(f"Unknown action '{action}' in TOKEN_COSTS")

    required_tokens = action_config["cost"]

    current_balance = await self.check_api_balance()

    if current_balance < CRITICAL_THRESHOLD:
        logger.error(
            f"CRITICAL: Keepa balance {current_balance} below threshold {CRITICAL_THRESHOLD}. "
            f"Blocking all actions."
        )
        return (False, current_balance, required_tokens)

    can_proceed = current_balance >= required_tokens

    if not can_proceed:
        logger.warning(
            f"Insufficient tokens for '{action}': {current_balance}/{required_tokens}"
        )

    return (can_proceed, current_balance, required_tokens)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/services/test_keepa_token_control.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
cd .worktrees/feature/token-control
git add backend/app/services/keepa_service.py backend/tests/services/test_keepa_token_control.py
git commit -m "feat(keepa): add can_perform_action method for token validation

Returns (can_proceed, balance, required) tuple for business actions.
Enforces global CRITICAL_THRESHOLD protection.
Reuses existing check_api_balance infrastructure.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: Create Guard Decorator

**Files:**
- Create: `backend/app/core/guards/__init__.py`
- Create: `backend/app/core/guards/require_tokens.py`
- Create: `backend/tests/core/guards/test_require_tokens.py`

**Step 1: Write the failing test**

```python
# backend/tests/core/guards/test_require_tokens.py
import pytest
from unittest.mock import AsyncMock, Mock
from app.core.guards.require_tokens import require_tokens
from app.core.exceptions import InsufficientTokensError
from app.services.keepa_service import KeepaService

@pytest.mark.asyncio
async def test_decorator_allows_execution_when_sufficient_tokens():
    """Decorator allows execution when tokens sufficient"""
    mock_keepa = Mock(spec=KeepaService)
    mock_keepa.can_perform_action = AsyncMock(return_value=(True, 100, 50))

    @require_tokens("surprise_me")
    async def test_endpoint(keepa: KeepaService):
        return {"status": "ok"}

    result = await test_endpoint(keepa=mock_keepa)

    assert result == {"status": "ok"}
    mock_keepa.can_perform_action.assert_called_once_with("surprise_me")

@pytest.mark.asyncio
async def test_decorator_blocks_when_insufficient_tokens():
    """Decorator raises InsufficientTokensError when tokens low"""
    mock_keepa = Mock(spec=KeepaService)
    mock_keepa.can_perform_action = AsyncMock(return_value=(False, 10, 50))

    @require_tokens("surprise_me")
    async def test_endpoint(keepa: KeepaService):
        return {"status": "ok"}

    with pytest.raises(InsufficientTokensError) as exc_info:
        await test_endpoint(keepa=mock_keepa)

    assert exc_info.value.details["current_balance"] == 10
    assert exc_info.value.details["required_tokens"] == 50

@pytest.mark.asyncio
async def test_decorator_requires_keepa_parameter():
    """Decorator raises ValueError if keepa parameter missing"""
    @require_tokens("surprise_me")
    async def test_endpoint():
        return {"status": "ok"}

    with pytest.raises(ValueError, match="requires 'keepa: KeepaService'"):
        await test_endpoint()

@pytest.mark.asyncio
async def test_decorator_validates_action_exists():
    """Decorator raises ValueError for unknown action"""
    mock_keepa = Mock(spec=KeepaService)

    @require_tokens("unknown_action")
    async def test_endpoint(keepa: KeepaService):
        return {"status": "ok"}

    with pytest.raises(ValueError, match="not found in TOKEN_COSTS"):
        await test_endpoint(keepa=mock_keepa)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/core/guards/test_require_tokens.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.core.guards'"

**Step 3: Write minimal implementation**

```python
# backend/app/core/guards/__init__.py
"""Guards for endpoint protection"""
from .require_tokens import require_tokens

__all__ = ["require_tokens"]
```

```python
# backend/app/core/guards/require_tokens.py
"""
Token Guard Decorator
Enforces token balance check before endpoint execution
"""
from functools import wraps
from typing import Callable
import logging

from ..token_costs import TOKEN_COSTS
from ...services.keepa_service import KeepaService
from ..exceptions import InsufficientTokensError

logger = logging.getLogger(__name__)

def require_tokens(action: str):
    """
    Decorator to enforce token balance check before endpoint execution.

    Args:
        action: Business action name from TOKEN_COSTS

    Raises:
        InsufficientTokensError: If tokens < required amount
        ValueError: If action not in TOKEN_COSTS or keepa param missing

    Usage:
        @require_tokens("surprise_me")
        async def discover_niches(keepa: KeepaService = Depends(...)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            keepa: KeepaService = kwargs.get("keepa")
            if not keepa:
                raise ValueError(
                    f"@require_tokens decorator requires 'keepa: KeepaService = Depends(...)' "
                    f"parameter in function {func.__name__}"
                )

            action_config = TOKEN_COSTS.get(action)
            if not action_config:
                logger.error(f"Unknown action '{action}' in @require_tokens")
                raise ValueError(f"Action '{action}' not found in TOKEN_COSTS")

            required_tokens = action_config["cost"]

            can_proceed, balance, _ = await keepa.can_perform_action(action)

            if not can_proceed:
                logger.warning(
                    f"[Token Guard] Action '{action}' blocked: "
                    f"{balance}/{required_tokens} tokens available. "
                    f"Description: {action_config['description']}"
                )

                raise InsufficientTokensError(
                    current_balance=balance,
                    required_tokens=required_tokens,
                    endpoint=action
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/core/guards/test_require_tokens.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
cd .worktrees/feature/token-control
git add backend/app/core/guards/ backend/tests/core/guards/
git commit -m "feat(guards): add @require_tokens decorator for endpoint protection

Async decorator enforces token balance via FastAPI dependency injection.
Logs refusals with context, raises InsufficientTokensError on failure.
Validates action exists in TOKEN_COSTS at decoration time.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Phase 2: Endpoint Integration

### Task 4: Integrate Guard into Niche Discovery Endpoint

**Files:**
- Modify: `backend/app/api/v1/endpoints/niches.py`
- Create: `backend/tests/api/v1/test_niches_token_guard.py`

**Step 1: Write the failing integration test**

```python
# backend/tests/api/v1/test_niches_token_guard.py
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.keepa_service import KeepaService, get_keepa_service

@pytest.fixture
def mock_keepa_sufficient():
    """Mock KeepaService with sufficient tokens"""
    mock = Mock(spec=KeepaService)
    mock.can_perform_action = AsyncMock(return_value=(True, 100, 50))
    return mock

@pytest.fixture
def mock_keepa_insufficient():
    """Mock KeepaService with insufficient tokens"""
    mock = Mock(spec=KeepaService)
    mock.can_perform_action = AsyncMock(return_value=(False, 10, 50))
    return mock

def test_discover_niches_blocks_on_insufficient_tokens(mock_keepa_insufficient):
    """Integration test: endpoint returns 429 when tokens insufficient"""
    app.dependency_overrides[get_keepa_service] = lambda: mock_keepa_insufficient

    client = TestClient(app)
    response = client.get("/api/v1/niches/discover")

    assert response.status_code == 429
    data = response.json()
    assert "detail" in data
    assert data["detail"]["current_balance"] == 10
    assert data["detail"]["required_tokens"] == 50
    assert data["detail"]["endpoint"] == "surprise_me"

    app.dependency_overrides.clear()

def test_discover_niches_allows_with_sufficient_tokens(mock_keepa_sufficient):
    """Integration test: endpoint executes when tokens sufficient"""
    app.dependency_overrides[get_keepa_service] = lambda: mock_keepa_sufficient

    with patch("app.api.v1.endpoints.niches.discover_niches_logic") as mock_logic:
        mock_logic.return_value = {"niches": []}

        client = TestClient(app)
        response = client.get("/api/v1/niches/discover")

        assert response.status_code == 200
        mock_logic.assert_called_once()

    app.dependency_overrides.clear()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/api/v1/test_niches_token_guard.py -v`
Expected: FAIL (decorator not applied yet, no 429 response)

**Step 3: Apply decorator to endpoint**

Modify `backend/app/api/v1/endpoints/niches.py`:

```python
# Add import at top
from app.core.guards import require_tokens

# Modify discover endpoint
@router.get("/discover")
@require_tokens("surprise_me")  # ADD THIS LINE
async def discover_niches(
    count: int = Query(default=3, ge=1, le=5),
    shuffle: bool = Query(default=True),
    keepa: KeepaService = Depends(get_keepa_service)
):
    """
    Discover curated niches with automatic token protection.

    Decorator ensures we have 50 tokens before execution.
    Returns HTTP 429 if insufficient tokens.
    """
    # Existing implementation unchanged
    ...
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/api/v1/test_niches_token_guard.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
cd .worktrees/feature/token-control
git add backend/app/api/v1/endpoints/niches.py backend/tests/api/v1/test_niches_token_guard.py
git commit -m "feat(niches): add token guard to discover endpoint

Protects /api/v1/niches/discover with @require_tokens('surprise_me').
Returns HTTP 429 with structured error when tokens insufficient.
Integration tests verify both success and failure paths.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: Integrate Guard into Manual Search Endpoint

**Files:**
- Modify: `backend/app/api/v1/endpoints/products.py`
- Create: `backend/tests/api/v1/test_products_token_guard.py`

**Step 1: Write the failing integration test**

```python
# backend/tests/api/v1/test_products_token_guard.py
import pytest
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient
from app.main import app
from app.services.keepa_service import get_keepa_service

def test_discover_with_scoring_blocks_on_insufficient_tokens():
    """Integration test: manual search blocked when tokens low"""
    mock_keepa = Mock()
    mock_keepa.can_perform_action = AsyncMock(return_value=(False, 5, 10))

    app.dependency_overrides[get_keepa_service] = lambda: mock_keepa

    client = TestClient(app)
    response = client.post("/api/v1/products/discover-with-scoring", json={
        "category": 283155,
        "bsr_max": 50000,
        "min_roi": 30
    })

    assert response.status_code == 429
    data = response.json()
    assert data["detail"]["current_balance"] == 5
    assert data["detail"]["required_tokens"] == 10

    app.dependency_overrides.clear()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/api/v1/test_products_token_guard.py -v`
Expected: FAIL (no 429 response yet)

**Step 3: Apply decorator to endpoint**

Modify `backend/app/api/v1/endpoints/products.py`:

```python
# Add import at top
from app.core.guards import require_tokens

# Modify endpoint
@router.post("/discover-with-scoring")
@require_tokens("manual_search")  # ADD THIS LINE
async def discover_with_scoring(
    filters: ProductFilters,
    keepa: KeepaService = Depends(get_keepa_service)
):
    """
    Manual product discovery with scoring.

    Protected by token guard - requires 10 tokens.
    """
    # Existing implementation unchanged
    ...
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/api/v1/test_products_token_guard.py -v`
Expected: PASS (1 test)

**Step 5: Commit**

```bash
cd .worktrees/feature/token-control
git add backend/app/api/v1/endpoints/products.py backend/tests/api/v1/test_products_token_guard.py
git commit -m "feat(products): add token guard to manual search endpoint

Protects /api/v1/products/discover-with-scoring with manual_search cost.
Prevents expensive searches when token balance insufficient.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 6: Add Explicit Check to AutoSourcing Service

**Files:**
- Modify: `backend/app/services/autosourcing_service.py`
- Create: `backend/tests/services/test_autosourcing_token_control.py`

**Step 1: Write the failing test**

```python
# backend/tests/services/test_autosourcing_token_control.py
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.services.autosourcing_service import run_autosourcing_job

@pytest.mark.asyncio
async def test_autosourcing_skips_on_insufficient_tokens():
    """AutoSourcing job skips gracefully when tokens insufficient"""
    mock_keepa = Mock()
    mock_keepa.can_perform_action = AsyncMock(return_value=(False, 50, 200))

    with patch("app.services.autosourcing_service.get_keepa_service", return_value=mock_keepa):
        with patch("app.services.autosourcing_service.update_job_status") as mock_update:
            await run_autosourcing_job("job_123")

            mock_update.assert_called_once_with(
                "job_123",
                status="SKIPPED_NO_TOKENS",
                message="Insufficient tokens: 50/200 available"
            )

@pytest.mark.asyncio
async def test_autosourcing_proceeds_with_sufficient_tokens():
    """AutoSourcing job proceeds when tokens sufficient"""
    mock_keepa = Mock()
    mock_keepa.can_perform_action = AsyncMock(return_value=(True, 300, 200))

    with patch("app.services.autosourcing_service.get_keepa_service", return_value=mock_keepa):
        with patch("app.services.autosourcing_service.execute_autosourcing_logic") as mock_execute:
            await run_autosourcing_job("job_456")

            mock_execute.assert_called_once_with("job_456", mock_keepa)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/services/test_autosourcing_token_control.py -v`
Expected: FAIL (function doesn't check tokens yet)

**Step 3: Add explicit token check**

Modify `backend/app/services/autosourcing_service.py`:

```python
async def run_autosourcing_job(job_id: str):
    """
    AutoSourcing job with graceful degradation.

    Uses explicit check instead of decorator to handle
    skipping gracefully without raising exception.
    """
    keepa = get_keepa_service()

    # ADD THIS BLOCK
    can_proceed, balance, needed = await keepa.can_perform_action("auto_sourcing_job")

    if not can_proceed:
        logger.warning(
            f"AutoSourcing job {job_id} SKIPPED: insufficient tokens "
            f"({balance}/{needed}). Will retry after token refresh."
        )

        await update_job_status(
            job_id,
            status="SKIPPED_NO_TOKENS",
            message=f"Insufficient tokens: {balance}/{needed} available"
        )
        return

    # Existing execution logic
    logger.info(f"AutoSourcing job {job_id} starting with {balance} tokens available")
    await execute_autosourcing_logic(job_id, keepa)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/services/test_autosourcing_token_control.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
cd .worktrees/feature/token-control
git add backend/app/services/autosourcing_service.py backend/tests/services/test_autosourcing_token_control.py
git commit -m "feat(autosourcing): add graceful token check with skip logic

Explicit can_perform_action check before batch job execution.
Skips job with SKIPPED_NO_TOKENS status instead of raising error.
Enables graceful degradation for automated workflows.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Phase 3: Documentation & Monitoring

### Task 7: Update API Documentation

**Files:**
- Modify: `backend/app/api/v1/endpoints/niches.py` (docstrings)
- Modify: `backend/app/api/v1/endpoints/products.py` (docstrings)

**Step 1: Update endpoint docstrings**

```python
# backend/app/api/v1/endpoints/niches.py
@router.get("/discover")
@require_tokens("surprise_me")
async def discover_niches(...):
    """
    Discover curated niches with automatic token protection.

    This endpoint uses the Keepa bestsellers API which costs 50 tokens per call.
    The @require_tokens decorator ensures sufficient balance before execution.

    Returns:
        - 200: List of discovered niches
        - 429: Insufficient tokens (see response body for details)

    Token Cost: 50 tokens

    Example 429 Response:
        {
            "detail": {
                "message": "Insufficient Keepa tokens: 15 available, 50 required",
                "current_balance": 15,
                "required_tokens": 50,
                "endpoint": "surprise_me",
                "deficit": 35
            }
        }
    """
    ...
```

```python
# backend/app/api/v1/endpoints/products.py
@router.post("/discover-with-scoring")
@require_tokens("manual_search")
async def discover_with_scoring(...):
    """
    Manual product discovery with ROI and velocity scoring.

    This endpoint uses the Keepa search API which costs 10 tokens per query.
    The @require_tokens decorator prevents execution when balance insufficient.

    Token Cost: 10 tokens

    Returns:
        - 200: Scored products matching filters
        - 429: Insufficient tokens (retry after daily refresh)
    """
    ...
```

**Step 2: Commit documentation**

```bash
cd .worktrees/feature/token-control
git add backend/app/api/v1/endpoints/niches.py backend/app/api/v1/endpoints/products.py
git commit -m "docs(api): add token cost and 429 response documentation

Documents token costs and HTTP 429 responses in endpoint docstrings.
Provides example error response format for API consumers.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 8: Update Memory Context Files

**Files:**
- Modify: `.claude/memory/compact_current.md`

**Step 1: Add token control section**

Add to `compact_current.md` after existing bugs section:

```markdown
### [2025-11-03] FEATURE - Intelligent Token Control System

**Status**: Implemented and deployed

**Components**:
1. TOKEN_COSTS registry (business-level action costs)
2. @require_tokens guard decorator with FastAPI injection
3. can_perform_action() in KeepaService
4. Integration in /niches/discover and /products/discover-with-scoring
5. Graceful degradation in AutoSourcing batch jobs

**Token Costs**:
- surprise_me: 50 tokens (bestsellers)
- niche_discovery: 150 tokens (3x bestsellers)
- manual_search: 10 tokens (search)
- product_lookup: 1 token (product)
- auto_sourcing_job: 200 tokens (conservative estimate)

**Safety Thresholds**:
- CRITICAL: 20 tokens (blocks all actions)
- WARNING: 100 tokens (logs warning)
- SAFE: 200+ tokens (healthy state)

**Behavior**:
- Endpoints return HTTP 429 when tokens insufficient
- AutoSourcing jobs skip with SKIPPED_NO_TOKENS status
- All refusals logged with context for monitoring

**Testing**:
- 11 unit tests (TOKEN_COSTS, decorator, service method)
- 4 integration tests (endpoint protection, error responses)
- Full coverage of success and failure paths
```

**Step 2: Commit context update**

```bash
cd .worktrees/feature/token-control
git add .claude/memory/compact_current.md
git commit -m "docs(memory): add token control system to context

Documents new intelligent token control architecture.
Updates memory with costs, thresholds, and behavior.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Phase 4: Validation & Deployment

### Task 9: Run Full Test Suite

**Step 1: Run all new tests**

```bash
cd .worktrees/feature/token-control/backend
python -m pytest tests/core/test_token_costs.py -v
python -m pytest tests/services/test_keepa_token_control.py -v
python -m pytest tests/core/guards/test_require_tokens.py -v
python -m pytest tests/api/v1/test_niches_token_guard.py -v
python -m pytest tests/api/v1/test_products_token_guard.py -v
python -m pytest tests/services/test_autosourcing_token_control.py -v
```

Expected: All tests PASS (15+ tests total)

**Step 2: Run existing tests to ensure no regression**

```bash
cd .worktrees/feature/token-control/backend
python -m pytest tests/ -v --tb=short
```

Expected: All existing tests still PASS

**Step 3: Document test results**

```bash
cd .worktrees/feature/token-control
git add -A
git commit -m "test: verify full test suite passes with token control

All 15 new tests passing (costs, service, decorator, integration).
No regressions in existing test suite.
Ready for deployment.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 10: Merge to Main and Deploy

**Step 1: Switch back to main worktree**

```bash
cd ../../  # Back to main worktree root
```

**Step 2: Merge feature branch**

```bash
git checkout main
git merge feature/token-control --no-ff
```

**Step 3: Push to trigger Render deployment**

```bash
git push origin main
```

**Step 4: Monitor deployment**

- Watch Render dashboard for successful deploy
- Check `/health` endpoint responds
- Verify `/api/v1/keepa/health` shows token balance

**Step 5: Validate in production**

```bash
# Test with low balance simulation (if possible)
curl -X GET https://arbitragevault-backend-v2.onrender.com/api/v1/niches/discover

# Check logs for token guard messages
# Render dashboard > Logs > Filter: "[Token Guard]"
```

---

## Testing Strategy Summary

**Unit Tests (11 tests):**
- TOKEN_COSTS structure validation
- can_perform_action logic (sufficient/insufficient/critical)
- Decorator behavior (allow/block/validate)

**Integration Tests (4 tests):**
- Niche discovery endpoint protection
- Manual search endpoint protection
- HTTP 429 response format validation

**Service Tests (2 tests):**
- AutoSourcing graceful skip
- AutoSourcing proceed with sufficient tokens

**Total Coverage:** 17 tests covering all components and integration points

---

## Rollback Plan

If issues arise post-deployment:

```bash
# Immediate rollback
git revert $(git log --grep="token-control" --format="%H" | head -1)
git push origin main

# Remove decorator from critical endpoints
# Revert: backend/app/api/v1/endpoints/niches.py
# Revert: backend/app/api/v1/endpoints/products.py

# Trigger Render redeploy
# Monitor logs for stability
```

---

## Success Criteria

- [ ] All 17 tests passing
- [ ] No regressions in existing functionality
- [ ] HTTP 429 responses contain actionable error messages
- [ ] AutoSourcing gracefully skips when tokens low
- [ ] Decorator adds < 50ms latency per request
- [ ] Token balance never goes negative in production
- [ ] All token refusals logged with context

---

## Implementation Notes

**DRY Principles:**
- Centralized TOKEN_COSTS (single source of truth)
- Reusable decorator across all endpoints
- Shared can_perform_action logic

**YAGNI Principles:**
- No predictive warnings (implement later if needed)
- No token pool sharing (single user for now)
- No dynamic pricing (Keepa costs stable)

**TDD Principles:**
- Write test first for every component
- Verify failure before implementation
- Commit after each green test

**Frequent Commits:**
- One commit per completed task
- Clear commit messages with context
- Co-authored with Claude for attribution

---

**Plan Complete** | Ready for execution via superpowers:executing-plans or superpowers:subagent-driven-development
