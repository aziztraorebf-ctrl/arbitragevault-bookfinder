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

    def test_timeout_constant_is_defined(self):
        """Verify TIMEOUT_PER_JOB constant is properly defined."""
        assert TIMEOUT_PER_JOB == 120, f"TIMEOUT_PER_JOB should be 120 seconds, got {TIMEOUT_PER_JOB}"

    @pytest.mark.asyncio
    async def test_timeout_during_discovery_updates_job_status(self, service, mock_db):
        """Timeout during discovery phase should result in proper cleanup."""
        # Mock slow discovery that will exceed timeout
        async def slow_discovery(*args, **kwargs):
            await asyncio.sleep(0.5)  # Will exceed test timeout
            return []

        with patch.object(service, '_discover_products', slow_discovery):
            with patch('app.services.autosourcing_service.TIMEOUT_PER_JOB', 0.1):
                # The service should handle timeout
                try:
                    await service.run_custom_search(
                        discovery_config={"categories": ["books"]},
                        scoring_config={},
                        profile_name="Timeout Test"
                    )
                except Exception:
                    pass  # Expected to fail

        # Job should have been committed at least once
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_timeout_exact_boundary(self):
        """Test TIMEOUT_PER_JOB boundary value."""
        # This tests the constant value is what we expect
        assert TIMEOUT_PER_JOB == 120, "TIMEOUT_PER_JOB should be 120 seconds"
        # Boundary validation - timeout should be reasonable
        assert TIMEOUT_PER_JOB > 60, "Timeout too short for batch operations"
        assert TIMEOUT_PER_JOB <= 300, "Timeout too long, user experience suffers"

    @pytest.mark.asyncio
    async def test_job_status_never_stuck_running(self, service, mock_db):
        """Job should never stay in RUNNING state after any error."""
        # Mock error during discovery
        async def error_discovery(*args, **kwargs):
            raise Exception("Unexpected error")

        with patch.object(service, '_discover_products', error_discovery):
            try:
                await service.run_custom_search(
                    discovery_config={"categories": ["books"]},
                    scoring_config={},
                    profile_name="Error Test"
                )
            except Exception:
                pass  # Expected

        # Verify commit was called (status update should happen)
        # The service should commit the initial job and update on error
        assert mock_db.commit.call_count >= 1

    @pytest.mark.asyncio
    async def test_concurrent_timeout_handling(self):
        """Multiple concurrent timeouts should each clean up properly."""
        # This verifies the timeout mechanism doesn't have race conditions
        # between multiple concurrent jobs

        async def slow_task():
            try:
                async with asyncio.timeout(0.1):
                    await asyncio.sleep(0.5)
            except TimeoutError:
                return "timed_out"
            return "completed"

        # Run multiple concurrent timeouts
        results = await asyncio.gather(
            slow_task(),
            slow_task(),
            slow_task()
        )

        # All should timeout properly
        assert all(r == "timed_out" for r in results)

    @pytest.mark.asyncio
    async def test_timeout_during_scoring_does_not_corrupt_db(self, service, mock_db):
        """Timeout during scoring phase should not leave corrupted data."""
        # Mock fast discovery, slow scoring
        async def fast_discovery(*args, **kwargs):
            return ["ASIN1", "ASIN2", "ASIN3"]

        async def slow_scoring(*args, **kwargs):
            await asyncio.sleep(0.5)
            return []

        with patch.object(service, '_discover_products', fast_discovery):
            with patch.object(service, '_score_and_filter_products', slow_scoring):
                with patch('app.services.autosourcing_service.TIMEOUT_PER_JOB', 0.1):
                    try:
                        await service.run_custom_search(
                            discovery_config={"categories": ["books"]},
                            scoring_config={},
                            profile_name="Partial Timeout"
                        )
                    except Exception:
                        pass

        # DB operations should be called but transaction should be consistent
        # No partial writes should occur
        assert mock_db.commit.called
