# Keepa Token Control System - Design Document

**Date**: 2025-11-03
**Status**: Approved
**Author**: Aziz (avec Claude Code)

---

## Context & Problem Statement

ArbitrageVault uses Keepa API for product analysis, with a limited token budget (20 tokens/minute, daily reset). Recent production incidents showed **tokens depleted brutally** (193 → -17 in 1 second) due to uncontrolled API calls, causing:

- Feature failures (Surprise Me, Manual Search, AutoSourcing)
- Poor user experience (silent failures, no warnings)
- Risk of Keepa account suspension

**Goal**: Implement intelligent token control to prevent exhaustion while maintaining system usability.

---

## Design Decisions

### 1. Architecture Choice: Guard Decorator Pattern

**Selected Approach**: `@require_tokens("action")` decorator with FastAPI dependency injection

**Alternatives Considered**:
- ❌ **Explicit checks in routes**: DRY violation, code duplication
- ❌ **Global middleware**: Opaque, hard to test per-route
- ✅ **Guard decorator**: Reusable, clear intent, testable

**Rationale**:
- Centralized token logic (single source of truth)
- Human-readable code (`@require_tokens("surprise_me")`)
- Flexible configuration per action
- Easy to debug (standard exception handling)

### 2. Dependency Injection: FastAPI Depends()

**Selected Approach**: Decorator reads `keepa: KeepaService` from function kwargs

**Alternatives Considered**:
- ❌ **Singleton global**: Harder to test, less idiomatic FastAPI
- ✅ **FastAPI Depends()**: Respects existing architecture, clean mocking

**Rationale**:
- Aligns with existing codebase patterns
- Superior testability (override dependencies in tests)
- Explicit dependencies in route signatures

### 3. Token Cost Naming: Business Actions

**Selected Approach**: Separate `TOKEN_COSTS` with business-level actions

**Alternatives Considered**:
- ❌ **Reuse ENDPOINT_COSTS**: Coupling to Keepa API internals
- ✅ **Business action names**: Decouples business logic from API

**Rationale**:
- Business actions may compose multiple API calls
- Clearer names for developers (`"surprise_me"` > `"bestsellers"`)
- Easier to evolve if Keepa pricing changes

---

## Architecture Overview

### System Layers

```
┌─────────────────────────────────────────┐
│  1. Token Costs Registry                │
│     (core/token_costs.py)               │
│     - Business action costs             │
│     - Safety thresholds                 │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  2. Guard Decorator                     │
│     (core/guards/require_tokens.py)     │
│     - @require_tokens("action")         │
│     - Pre-execution validation          │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  3. Service Layer                       │
│     (services/keepa_service.py)         │
│     - can_perform_action(action)        │
│     - Balance checking                  │
└─────────────────────────────────────────┘
```

### Execution Flow

```
HTTP Request
    ↓
@require_tokens("surprise_me")
    ↓
Read TOKEN_COSTS["surprise_me"] → cost=50
    ↓
keepa.can_perform_action("surprise_me")
    ↓
Check balance >= 50?
    ├─ YES → Execute endpoint
    └─ NO  → raise InsufficientTokensError (HTTP 429)
```

---

## Component Specifications

### 1. Token Costs Registry

**File**: `backend/app/core/token_costs.py`

**Purpose**: Centralized definition of business action costs

**Structure**:
```python
class ActionCost(TypedDict):
    cost: int
    description: str
    endpoint_type: str  # "single" | "batch" | "composite"

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

# Safety thresholds
CRITICAL_THRESHOLD = 20   # Block all actions
WARNING_THRESHOLD = 100   # Warn user but allow
SAFE_THRESHOLD = 200      # Healthy state
```

**Benefits**:
- Self-documenting (descriptions for UI tooltips)
- Typed structure prevents errors
- `endpoint_type` enables UI-specific handling

### 2. Guard Decorator

**File**: `backend/app/core/guards/require_tokens.py`

**Purpose**: Pre-execution token validation for FastAPI endpoints

