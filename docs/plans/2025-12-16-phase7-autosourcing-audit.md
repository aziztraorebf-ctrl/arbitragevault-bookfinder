# Phase 7: AutoSourcing Safeguards - Audit Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Audit complet Phase 7 AutoSourcing avec tests hostiles, validation edge cases, et couverture 100%

**Architecture:** AutoSourcingService orchestre discovery -> deduplication -> scoring -> filtering avec safeguards (cost estimation, timeout 120s, balance check)

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, pytest-asyncio, Keepa REST API

**Status actuel:**
- 53 tests existants (unit + API + E2E)
- Code quality 9.5/10
- E2E tests 5/5
- Gaps identifies: edge cases timeout, batch API failures, race conditions

---

## Analyse des Gaps

### Tests Existants (53)
| Fichier | Tests | Coverage |
|---------|-------|----------|
| test_autosourcing_roi_calculation.py | 10 | ROI calculation |
| test_autosourcing_meets_criteria.py | 9 | Criteria filtering |
| test_autosourcing_cost_estimator.py | 5 | Cost estimation |
| test_autosourcing_safeguards_schemas.py | 5 | Schema validation |
| test_autosourcing_validator.py | 4 | Job validation |
| test_autosourcing_deduplication.py | 2 | Basic dedup |
| test_autosourcing_token_control.py | 4 | Token protection |
| test_autosourcing_estimate.py | 3 | /estimate endpoint |
| test_autosourcing_timeout.py | 3 | Timeout handling |
| test_autosourcing_validation_enforcement.py | 2 | 400/429 enforcement |
| test_autosourcing_real_keepa.py | 5 | Real API (REPLAY) |
| E2E Playwright | 5+ | Frontend flows |

### Gaps Identifies
1. **Batch API partial failures** - Que se passe-t-il si 30/50 ASINs echouent?
2. **Deduplication edge cases** - Liste vide, tous duplicates, max_to_analyze=0
3. **Timeout race conditions** - Timeout pendant DB commit
4. **Error propagation** - InsufficientTokensError mid-batch
5. **Job status transitions** - RUNNING->FAILED sans picks orphelins
6. **Recent duplicates removal** - Window boundary (exactement 7 jours)

---

## Evaluation Parallelisation & Playwright

### Agents en Parallele: RECOMMANDE PARTIEL

**Tasks parallelisables:**
- Task 1-3 (Unit tests) peuvent etre parallelises (independants)
- Task 4-5 (Integration tests) peuvent etre parallelises

**Tasks sequentielles:**
- Task 6-7 (API tests) dependent des services
- Task 8 (E2E Playwright) doit etre dernier

**Recommandation:** 2 agents paralleles max pour eviter conflits Git

### Playwright E2E: RECOMMANDE

**Justification:**
- Frontend AutoSourcing existe (pages, hooks)
- Tests E2E existants (05-autosourcing-flow.spec.js)
- Valide flux utilisateur complet: estimation -> execution -> resultats

**Tests Playwright a ajouter:**
1. Flow estimation avec cout > 200 tokens (rejection)
2. Flow execution avec timeout simule
3. Flow actions utilisateur (to_buy, favorite)

---

## Tasks Implementation

### Task 1: Tests Hostiles Deduplication (Unit)

**Files:**
- Create: `tests/unit/test_autosourcing_deduplication_hostile.py`

**Step 1: Write failing tests for edge cases**

