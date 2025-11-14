"""
Tests for AutoSourcing timeout protection.

NOTE: Full timeout testing (121s delay) would take too long in test suite.
These tests verify timeout infrastructure is in place and working.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.api.v1.routers.autosourcing import run_custom_search, RunCustomSearchRequest
from app.models.autosourcing import AutoSourcingJob, JobStatus
from app.schemas.autosourcing_safeguards import TIMEOUT_PER_JOB
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_run_custom_enforces_timeout():
    """
    Test run_custom endpoint enforces timeout with asyncio.timeout().

    Uses a very short timeout (0.1s) to test timeout enforcement
    without waiting 120+ seconds.
    """
    # Create request
    request = RunCustomSearchRequest(
        profile_name="Test Timeout",
        discovery_config={"categories": ["books"], "max_results": 10},
        scoring_config={"roi_min": 30, "velocity_min": 70}
    )

    # Mock dependencies
    mock_keepa_service = AsyncMock()
    mock_keepa_service.check_api_balance = AsyncMock(return_value=1000)

    mock_autosourcing_service = AsyncMock()
    # Make run_custom_search take longer than timeout
    async def slow_search(*args, **kwargs):
        await asyncio.sleep(0.5)  # Exceeds 0.1s test timeout
        return AutoSourcingJob(
            id=uuid4(),
            profile_name="Slow",
            status=JobStatus.SUCCESS,
            total_tested=0,
            total_selected=0,
            launched_at=datetime.now(timezone.utc),
            picks=[]
        )
    mock_autosourcing_service.run_custom_search = slow_search

    # Test with very short timeout (0.1s instead of 120s)
    with patch('app.api.v1.routers.autosourcing.TIMEOUT_PER_JOB', 0.1):
        with pytest.raises(HTTPException) as exc_info:
            await run_custom_search(
                request=request,
                service=mock_autosourcing_service,
                keepa_service=mock_keepa_service
            )

        # Should raise 408 Request Timeout
        assert exc_info.value.status_code == 408
        assert "timeout" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_run_custom_completes_within_timeout():
    """
    Test run_custom endpoint completes successfully when within timeout.
    """
    # Create request
    request = RunCustomSearchRequest(
        profile_name="Test Fast Job",
        discovery_config={"categories": ["books"], "max_results": 5},
        scoring_config={"roi_min": 30, "velocity_min": 70}
    )

    # Mock dependencies
    mock_keepa_service = AsyncMock()
    mock_keepa_service.check_api_balance = AsyncMock(return_value=1000)

    mock_autosourcing_service = AsyncMock()
    # Make run_custom_search complete quickly
    mock_job = AutoSourcingJob(
        id=uuid4(),
        profile_name="Test Fast Job",
        status=JobStatus.SUCCESS,
        total_tested=5,
        total_selected=2,
        launched_at=datetime.now(timezone.utc),
        picks=[]
    )
    mock_autosourcing_service.run_custom_search = AsyncMock(return_value=mock_job)

    # Should complete successfully
    result = await run_custom_search(
        request=request,
        service=mock_autosourcing_service,
        keepa_service=mock_keepa_service
    )

    assert result.status == JobStatus.SUCCESS
    assert result.profile_name == "Test Fast Job"


def test_timeout_constant_is_defined():
    """Verify TIMEOUT_PER_JOB constant is properly defined."""
    assert TIMEOUT_PER_JOB == 120, f"TIMEOUT_PER_JOB should be 120 seconds, got {TIMEOUT_PER_JOB}"