**Implementation**:
```python
from functools import wraps
from typing import Callable
import logging
from fastapi import Depends

from ..token_costs import TOKEN_COSTS
from ...services.keepa_service import KeepaService, get_keepa_service
from ..exceptions import InsufficientTokensError

logger = logging.getLogger(__name__)

def require_tokens(action: str):
    """
    Decorator to enforce token balance check before endpoint execution.

    Args:
        action: Business action name from TOKEN_COSTS

    Raises:
        InsufficientTokensError: If tokens < required amount

    Usage:
        @require_tokens("surprise_me")
        async def discover_niches(keepa: KeepaService = Depends(...)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract KeepaService from function kwargs
            keepa: KeepaService = kwargs.get("keepa")
            if not keepa:
                raise ValueError(
                    f"@require_tokens decorator requires 'keepa: KeepaService = Depends(...)' "
                    f"parameter in function {func.__name__}"
                )

            # Get action cost and metadata
            action_config = TOKEN_COSTS.get(action)
            if not action_config:
                logger.error(f"Unknown action '{action}' in @require_tokens")
                raise ValueError(f"Action '{action}' not found in TOKEN_COSTS")

            required_tokens = action_config["cost"]

            # Check if we can perform this action
            can_proceed, balance, _ = await keepa.can_perform_action(action)

            if not can_proceed:
                # Log refusal with context
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

            # Proceed with original function
            return await func(*args, **kwargs)

        return wrapper
    return decorator
```

**Features**:
- Automatic `keepa` extraction from FastAPI kwargs
- Validates action exists in TOKEN_COSTS
- Detailed logging for debugging and monitoring
- Preserves original function signature with `@wraps`
- Clear error messages if misconfigured

### 3. Service Layer Enhancement

**File**: `backend/app/services/keepa_service.py`

**New Method**: `can_perform_action(action: str) -> tuple[bool, int, int]`

**Implementation**:
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

    # Get action configuration
    action_config = TOKEN_COSTS.get(action)
    if not action_config:
        raise ValueError(f"Unknown action '{action}' in TOKEN_COSTS")

    required_tokens = action_config["cost"]

    # Check current balance via existing method
    current_balance = await self.check_api_balance()

    # Block if below critical threshold (global safety)
    if current_balance < CRITICAL_THRESHOLD:
        logger.error(
            f"CRITICAL: Keepa balance {current_balance} below threshold {CRITICAL_THRESHOLD}. "
            f"Blocking all actions."
        )
        return (False, current_balance, required_tokens)

    # Check if sufficient for this specific action
    can_proceed = current_balance >= required_tokens

    if not can_proceed:
        logger.warning(
            f"Insufficient tokens for '{action}': {current_balance}/{required_tokens}"
        )

    return (can_proceed, current_balance, required_tokens)
```

**Features**:
- Reuses existing `check_api_balance()` method
- Global critical threshold protection
- Returns structured data for flexible handling
- Can be used by decorator OR explicit checks

---

## Integration Examples

### Standard Endpoint (Decorator)

**File**: `backend/app/api/v1/endpoints/niches.py`

```python
from app.core.guards.require_tokens import require_tokens

@router.get("/discover")
@require_tokens("surprise_me")  # Token guard
async def discover_niches(
    count: int = Query(default=3, ge=1, le=5),
    shuffle: bool = Query(default=True),
    keepa: KeepaService = Depends(get_keepa_service)  # Required by decorator
):
    """
    Discover curated niches with automatic token protection.

    Decorator ensures we have 50 tokens before execution.
    Returns HTTP 429 if insufficient tokens.
    """
    # Safe to proceed - decorator validated tokens
    niches = await discover_niches_logic(count, shuffle, keepa)
    return niches
```

### Batch Job (Explicit Check)

**File**: `backend/app/services/autosourcing_service.py`

```python
async def run_autosourcing_job(job_id: str):
    """
    AutoSourcing job with graceful degradation.

    Uses explicit check instead of decorator to handle
    skipping gracefully without raising exception.
    """
    keepa = get_keepa_service()

    # Explicit token check
    can_proceed, balance, needed = await keepa.can_perform_action("auto_sourcing_job")

    if not can_proceed:
        logger.warning(
            f"AutoSourcing job {job_id} SKIPPED: insufficient tokens "
            f"({balance}/{needed}). Will retry after token refresh."
        )

        # Update job status to indicate skip reason
        await update_job_status(
            job_id,
            status="SKIPPED_NO_TOKENS",
            message=f"Insufficient tokens: {balance}/{needed} available"
        )
        return

    # Proceed with job execution
    logger.info(f"AutoSourcing job {job_id} starting with {balance} tokens available")
    await execute_autosourcing_logic(job_id, keepa)
