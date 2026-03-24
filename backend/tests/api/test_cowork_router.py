"""
Tests for Cowork API router endpoints.
"""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.db import get_db_session

VALID_TOKEN = "test-cowork-token-123"


def _auth_header(token: str = VALID_TOKEN) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _mock_db_execute_result():
    """Create a mock result for db.execute() calls."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_result.scalars.return_value.first.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    return mock_result


@pytest.fixture(autouse=True)
def _override_db_session():
    """Override get_db_session dependency with a mock."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=_mock_db_execute_result())

    async def _fake_session():
        yield mock_session

    app.dependency_overrides[get_db_session] = _fake_session
    yield mock_session
    app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture(autouse=True)
def _mock_db_health():
    """Mock db_manager.health_check for all tests."""
    with patch("app.core.db.db_manager.health_check", new_callable=AsyncMock, return_value=True):
        yield


def _settings_patch(**overrides):
    """Return a patch context for get_settings with sensible defaults."""
    defaults = {
        "cowork_api_token": VALID_TOKEN,
        "keepa_api_key": "fake",
        "environment": "test",
    }
    defaults.update(overrides)
    p = patch("app.api.v1.routers.cowork.get_settings")
    return p, defaults


def _client_with_settings(**overrides):
    """Create TestClient and settings patch context."""
    p, defaults = _settings_patch(**overrides)
    mock_settings = p.start()
    for k, v in defaults.items():
        setattr(mock_settings.return_value, k, v)
    client = TestClient(app)
    return client, p


def test_cowork_no_token():
    """GET dashboard without auth header returns 401."""
    client, p = _client_with_settings()
    try:
        response = client.get("/api/v1/cowork/dashboard-summary")
        assert response.status_code == 401
    finally:
        p.stop()


def test_cowork_wrong_token():
    """GET dashboard with wrong Bearer returns 401."""
    client, p = _client_with_settings()
    try:
        response = client.get(
            "/api/v1/cowork/dashboard-summary",
            headers=_auth_header("wrong-token"),
        )
        assert response.status_code == 401
    finally:
        p.stop()


def test_cowork_no_config():
    """GET dashboard when COWORK_API_TOKEN not set returns 503."""
    client, p = _client_with_settings(cowork_api_token=None)
    try:
        response = client.get(
            "/api/v1/cowork/dashboard-summary",
            headers=_auth_header(),
        )
        assert response.status_code == 503
    finally:
        p.stop()


def test_dashboard_summary_smoke():
    """GET dashboard with valid token returns 200 with valid schema."""
    client, p = _client_with_settings()
    try:
        response = client.get(
            "/api/v1/cowork/dashboard-summary",
            headers=_auth_header(),
        )
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "db_healthy" in data
        assert "keepa_configured" in data
        assert "autosourcing" in data
        assert "daily_review" in data
        assert isinstance(data["autosourcing"]["jobs_last_24h"], int)
        assert isinstance(data["autosourcing"]["picks_last_24h"], int)
    finally:
        p.stop()


def test_fetch_and_score_no_keepa():
    """POST fetch-and-score with no Keepa returns 503."""
    client, p = _client_with_settings(keepa_api_key=None)
    try:
        with patch("app.api.v1.routers.cowork.get_keepa_service", new_callable=AsyncMock, return_value=MagicMock()):
            response = client.post(
                "/api/v1/cowork/fetch-and-score",
                json={},
                headers=_auth_header(),
            )
        assert response.status_code == 503
    finally:
        p.stop()


def test_daily_buy_list_empty():
    """GET buy-list returns 200 with empty items."""
    client, p = _client_with_settings()
    try:
        with patch(
            "app.api.v1.routers.cowork.generate_actionable_review",
            return_value={"generated_at": "2026-01-01T00:00:00", "items": []},
        ):
            response = client.get(
                "/api/v1/cowork/daily-buy-list",
                headers=_auth_header(),
            )
        assert response.status_code == 200
        data = response.json()
        assert data["total_actionable"] == 0
        assert data["items"] == []
    finally:
        p.stop()


def test_daily_buy_list_smoke(_override_db_session):
    """GET buy-list returns 200 with valid schema when picks exist."""
    mock_pick = MagicMock()
    mock_pick.asin = "B00TEST123"
    mock_pick.title = "Test Book"
    mock_pick.roi_percentage = 45.0
    mock_pick.bsr = 50000
    mock_pick.amazon_on_listing = False
    mock_pick.current_price = 20.0
    mock_pick.estimated_buy_cost = 7.0
    mock_pick.condition_signal = None
    mock_pick.stability_score = 0.8
    mock_pick.is_ignored = False
    mock_pick.created_at = None

    # First execute call returns picks, subsequent calls return empty (history + config)
    mock_result_with_pick = MagicMock()
    mock_result_with_pick.scalars.return_value.all.return_value = [mock_pick]
    mock_result_empty = _mock_db_execute_result()

    _override_db_session.execute = AsyncMock(
        side_effect=[mock_result_with_pick, mock_result_empty, mock_result_empty]
    )

    mock_items = [
        {
            "asin": "B00TEST123",
            "title": "Test Book",
            "classification": "JACKPOT",
            "roi_percentage": 45.0,
            "bsr": 50000,
            "action_recommendation": "BUY",
        }
    ]
    client, p = _client_with_settings()
    try:
        with patch(
            "app.api.v1.routers.cowork.generate_actionable_review",
            return_value={"generated_at": "2026-01-01T00:00:00", "items": mock_items},
        ):
            response = client.get(
                "/api/v1/cowork/daily-buy-list",
                headers=_auth_header(),
            )
        assert response.status_code == 200
        data = response.json()
        assert data["total_actionable"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["asin"] == "B00TEST123"
        assert "generated_at" in data
        assert "days_back" in data
    finally:
        p.stop()
