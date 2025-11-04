"""Tests for require_tokens guard decorator."""
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock
from app.core.guards.require_tokens import require_tokens
from app.services.keepa_service import KeepaService


# Test app
app = FastAPI()

# Mock keepa service
mock_keepa = Mock(spec=KeepaService)


def get_mock_keepa():
    return mock_keepa


@app.post("/test-sufficient")
@require_tokens("manual_search")
async def endpoint_sufficient(keepa: KeepaService = Depends(get_mock_keepa)):
    return {"success": True}


@app.post("/test-insufficient")
@require_tokens("surprise_me")
async def endpoint_insufficient(keepa: KeepaService = Depends(get_mock_keepa)):
    return {"success": True}


@pytest.fixture
def client():
    return TestClient(app)


def test_require_tokens_allows_execution_when_sufficient(client):
    """Test decorator allows execution when tokens are sufficient."""
    # Mock sufficient balance
    mock_keepa.can_perform_action = AsyncMock(return_value={
        "can_proceed": True,
        "current_balance": 150,
        "required_tokens": 10,
        "action": "manual_search"
    })

    response = client.post("/test-sufficient")

    assert response.status_code == 200
    assert response.json() == {"success": True}
    mock_keepa.can_perform_action.assert_called_once_with("manual_search")


def test_require_tokens_blocks_execution_when_insufficient(client):
    """Test decorator blocks execution when tokens are insufficient."""
    # Mock insufficient balance
    mock_keepa.can_perform_action = AsyncMock(return_value={
        "can_proceed": False,
        "current_balance": 5,
        "required_tokens": 50,
        "action": "surprise_me"
    })

    response = client.post("/test-insufficient")

    assert response.status_code == 429
    data = response.json()
    # FastAPI wraps custom detail dict in another detail key
    error_detail = data["detail"]
    assert "Insufficient Keepa tokens" in error_detail["detail"]
    assert error_detail["current_balance"] == 5
    assert error_detail["required_tokens"] == 50
    mock_keepa.can_perform_action.assert_called_once_with("surprise_me")


def test_require_tokens_provides_informative_error_message(client):
    """Test error message includes actionable information for user."""
    mock_keepa.can_perform_action = AsyncMock(return_value={
        "can_proceed": False,
        "current_balance": 15,
        "required_tokens": 50,
        "action": "surprise_me"
    })

    response = client.post("/test-insufficient")

    assert response.status_code == 429
    data = response.json()
    # Should include current balance, required tokens, and deficit
    error_detail = data["detail"]
    assert error_detail["current_balance"] == 15
    assert error_detail["required_tokens"] == 50
    assert error_detail["deficit"] == 35
    assert "surprise_me" in error_detail["detail"]