```

### Manual Analysis Endpoint

**File**: `backend/app/api/v1/endpoints/products.py`

```python
@router.post("/discover-with-scoring")
@require_tokens("manual_search")  # 10 tokens required
async def discover_with_scoring(
    filters: ProductFilters,
    keepa: KeepaService = Depends(get_keepa_service)
):
    """
    Manual product discovery with scoring.

    Protected by token guard - requires 10 tokens.
    """
    products = await keepa.search_products(filters)
    scored = await score_products(products)
    return scored
```

---

## Error Handling

### HTTP 429 Response Format

When tokens are insufficient, endpoints return:

```json
{
  "detail": {
    "message": "Insufficient Keepa tokens: 15 available, 50 required",
    "current_balance": 15,
    "required_tokens": 50,
    "endpoint": "surprise_me",
    "deficit": 35,
    "solution": "Wait for daily token refresh or upgrade Keepa plan"
  }
}
```

### Frontend Handling

**Recommended approach**:
```typescript
try {
  const niches = await api.discoverNiches();
} catch (error) {
  if (error.status === 429) {
    // Show user-friendly message
    toast.error(
      `Insufficient tokens: ${error.detail.current_balance}/${error.detail.required_tokens} available. ` +
      `Daily refresh at midnight UTC.`
    );

    // Optionally disable button
    setButtonDisabled(true);
  }
}
```

---

## Testing Strategy

### Unit Tests

**Test File**: `backend/tests/test_token_control.py`

```python
async def test_require_tokens_decorator_success():
    """Decorator allows execution when tokens sufficient"""
    # Mock keepa with sufficient balance
    mock_keepa = Mock()
    mock_keepa.can_perform_action.return_value = (True, 100, 50)

    @require_tokens("surprise_me")
    async def test_endpoint(keepa: KeepaService):
        return {"status": "ok"}

    result = await test_endpoint(keepa=mock_keepa)
    assert result == {"status": "ok"}

async def test_require_tokens_decorator_blocks():
    """Decorator raises InsufficientTokensError when tokens low"""
    # Mock keepa with insufficient balance
    mock_keepa = Mock()
    mock_keepa.can_perform_action.return_value = (False, 10, 50)

    @require_tokens("surprise_me")
    async def test_endpoint(keepa: KeepaService):
        return {"status": "ok"}

    with pytest.raises(InsufficientTokensError) as exc_info:
        await test_endpoint(keepa=mock_keepa)

    assert exc_info.value.details["current_balance"] == 10
    assert exc_info.value.details["required_tokens"] == 50

async def test_can_perform_action():
    """Service method returns correct tuple"""
    keepa = KeepaService(api_key="test")
    keepa.check_api_balance = AsyncMock(return_value=100)

    can_proceed, balance, needed = await keepa.can_perform_action("product_lookup")

    assert can_proceed is True
    assert balance == 100
    assert needed == 1
```

### Integration Tests

**Test Scenario**: Real endpoint with mocked Keepa service

```python
async def test_discover_niches_endpoint_blocks_on_low_tokens(client: TestClient):
    """Integration test: endpoint returns 429 when tokens insufficient"""
    # Override KeepaService dependency
    mock_keepa = Mock()
    mock_keepa.can_perform_action.return_value = (False, 10, 50)

    app.dependency_overrides[get_keepa_service] = lambda: mock_keepa

    response = client.get("/api/v1/niches/discover")

    assert response.status_code == 429
    assert response.json()["detail"]["current_balance"] == 10
    assert response.json()["detail"]["required_tokens"] == 50