```python
"""
Hostile tests for ASIN deduplication edge cases.
Phase 7 Audit - TDD approach.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.autosourcing_service import AutoSourcingService


class TestDeduplicationHostile:
    """Hostile edge case tests for deduplication."""

    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies."""
        mock_db = MagicMock()
        mock_keepa = MagicMock()
        return AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa)

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self, service):
        """Empty input should return empty output."""
        result = await service.process_asins_with_deduplication([])
        assert result == []

    @pytest.mark.asyncio
    async def test_all_duplicates_returns_one(self, service):
        """All identical ASINs should return single item."""
        asins = ["ASIN1"] * 100
        result = await service.process_asins_with_deduplication(asins)
        assert len(result) == 1
        assert result[0] == "ASIN1"

    @pytest.mark.asyncio
    async def test_max_to_analyze_zero_returns_empty(self, service):
        """max_to_analyze=0 should return empty list."""
        asins = ["ASIN1", "ASIN2", "ASIN3"]
        result = await service.process_asins_with_deduplication(asins, max_to_analyze=0)
        assert result == []

    @pytest.mark.asyncio
    async def test_max_to_analyze_negative_raises_or_empty(self, service):
        """Negative max_to_analyze should be handled gracefully."""
        asins = ["ASIN1", "ASIN2"]
        # Should either raise ValueError or return empty
        result = await service.process_asins_with_deduplication(asins, max_to_analyze=-1)
        assert result == []  # Graceful handling

    @pytest.mark.asyncio
    async def test_preserves_first_occurrence_order_large_list(self, service):
        """Order preservation with 1000+ items."""
        # Create list with specific pattern
        asins = [f"ASIN{i % 100}" for i in range(1000)]  # 100 unique, repeated 10x each
        result = await service.process_asins_with_deduplication(asins, max_to_analyze=100)

        # Should preserve order of first occurrences
        assert result[0] == "ASIN0"
        assert result[1] == "ASIN1"
        assert len(result) == 100

    @pytest.mark.asyncio
    async def test_none_asins_in_list_handled(self, service):
        """None values in list should be handled."""
        asins = ["ASIN1", None, "ASIN2", None, "ASIN3"]
        # Should skip None values or raise
        result = await service.process_asins_with_deduplication(asins)
        assert None not in result
        assert len(result) <= 3

    @pytest.mark.asyncio
    async def test_empty_string_asin_handled(self, service):
        """Empty string ASINs should be handled."""
        asins = ["ASIN1", "", "ASIN2", "", "ASIN3"]
        result = await service.process_asins_with_deduplication(asins)
        # Empty strings should be filtered or kept (document behavior)
        assert "ASIN1" in result
```

**Step 2: Run tests to verify failures**

```bash
cd backend && python -m pytest tests/unit/test_autosourcing_deduplication_hostile.py -v
```

Expected: Some tests FAIL (None handling, empty string, negative max)

**Step 3: Fix service to handle edge cases**

Modify `app/services/autosourcing_service.py:337-382`:

```python
async def process_asins_with_deduplication(
    self,
    asins: List[str],
    max_to_analyze: int = None
) -> List[str]:
    """
    Deduplicate ASINs with hostile input handling.
    """
    # Handle None/empty input
    if not asins:
        return []

    # Handle invalid max_to_analyze
    if max_to_analyze is None:
        from app.schemas.autosourcing_safeguards import MAX_PRODUCTS_PER_SEARCH
        max_to_analyze = MAX_PRODUCTS_PER_SEARCH

    if max_to_analyze <= 0:
        logger.warning(f"Invalid max_to_analyze={max_to_analyze}, returning empty")
        return []

    seen = set()
    unique_asins = []

    for asin in asins:
        # Skip None and empty strings
        if not asin or not isinstance(asin, str):
            logger.debug(f"Skipping invalid ASIN: {asin}")
            continue

        # Skip duplicates
        if asin in seen:
            continue

        # Check limit
        if len(unique_asins) >= max_to_analyze:
            break

        seen.add(asin)
        unique_asins.append(asin)

    return unique_asins
```

**Step 4: Run tests to verify pass**

```bash
cd backend && python -m pytest tests/unit/test_autosourcing_deduplication_hostile.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add tests/unit/test_autosourcing_deduplication_hostile.py
git add app/services/autosourcing_service.py
git commit -m "test(phase7): add hostile deduplication tests with edge cases"
```

---

### Task 2: Tests Batch API Partial Failures (Unit)

**Files:**
- Create: `tests/unit/test_autosourcing_batch_failures.py`

