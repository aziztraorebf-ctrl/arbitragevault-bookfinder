"""Integration tests for Niche Discovery endpoint token guard."""
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

    async def mock_can_perform(action):
        return {
            "can_proceed": True,
            "current_balance": 150,
            "required_tokens": 50,
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

    async def mock_can_perform(action):
        return {
            "can_proceed": False,
            "current_balance": 10,
            "required_tokens": 50,
            "action": action
        }

    mock_keepa.can_perform_action = mock_can_perform

    def override_keepa():
        return mock_keepa

    app.dependency_overrides[get_keepa_service] = override_keepa
    yield mock_keepa
    app.dependency_overrides.pop(get_keepa_service, None)


def test_niche_discovery_blocked_when_insufficient_tokens(mock_keepa_insufficient):
    """Test niche discovery returns 429 when tokens insufficient."""
    response = client.get("/api/v1/niches/discover")

    assert response.status_code == 429
    data = response.json()
    assert "Insufficient Keepa tokens" in data["detail"]["detail"]
    assert data["detail"]["current_balance"] == 10
    assert data["detail"]["required_tokens"] == 50
    assert "X-Token-Balance" in response.headers


def test_niche_discovery_proceeds_when_sufficient_tokens(mock_keepa_sufficient):
    """Test niche discovery proceeds normally when tokens sufficient."""
    # Mock the actual niche discovery logic to avoid real Keepa API calls
    with patch("app.services.niche_templates.discover_curated_niches") as mock_discover:
        mock_discover.return_value = []

        response = client.get("/api/v1/niches/discover")

        # Should NOT be 429 (might be 200 or other depending on mock)
        assert response.status_code != 429
