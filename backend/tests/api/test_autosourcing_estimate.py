"""
Tests for AutoSourcing cost estimation API endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_estimate_endpoint_returns_cost_breakdown(mock_keepa_balance):
    """Test /estimate endpoint returns complete cost breakdown."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/autosourcing/estimate",
        json={
            "discovery_config": {
                "categories": ["books"],
                "max_results": 50
            }
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "estimated_tokens" in data
    assert "current_balance" in data
    assert "safe_to_proceed" in data
    assert isinstance(data["estimated_tokens"], int)
    assert data["estimated_tokens"] > 0

def test_estimate_endpoint_warns_expensive_jobs(mock_keepa_balance):
    """Test /estimate endpoint warns about jobs exceeding MAX_TOKENS_PER_JOB."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/autosourcing/estimate",
        json={
            "discovery_config": {
                "categories": ["books", "electronics", "toys"],
                "max_results": 100
            }
        }
    )

    data = response.json()

    # Should warn but not reject (estimation only)
    assert "warning_message" in data
    if data["estimated_tokens"] > 200:
        assert data["safe_to_proceed"] is False

def test_estimate_endpoint_validation_errors():
    """Test /estimate endpoint validates request body."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/autosourcing/estimate",
        json={}
    )

    assert response.status_code == 422