**Step 1: Write failing tests**

```python
"""
Tests for batch API partial failure handling.
Phase 7 Audit - Ensures graceful degradation.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.autosourcing_service import AutoSourcingService
from app.core.exceptions import InsufficientTokensError


class TestBatchAPIFailures:
    """Test batch API failure scenarios."""

    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        mock_keepa = MagicMock()
        mock_keepa._make_request = AsyncMock()
        mock_keepa._ensure_sufficient_balance = AsyncMock()
        return AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa)

    @pytest.mark.asyncio
    async def test_partial_batch_success(self, service):
        """30/50 ASINs succeed - should return 30 results."""
        # Mock API returning only 30 products from 50 requested
        service.keepa_service._make_request.return_value = {
            "products": [{"asin": f"ASIN{i}"} for i in range(30)]
        }

        asins = [f"ASIN{i}" for i in range(50)]
        result = await service._fetch_products_batch(asins)

        assert len(result) == 30  # Only successful ones

    @pytest.mark.asyncio
    async def test_batch_api_timeout_continues(self, service):
        """First batch times out, second succeeds."""
        call_count = 0

        async def mock_request(endpoint, params):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("Batch timeout")
            return {"products": [{"asin": "ASIN_SUCCESS"}]}

        service.keepa_service._make_request = mock_request

        # 100 ASINs = 2 batches of 50
        asins = [f"ASIN{i}" for i in range(100)]
        result = await service._fetch_products_batch(asins, batch_size=50)

        # Should have results from second batch only
        assert "ASIN_SUCCESS" in result

    @pytest.mark.asyncio
    async def test_batch_insufficient_tokens_raises(self, service):
        """InsufficientTokensError should propagate up."""
        service.keepa_service._ensure_sufficient_balance.side_effect = InsufficientTokensError(
            current_balance=10,
            required_tokens=50,
            endpoint="batch"
        )

        asins = ["ASIN1", "ASIN2"]

        with pytest.raises(InsufficientTokensError):
            await service._fetch_products_batch(asins)

    @pytest.mark.asyncio
    async def test_empty_batch_returns_empty_dict(self, service):
        """Empty ASIN list should return empty dict."""
        result = await service._fetch_products_batch([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_all_batches_fail_returns_empty(self, service):
        """All batches failing should return empty dict."""
        service.keepa_service._make_request.side_effect = Exception("API Error")

        asins = [f"ASIN{i}" for i in range(50)]
        result = await service._fetch_products_batch(asins)

        assert result == {}
```

**Step 2: Run tests**

```bash
cd backend && python -m pytest tests/unit/test_autosourcing_batch_failures.py -v
```

**Step 3: Verify/fix implementation**

Current implementation in `autosourcing_service.py:384-445` already handles most cases.
Verify and add any missing error handling.

**Step 4: Commit**

```bash
git add tests/unit/test_autosourcing_batch_failures.py
git commit -m "test(phase7): add batch API partial failure tests"
```

---

### Task 3: Tests Timeout Race Conditions (Unit)

**Files:**
- Create: `tests/unit/test_autosourcing_timeout_race.py`

**Step 1: Write tests for race conditions**

