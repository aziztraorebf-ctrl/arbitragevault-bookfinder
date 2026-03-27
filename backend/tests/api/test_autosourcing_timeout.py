"""
Tests for AutoSourcing timeout protection.

The timeout is now enforced inside AutoSourcingService.run_custom_search(),
not in the router endpoint. These tests verify the infrastructure is in place.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from app.models.autosourcing import AutoSourcingJob, JobStatus
from app.schemas.autosourcing_safeguards import TIMEOUT_PER_JOB
from datetime import datetime, timezone
from uuid import uuid4


@pytest.mark.asyncio
async def test_run_custom_delegates_to_service():
    """
    Test run_custom endpoint delegates to service.run_custom_search().

    Timeout protection is handled inside the service, not the router.
    """
    from app.api.v1.routers.autosourcing import run_custom_search, RunCustomSearchRequest

    request = RunCustomSearchRequest(
        profile_name="Test Job",
        discovery_config={"categories": ["books"], "max_results": 10},
        scoring_config={"roi_min": 30, "velocity_min": 70}
    )

    mock_keepa_service = AsyncMock()
    mock_keepa_service.check_api_balance = AsyncMock(return_value=1000)

    mock_job = AutoSourcingJob(
        id=uuid4(),
        profile_name="Test Job",
        status=JobStatus.SUCCESS,
        total_tested=5,
        total_selected=2,
        launched_at=datetime.now(timezone.utc),
        picks=[]
    )

    mock_autosourcing_service = AsyncMock()
    mock_autosourcing_service.run_custom_search = AsyncMock(return_value=mock_job)

    mock_user = MagicMock()

    result = await run_custom_search(
        request=request,
        service=mock_autosourcing_service,
        keepa_service=mock_keepa_service,
        current_user=mock_user,
    )

    assert result.status == JobStatus.SUCCESS
    assert result.profile_name == "Test Job"
    mock_autosourcing_service.run_custom_search.assert_called_once()


@pytest.mark.asyncio
async def test_run_custom_completes_within_timeout():
    """
    Test run_custom endpoint completes successfully when within timeout.
    """
    from app.api.v1.routers.autosourcing import run_custom_search, RunCustomSearchRequest

    request = RunCustomSearchRequest(
        profile_name="Test Fast Job",
        discovery_config={"categories": ["books"], "max_results": 5},
        scoring_config={"roi_min": 30, "velocity_min": 70}
    )

    mock_keepa_service = AsyncMock()
    mock_keepa_service.check_api_balance = AsyncMock(return_value=1000)

    mock_job = AutoSourcingJob(
        id=uuid4(),
        profile_name="Test Fast Job",
        status=JobStatus.SUCCESS,
        total_tested=5,
        total_selected=2,
        launched_at=datetime.now(timezone.utc),
        picks=[]
    )
    mock_autosourcing_service = AsyncMock()
    mock_autosourcing_service.run_custom_search = AsyncMock(return_value=mock_job)

    mock_user = MagicMock()

    result = await run_custom_search(
        request=request,
        service=mock_autosourcing_service,
        keepa_service=mock_keepa_service,
        current_user=mock_user,
    )

    assert result.status == JobStatus.SUCCESS
    assert result.profile_name == "Test Fast Job"


def test_timeout_constant_is_defined():
    """Verify TIMEOUT_PER_JOB constant is properly defined."""
    assert TIMEOUT_PER_JOB == 120, f"TIMEOUT_PER_JOB should be 120 seconds, got {TIMEOUT_PER_JOB}"
