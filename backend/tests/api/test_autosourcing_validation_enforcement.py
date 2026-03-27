"""
Tests for AutoSourcing validation enforcement in run_custom endpoint.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException

from app.api.v1.routers.autosourcing import run_custom_search, RunCustomSearchRequest


@pytest.mark.asyncio
async def test_run_custom_rejects_expensive_jobs():
    """Test run_custom endpoint rejects jobs exceeding MAX_TOKENS_PER_JOB."""
    request = RunCustomSearchRequest(
        profile_name="Test Expensive Job",
        discovery_config={
            "categories": ["books", "electronics", "toys", "games"],
            "max_results": 200
        },
        scoring_config={
            "roi_min": 30,
            "velocity_min": 70
        }
    )

    mock_keepa_service = AsyncMock()
    mock_keepa_service.check_api_balance = AsyncMock(return_value=1000)

    mock_service = AsyncMock()
    mock_user = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await run_custom_search(
            request=request,
            service=mock_service,
            keepa_service=mock_keepa_service,
            current_user=mock_user,
        )

    assert exc_info.value.status_code == 400
    assert "JOB_TOO_EXPENSIVE" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_run_custom_rejects_insufficient_balance():
    """Test run_custom endpoint rejects jobs when token balance too low."""
    request = RunCustomSearchRequest(
        profile_name="Test Low Balance",
        discovery_config={
            "categories": ["books"],
            "max_results": 20
        },
        scoring_config={
            "roi_min": 30,
            "velocity_min": 70
        }
    )

    mock_keepa_service = AsyncMock()
    mock_keepa_service.check_api_balance = AsyncMock(return_value=30)

    mock_service = AsyncMock()
    mock_user = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await run_custom_search(
            request=request,
            service=mock_service,
            keepa_service=mock_keepa_service,
            current_user=mock_user,
        )

    assert exc_info.value.status_code == 429
    assert "INSUFFICIENT_TOKENS" in str(exc_info.value.detail)