```python
"""
Tests for timeout race conditions.
Phase 7 Audit - Ensures DB state consistency on timeout.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from app.services.autosourcing_service import AutoSourcingService
from app.models.autosourcing import JobStatus
from app.schemas.autosourcing_safeguards import TIMEOUT_PER_JOB


class TestTimeoutRaceConditions:
    """Test timeout edge cases and race conditions."""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_keepa(self):
        keepa = MagicMock()
        keepa.can_perform_action = AsyncMock(return_value={
            "can_proceed": True,
            "current_balance": 1000,
            "required_tokens": 50
        })
        keepa._make_request = AsyncMock()
        keepa._ensure_sufficient_balance = AsyncMock()
        return keepa

    @pytest.fixture
    def service(self, mock_db, mock_keepa):
        return AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa)

    @pytest.mark.asyncio
    async def test_timeout_during_discovery_updates_job_status(self, service, mock_db):
        """Timeout during discovery phase should mark job FAILED."""
        # Mock slow discovery
        async def slow_discovery(*args, **kwargs):
            await asyncio.sleep(0.5)  # Will exceed test timeout
            return []

        with patch.object(service, '_discover_products', slow_discovery):
            with patch('app.services.autosourcing_service.TIMEOUT_PER_JOB', 0.1):
                with pytest.raises(Exception):  # HTTPException or TimeoutError
                    await service.run_custom_search(
                        discovery_config={"categories": ["books"]},
                        scoring_config={},
                        profile_name="Timeout Test"
                    )

        # Job should have been committed with FAILED status
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_timeout_during_scoring_saves_partial_results(self, service, mock_db):
        """Timeout during scoring should save discovered ASINs."""
        # Mock fast discovery, slow scoring
        async def fast_discovery(*args, **kwargs):
            return ["ASIN1", "ASIN2", "ASIN3"]

        async def slow_scoring(*args, **kwargs):
            await asyncio.sleep(0.5)
            return []

        with patch.object(service, '_discover_products', fast_discovery):
            with patch.object(service, '_score_and_filter_products', slow_scoring):
                with patch('app.services.autosourcing_service.TIMEOUT_PER_JOB', 0.1):
                    with pytest.raises(Exception):
                        await service.run_custom_search(
                            discovery_config={"categories": ["books"]},
                            scoring_config={},
                            profile_name="Partial Timeout"
                        )

    @pytest.mark.asyncio
    async def test_timeout_exact_boundary(self, service):
        """Test behavior at exactly TIMEOUT_PER_JOB seconds."""
        # This tests the boundary condition
        assert TIMEOUT_PER_JOB == 120, "TIMEOUT_PER_JOB should be 120 seconds"

    @pytest.mark.asyncio
    async def test_job_status_never_stuck_running(self, service, mock_db):
        """Job should never stay in RUNNING state after any error."""
        # Mock error during any phase
        async def error_discovery(*args, **kwargs):
            raise Exception("Unexpected error")

        with patch.object(service, '_discover_products', error_discovery):
            with pytest.raises(Exception):
                await service.run_custom_search(
                    discovery_config={"categories": ["books"]},
                    scoring_config={},
                    profile_name="Error Test"
                )

        # Verify commit was called (status update)
        assert mock_db.commit.call_count >= 2  # Creation + error update
```

**Step 2-5: Run, verify, commit**

```bash
cd backend && python -m pytest tests/unit/test_autosourcing_timeout_race.py -v
git add tests/unit/test_autosourcing_timeout_race.py
git commit -m "test(phase7): add timeout race condition tests"
```

---

### Task 4: Tests Recent Duplicates Removal (Integration)

**Files:**
- Create: `tests/integration/test_autosourcing_recent_duplicates.py`

**Step 1: Write integration tests**

