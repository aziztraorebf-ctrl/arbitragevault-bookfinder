"""Integration tests for Products endpoint token guard."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.core.db import get_db_session
from app.services.keepa_service import get_keepa_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def override_dependencies():
    """Override dependencies for all tests."""
    # Mock DB session
    async def mock_db():
        yield MagicMock()

    app.dependency_overrides[get_db_session] = mock_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_keepa_sufficient():
    """Mock KeepaService with sufficient balance."""
    mock_keepa = MagicMock()
    mock_keepa.close = AsyncMock()

    async def mock_can_perform(action):
        return {
            "can_proceed": True,
            "current_balance": 50,
            "required_tokens": 10,
            "action": action
        }

    mock_keepa.can_perform_action = mock_can_perform

    def override_keepa():
        return mock_keepa

    app.dependency_overrides[get_keepa_service] = override_keepa
    yield mock_keepa
    app.dependency_overrides.pop(get_keepa_service, None)


@pytest.fixture
def mock_keepa_insufficient():
    """Mock KeepaService with insufficient balance."""
    mock_keepa = MagicMock()
    mock_keepa.close = AsyncMock()

    async def mock_can_perform(action):
        return {
            "can_proceed": False,
            "current_balance": 5,
            "required_tokens": 10,
            "action": action
        }

    mock_keepa.can_perform_action = mock_can_perform

    def override_keepa():
        return mock_keepa

    app.dependency_overrides[get_keepa_service] = override_keepa
    yield mock_keepa
    app.dependency_overrides.pop(get_keepa_service, None)


def test_manual_search_blocked_when_insufficient_tokens(mock_keepa_insufficient):
    """Test manual search returns 429 when tokens insufficient."""
    response = client.post("/api/v1/products/discover-with-scoring", json={
        "domain": 1,
        "bsr_min": 10000,
        "bsr_max": 50000,
        "price_min": 10.0,
        "price_max": 50.0
    })

    assert response.status_code == 429
    data = response.json()
    assert "Insufficient Keepa tokens" in data["detail"]["detail"]
    assert data["detail"]["current_balance"] == 5
    assert data["detail"]["required_tokens"] == 10
    assert "X-Token-Balance" in response.headers


def test_manual_search_proceeds_when_sufficient_tokens(mock_keepa_sufficient):
    """Test manual search proceeds normally when tokens sufficient."""
    # Mock the actual product discovery logic
    with patch("app.services.keepa_product_finder.KeepaProductFinderService.discover_with_scoring") as mock_discover:
        mock_discover.return_value = []

        response = client.post("/api/v1/products/discover-with-scoring", json={
            "domain": 1,
            "bsr_min": 10000,
            "bsr_max": 50000
        })

        # Should NOT be 429
        assert response.status_code != 429
