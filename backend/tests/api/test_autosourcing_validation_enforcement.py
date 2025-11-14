"""
Tests for AutoSourcing validation enforcement in run_custom endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app
from app.api.v1.routers.autosourcing import get_autosourcing_service

# Mock service for dependency override
async def mock_autosourcing_service():
    return MagicMock()

def test_run_custom_rejects_expensive_jobs(mock_keepa_balance):
    """Test run_custom endpoint rejects jobs exceeding MAX_TOKENS_PER_JOB."""
    # Override dependency to prevent DB access
    app.dependency_overrides[get_autosourcing_service] = mock_autosourcing_service

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/autosourcing/run-custom",
            json={
                "profile_name": "Test Expensive Job",
                "discovery_config": {
                    "categories": ["books", "electronics", "toys", "games"],
                    "max_results": 200
                },
                "scoring_config": {
                    "roi_min": 30,
                    "velocity_min": 70
                }
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "JOB_TOO_EXPENSIVE" in data.get("detail", {}).get("error", "")
    finally:
        # Clean up override
        app.dependency_overrides.clear()

def test_run_custom_rejects_insufficient_balance():
    """Test run_custom endpoint rejects jobs when token balance too low."""
    # Override dependency AND mock balance
    app.dependency_overrides[get_autosourcing_service] = mock_autosourcing_service

    with patch('app.services.keepa_service.KeepaService.check_api_balance', new_callable=AsyncMock) as mock_balance:
        mock_balance.return_value = 30

        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/autosourcing/run-custom",
                json={
                    "profile_name": "Test Low Balance",
                    "discovery_config": {
                        "categories": ["books"],
                        "max_results": 20
                    },
                    "scoring_config": {
                        "roi_min": 30,
                        "velocity_min": 70
                    }
                }
            )

            assert response.status_code == 429
            data = response.json()
            assert "INSUFFICIENT_TOKENS" in data.get("detail", {}).get("error", "")
        finally:
            # Clean up override
            app.dependency_overrides.clear()