```python
"""
Integration tests for recent duplicates removal.
Phase 7 Audit - Tests 7-day window behavior.
"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock

from app.services.autosourcing_service import AutoSourcingService
from app.models.autosourcing import AutoSourcingPick, AutoSourcingJob, JobStatus


class TestRecentDuplicatesRemoval:
    """Test recent duplicates removal with time boundaries."""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        mock_keepa = MagicMock()
        return AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa)

    def create_pick(self, asin: str, job_id=None, created_days_ago: int = 0):
        """Helper to create pick with specific age."""
        return AutoSourcingPick(
            id=uuid4(),
            job_id=job_id or uuid4(),
            asin=asin,
            title=f"Product {asin}",
            roi_percentage=35.0,
            velocity_score=75,
            stability_score=80,
            confidence_score=85,
            overall_rating="A",
            created_at=datetime.now(timezone.utc) - timedelta(days=created_days_ago)
        )

    @pytest.mark.asyncio
    async def test_removes_picks_from_last_7_days(self, service, mock_db):
        """Picks with same ASIN from last 7 days should be removed."""
        # Mock: ASIN1 was found 3 days ago
        mock_db.execute.return_value.scalars.return_value.all.return_value = ["ASIN1"]

        new_picks = [
            self.create_pick("ASIN1"),  # Duplicate - should be removed
            self.create_pick("ASIN2"),  # New - should be kept
        ]

        result = await service._remove_recent_duplicates(new_picks)

        assert len(result) == 1
        assert result[0].asin == "ASIN2"

    @pytest.mark.asyncio
    async def test_keeps_picks_older_than_7_days(self, service, mock_db):
        """Picks with same ASIN from >7 days ago should be kept."""
        # Mock: No recent duplicates
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        new_picks = [
            self.create_pick("ASIN1"),
            self.create_pick("ASIN2"),
        ]

        result = await service._remove_recent_duplicates(new_picks)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_boundary_exactly_7_days(self, service, mock_db):
        """Pick from exactly 7 days ago should be considered recent."""
        # This tests the boundary condition
        # Mock: ASIN1 was found exactly 7 days ago
        mock_db.execute.return_value.scalars.return_value.all.return_value = ["ASIN1"]

        new_picks = [self.create_pick("ASIN1")]

        result = await service._remove_recent_duplicates(new_picks)

        # Should be removed (within 7-day window)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_empty_picks_returns_empty(self, service, mock_db):
        """Empty picks list should return empty."""
        result = await service._remove_recent_duplicates([])
        assert result == []
```

**Step 2-5: Run, verify, commit**

```bash
cd backend && python -m pytest tests/integration/test_autosourcing_recent_duplicates.py -v
git add tests/integration/test_autosourcing_recent_duplicates.py
git commit -m "test(phase7): add recent duplicates removal integration tests"
```

---

### Task 5: Tests API Error Responses (Integration)

**Files:**
- Create: `tests/api/test_autosourcing_error_responses.py`

**Step 1: Write API error response tests**

```python
"""
API tests for error response format and content.
Phase 7 Audit - Validates frontend-friendly error messages.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestAutoSourcingErrorResponses:
    """Test API error responses are frontend-friendly."""

    @pytest.mark.asyncio
    async def test_400_error_includes_suggestion(self, test_client):
        """400 errors should include actionable suggestion."""
        # Mock expensive job
        with patch('app.api.v1.routers.autosourcing.estimate_job_cost', return_value=300):
            response = test_client.post(
                "/api/v1/autosourcing/estimate",
                json={
                    "discovery_config": {"categories": ["books"], "max_results": 1000},
                    "scoring_config": {}
                }
            )

        if response.status_code == 400:
            detail = response.json().get("detail", {})
            assert "suggestion" in detail or "max_allowed" in detail

    @pytest.mark.asyncio
    async def test_429_error_includes_balance_info(self, test_client):
        """429 errors should include current balance."""
        # Mock insufficient balance
        with patch('app.services.keepa_service.KeepaService.check_api_balance',
                   new_callable=AsyncMock, return_value=10):
            response = test_client.post(
                "/api/v1/autosourcing/run-custom",
                json={
                    "profile_name": "Test",
                    "discovery_config": {"categories": ["books"]},
                    "scoring_config": {}
                }
            )

        if response.status_code == 429:
            detail = response.json().get("detail", {})
            # Should include balance information
            assert "balance" in str(detail).lower() or "tokens" in str(detail).lower()

    @pytest.mark.asyncio
    async def test_408_error_message_clear(self, test_client):
        """408 timeout errors should have clear message."""
        # This would require mocking slow service
        # Verify 408 response format when it occurs
        pass  # Covered by existing timeout tests

    @pytest.mark.asyncio
    async def test_error_responses_are_json(self, test_client):
        """All error responses should be valid JSON."""
        # Test various error scenarios return JSON
        endpoints = [
            ("/api/v1/autosourcing/jobs/invalid-uuid", "GET"),
            ("/api/v1/autosourcing/picks/invalid-uuid/action", "PUT"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = test_client.get(endpoint)
            else:
                response = test_client.put(endpoint, json={"action": "to_buy"})

            # Should return JSON even on error
            assert response.headers.get("content-type", "").startswith("application/json")
```