```

---

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Create `backend/app/core/token_costs.py` with TOKEN_COSTS
- [ ] Create `backend/app/core/guards/` directory
- [ ] Create `backend/app/core/guards/__init__.py`
- [ ] Create `backend/app/core/guards/require_tokens.py` with decorator
- [ ] Add `can_perform_action()` to `keepa_service.py`
- [ ] Write unit tests for decorator and service method

### Phase 2: Endpoint Integration
- [ ] Update `/api/v1/niches/discover` with `@require_tokens("surprise_me")`
- [ ] Update `/api/v1/products/discover-with-scoring` with `@require_tokens("manual_search")`
- [ ] Update `/api/v1/keepa/ingest` with `@require_tokens("product_lookup")`
- [ ] Update AutoSourcing service with explicit check

### Phase 3: Monitoring & Logging
- [ ] Add Sentry alerts for InsufficientTokensError
- [ ] Create dashboard widget showing token balance
- [ ] Add daily token usage metrics

### Phase 4: Frontend Enhancement (Optional)
- [ ] Display Keepa balance in header
- [ ] Disable buttons when tokens < action cost
- [ ] Show user-friendly messages on HTTP 429
- [ ] Add tooltip with token cost per action

---

## Monitoring & Observability

### Key Metrics to Track

1. **Token Refusals**: Count of HTTP 429 responses per action
2. **Token Balance**: Current Keepa balance (hourly snapshot)
3. **Usage by Action**: Tokens consumed per business action
4. **Refusal Patterns**: Time-of-day distribution of refusals

### Logging Strategy

**Token Guard Logs**:
```
[Token Guard] Action 'surprise_me' blocked: 15/50 tokens available. Description: Generate random niche via bestsellers
```

**Service Layer Logs**:
```
Insufficient tokens for 'niche_discovery': 40/150
CRITICAL: Keepa balance 8 below threshold 20. Blocking all actions.
```

**Sentry Integration**:
```python
import sentry_sdk

if not can_proceed:
    sentry_sdk.capture_message(
        f"Token exhaustion: {action} blocked ({balance}/{required})",
        level="warning",
        extra={
            "action": action,
            "balance": balance,
            "required": required
        }
    )
```

---

## Future Enhancements

### Short Term
1. **Predictive Warnings**: Alert user when balance approaches critical threshold
2. **Token Budget Forecasting**: Estimate daily consumption patterns
3. **Action Prioritization**: Queue low-priority actions when tokens scarce

### Medium Term
1. **Multi-Tier Pricing**: Support different Keepa plan limits
2. **Token Pool Sharing**: Share tokens across team members
3. **Cost Optimization**: Batch similar requests to reduce token usage

### Long Term
1. **ML-Based Forecasting**: Predict optimal times for batch operations
2. **Dynamic Pricing Adaptation**: Auto-adjust if Keepa changes costs
3. **Alternative Data Sources**: Fallback to other APIs when tokens exhausted

---

## Risk Assessment

### Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Decorator not called | Low | High | Unit tests, code review |
| TOKEN_COSTS outdated | Medium | Medium | Periodic Keepa API audit |
| False positives (block when sufficient) | Low | High | Comprehensive integration tests |
| Race conditions (concurrent requests) | Low | Low | KeepaThrottle already handles with locks |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Users hit limits frequently | High | Medium | Dashboard with usage tips |
| AutoSourcing always skipped | Medium | High | Run during off-peak hours |
| Critical features blocked | Low | High | Priority queue for essential actions |

---

## Rollback Plan

If issues arise post-deployment:

1. **Immediate**: Remove `@require_tokens` decorators (revert commits)
2. **Short-term**: Revert to previous throttle-only protection
3. **Analysis**: Review logs to identify failure patterns
4. **Fix**: Address issues in staging environment
5. **Re-deploy**: With additional safeguards

**Rollback Command**:
```bash
git revert <token-control-commit-hash>
git push origin main
# Trigger Render redeploy
```

---

## Success Criteria

### Functional
- [ ] No token exhaustion incidents (balance stays > 0)
- [ ] All endpoints protected by decorator or explicit check
- [ ] HTTP 429 responses contain actionable error messages
- [ ] AutoSourcing gracefully skips when tokens low

### Performance
- [ ] Decorator adds < 50ms latency per request
- [ ] No impact on non-Keepa endpoints
- [ ] Token balance check cached appropriately

### User Experience
- [ ] Users understand why actions are blocked
- [ ] Dashboard shows clear token status
- [ ] No silent failures (all refusals logged)

---

## Approval & Sign-Off

**Design Approved By**: Aziz
**Date**: 2025-11-03
**Implementation Start**: 2025-11-03
**Target Completion**: 2025-11-04

**Next Steps**:
1. Create git worktree for isolated implementation
2. Implement core components (token_costs, decorator, service method)
3. Write comprehensive tests
4. Integrate into critical endpoints
5. Deploy to production with monitoring

---

**Document Version**: 1.0
**Last Updated**: 2025-11-03