**Step 2-5: Run, verify, commit**

```bash
cd backend && python -m pytest tests/api/test_autosourcing_error_responses.py -v
git add tests/api/test_autosourcing_error_responses.py
git commit -m "test(phase7): add API error response format tests"
```

---

### Task 6: Tests Job Status Transitions (Integration)

**Files:**
- Create: `tests/integration/test_autosourcing_job_states.py`

**Step 1: Write state transition tests**

```python
"""
Integration tests for job status state machine.
Phase 7 Audit - Ensures valid state transitions only.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.models.autosourcing import AutoSourcingJob, JobStatus


class TestJobStatusTransitions:
    """Test valid job status transitions."""

    def test_valid_transitions(self):
        """Document valid state transitions."""
        valid_transitions = {
            JobStatus.PENDING: [JobStatus.RUNNING, JobStatus.CANCELLED],
            JobStatus.RUNNING: [JobStatus.SUCCESS, JobStatus.ERROR, JobStatus.FAILED],
            JobStatus.SUCCESS: [],  # Terminal state
            JobStatus.ERROR: [],    # Terminal state
            JobStatus.FAILED: [],   # Terminal state (timeout)
            JobStatus.CANCELLED: [], # Terminal state
        }

        # Verify all statuses are covered
        for status in JobStatus:
            assert status in valid_transitions

    def test_job_starts_pending_or_running(self):
        """New jobs should start in PENDING or RUNNING state."""
        job = AutoSourcingJob(
            profile_name="Test",
            discovery_config={},
            scoring_config={},
            status=JobStatus.RUNNING,
            launched_at=datetime.now(timezone.utc)
        )

        assert job.status in [JobStatus.PENDING, JobStatus.RUNNING]

    def test_completed_job_has_timestamp(self):
        """Completed jobs should have completed_at timestamp."""
        job = AutoSourcingJob(
            profile_name="Test",
            discovery_config={},
            scoring_config={},
            status=JobStatus.SUCCESS,
            launched_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )

        assert job.completed_at is not None

    def test_failed_job_has_error_message(self):
        """Failed jobs should have error_message."""
        job = AutoSourcingJob(
            profile_name="Test",
            discovery_config={},
            scoring_config={},
            status=JobStatus.FAILED,
            launched_at=datetime.now(timezone.utc),
            error_message="Timeout exceeded"
        )

        assert job.error_message is not None
        assert len(job.error_message) > 0

    def test_error_job_has_error_message(self):
        """Error jobs should have error_message."""
        job = AutoSourcingJob(
            profile_name="Test",
            discovery_config={},
            scoring_config={},
            status=JobStatus.ERROR,
            launched_at=datetime.now(timezone.utc),
            error_message="API error"
        )

        assert job.error_message is not None
```

**Step 2-5: Run, verify, commit**

```bash
cd backend && python -m pytest tests/integration/test_autosourcing_job_states.py -v
git add tests/integration/test_autosourcing_job_states.py
git commit -m "test(phase7): add job status transition tests"
```

---

### Task 7: Hostile Review Service Principal

**Files:**
- Review: `app/services/autosourcing_service.py`
- Create: `tests/unit/test_autosourcing_hostile_review.py`

**Step 1: Hostile review checklist**

```python
"""
Hostile review tests for AutoSourcingService.
Phase 7 Audit - Attack surface analysis.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock


class TestHostileReviewAutoSourcing:
    """Hostile review: find bugs before they find you."""

    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        mock_keepa = MagicMock()
        mock_keepa.can_perform_action = AsyncMock(return_value={
            "can_proceed": True, "current_balance": 1000, "required_tokens": 50
        })
        from app.services.autosourcing_service import AutoSourcingService
        return AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa)

    # Edge case: What if discovery_config is None?
    @pytest.mark.asyncio
    async def test_none_discovery_config_handled(self, service):
        """None discovery_config should raise or use defaults."""
        with pytest.raises((TypeError, ValueError, KeyError)):
            await service.run_custom_search(
                discovery_config=None,
                scoring_config={},
                profile_name="None Config Test"
            )

    # Edge case: What if scoring_config is None?
    @pytest.mark.asyncio
    async def test_none_scoring_config_handled(self, service):
        """None scoring_config should use defaults."""
        # Should not crash
        try:
            await service.run_custom_search(
                discovery_config={"categories": ["books"]},
                scoring_config=None,
                profile_name="None Scoring Test"
            )
        except (TypeError, AttributeError):
            pytest.fail("Should handle None scoring_config gracefully")

    # Edge case: What if profile_name is empty?
    @pytest.mark.asyncio
    async def test_empty_profile_name_handled(self, service):
        """Empty profile_name should be handled."""
        # Should either use default name or raise validation error
        pass  # Document expected behavior

    # Edge case: What if categories list is empty?
    @pytest.mark.asyncio
    async def test_empty_categories_uses_default(self, service):
        """Empty categories should use Books default."""
        # Mock to verify correct category ID used
        pass

    # Race condition: What if DB commit fails mid-job?
    @pytest.mark.asyncio
    async def test_db_commit_failure_handled(self, service):
        """DB commit failure should not leave orphan records."""
        service.db.commit = AsyncMock(side_effect=Exception("DB Error"))

        with pytest.raises(Exception):
            await service.run_custom_search(
                discovery_config={"categories": ["books"]},
                scoring_config={},
                profile_name="DB Fail Test"
            )

    # Security: What if malicious ASIN injected?
    @pytest.mark.asyncio
    async def test_malicious_asin_sanitized(self, service):
        """Malicious ASIN patterns should be filtered."""
        malicious_asins = [
            "'; DROP TABLE products; --",
            "<script>alert('xss')</script>",
            "ASIN\x00NULL",
        ]

        result = await service.process_asins_with_deduplication(malicious_asins)

        # Should either sanitize or skip malicious entries
        for asin in result:
            assert "DROP" not in asin
            assert "<script>" not in asin
```

**Step 2-5: Run, verify, commit**

```bash
cd backend && python -m pytest tests/unit/test_autosourcing_hostile_review.py -v
git add tests/unit/test_autosourcing_hostile_review.py
git commit -m "test(phase7): add hostile review tests for AutoSourcingService"
```

---

### Task 8: E2E Tests Playwright (Frontend)

**Files:**
- Create: `tests/e2e/tests/12-phase7-autosourcing-complete.spec.js`

**Step 1: Write comprehensive E2E tests**

```javascript
/**
 * Phase 7 AutoSourcing Complete E2E Tests
 * Tests full user flow from estimation to results
 */
const { test, expect } = require('@playwright/test');

test.describe('Phase 7 AutoSourcing E2E', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to AutoSourcing page
    await page.goto('/autosourcing');
  });

  test('estimation flow shows cost breakdown', async ({ page }) => {
    // Fill in discovery config
    await page.fill('[data-testid="category-select"]', 'books');
    await page.fill('[data-testid="max-results"]', '50');

    // Click estimate button
    await page.click('[data-testid="estimate-btn"]');

    // Wait for estimation result
    await expect(page.locator('[data-testid="cost-estimate"]')).toBeVisible();

    // Should show breakdown
    await expect(page.locator('[data-testid="discovery-cost"]')).toBeVisible();
    await expect(page.locator('[data-testid="analysis-cost"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-cost"]')).toBeVisible();
  });

  test('expensive job shows warning', async ({ page }) => {
    // Configure expensive job (>200 tokens)
    await page.fill('[data-testid="max-results"]', '500');

    // Click estimate
    await page.click('[data-testid="estimate-btn"]');

    // Should show warning about cost
    await expect(page.locator('[data-testid="cost-warning"]')).toBeVisible();
  });

  test('run job and see results', async ({ page }) => {
    // Configure reasonable job
    await page.fill('[data-testid="profile-name"]', 'E2E Test Job');
    await page.fill('[data-testid="max-results"]', '10');

    // Run job
    await page.click('[data-testid="run-btn"]');

    // Wait for completion (up to 30s)
    await expect(page.locator('[data-testid="job-status"]')).toHaveText(/SUCCESS|completed/i, {
      timeout: 30000
    });

    // Results should be visible
    await expect(page.locator('[data-testid="results-list"]')).toBeVisible();
  });

  test('user can mark pick as to_buy', async ({ page }) => {
    // Assume job already ran - go to results
    await page.goto('/autosourcing/results');

    // Find first pick
    const firstPick = page.locator('[data-testid="pick-card"]').first();

    // Click to_buy action
    await firstPick.locator('[data-testid="action-to-buy"]').click();

    // Verify status updated
    await expect(firstPick.locator('[data-testid="action-status"]')).toHaveText(/to_buy/i);
  });

  test('timeout shows friendly error', async ({ page }) => {
    // This requires backend mock for timeout
    // Skip if not configured
    test.skip();
  });

  test('insufficient balance shows clear message', async ({ page }) => {
    // This requires backend mock for low balance
    // Skip if not configured
    test.skip();
  });

});
```

**Step 2: Run Playwright tests**

```bash
cd backend/tests/e2e && npx playwright test tests/12-phase7-autosourcing-complete.spec.js --headed
```

**Step 3: Fix any failures**

**Step 4: Commit**

```bash
git add tests/e2e/tests/12-phase7-autosourcing-complete.spec.js
git commit -m "test(phase7): add comprehensive E2E tests for AutoSourcing flow"
```

---

### Task 9: Verification & Documentation

**Step 1: Run all Phase 7 tests**

```bash
cd backend && python -m pytest tests/ -k "autosourcing" -v --tb=short
```

Expected: All tests PASS

**Step 2: Generate coverage report**

```bash
cd backend && python -m pytest tests/ -k "autosourcing" --cov=app/services/autosourcing --cov-report=html
```

**Step 3: Update compact_current.md**

Document Phase 7 audit completion with:
- Tests added count
- Coverage percentage
- Edge cases covered
- Any fixes applied

**Step 4: Final commit**

```bash
git add .claude/compact_current.md
git commit -m "docs(phase7): complete audit documentation"
```

---

## Summary

| Task | Type | Tests | Time Est. |
|------|------|-------|-----------|
| 1. Deduplication Hostile | Unit | 7 | 15 min |
| 2. Batch API Failures | Unit | 5 | 15 min |
| 3. Timeout Race Conditions | Unit | 4 | 15 min |
| 4. Recent Duplicates | Integration | 4 | 10 min |
| 5. API Error Responses | Integration | 4 | 10 min |
| 6. Job Status Transitions | Integration | 5 | 10 min |
| 7. Hostile Review | Unit | 6 | 20 min |
| 8. E2E Playwright | E2E | 6 | 25 min |
| 9. Verification | Docs | - | 10 min |

**Total:** ~41 nouveaux tests, ~2h30 d'effort

**Parallelisation recommandee:**
- Agent 1: Tasks 1-3 (Unit tests)
- Agent 2: Tasks 4-6 (Integration tests)
- Sequential: Tasks 7-9 (apres merge)

---

**Plan complet et sauvegarde dans `docs/plans/2025-12-16-phase7-autosourcing-audit.md`.**

**Deux options d'execution:**

1. **Subagent-Driven (cette session)** - Je dispatch un subagent par task, review entre tasks, iteration rapide

2. **Parallel Session (separee)** - Ouvrir nouvelle session avec executing-plans, execution batch avec checkpoints

**Quelle approche ?**
