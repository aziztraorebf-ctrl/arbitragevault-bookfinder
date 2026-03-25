"""
Tests for Cowork API router endpoints.
"""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")

import uuid
from datetime import datetime

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.db import get_db_session
from app.models.autosourcing import JobStatus

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


# --- last-job-stats tests ---

def _make_mock_job(**overrides):
    """Create a mock AutoSourcingJob with realistic attributes."""
    job = MagicMock()
    job.id = overrides.get("id", uuid.uuid4())
    job.status = overrides.get("status", JobStatus.SUCCESS)
    job.total_tested = overrides.get("total_tested", 50)
    job.total_selected = overrides.get("total_selected", 5)
    job.created_at = overrides.get("created_at", datetime(2026, 3, 25, 12, 0, 0))
    job.picks = overrides.get("picks", [])
    return job


def test_last_job_stats_empty_db():
    """GET last-job-stats with no jobs returns null fields."""
    client, p = _client_with_settings()
    try:
        response = client.get(
            "/api/v1/cowork/last-job-stats",
            headers=_auth_header(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] is None
        assert data["status"] is None
        assert data["total_tested"] == 0
        assert data["total_selected"] == 0
        assert data["created_at"] is None
    finally:
        p.stop()


def test_last_job_stats_with_job(_override_db_session):
    """GET last-job-stats with existing job returns correct fields."""
    mock_job = _make_mock_job(
        total_tested=100,
        total_selected=8,
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_job
    _override_db_session.execute = AsyncMock(return_value=mock_result)

    client, p = _client_with_settings()
    try:
        response = client.get(
            "/api/v1/cowork/last-job-stats",
            headers=_auth_header(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == str(mock_job.id)
        assert data["status"] == "success"
        assert data["total_tested"] == 100
        assert data["total_selected"] == 8
        assert data["created_at"] is not None
    finally:
        p.stop()


def test_last_job_stats_checks_real_attributes():
    """Verify last-job-stats only accesses attributes that exist on AutoSourcingJob model."""
    from app.models.autosourcing import AutoSourcingJob

    required_attrs = ["id", "status", "total_tested", "total_selected", "created_at"]
    model_columns = {col.key for col in AutoSourcingJob.__table__.columns}

    for attr in required_attrs:
        assert attr in model_columns, (
            f"Phantom attribute: last-job-stats accesses '{attr}' "
            f"but it does not exist on AutoSourcingJob model. "
            f"Available columns: {sorted(model_columns)}"
        )


def test_last_job_stats_does_not_use_total_discovered():
    """Regression: ensure total_discovered is NOT on the model (was the original bug)."""
    from app.models.autosourcing import AutoSourcingJob

    model_columns = {col.key for col in AutoSourcingJob.__table__.columns}
    assert "total_discovered" not in model_columns, (
        "total_discovered should NOT exist on AutoSourcingJob. "
        "Use total_tested and total_selected instead."
    )


def test_last_job_stats_db_error_returns_500(_override_db_session):
    """GET last-job-stats should return 500 on DB error, not silent empty response."""
    _override_db_session.execute = AsyncMock(
        side_effect=RuntimeError("DB connection lost")
    )

    client, p = _client_with_settings()
    try:
        response = client.get(
            "/api/v1/cowork/last-job-stats",
            headers=_auth_header(),
        )
        # After fix: should return 500 instead of silently returning empty data
        assert response.status_code == 500
    finally:
        p.stop()


def test_last_job_stats_no_auth():
    """GET last-job-stats without auth returns 401."""
    client, p = _client_with_settings()
    try:
        response = client.get("/api/v1/cowork/last-job-stats")
        assert response.status_code == 401
    finally:
        p.stop()


# --- fetch-and-score tests ---

def test_fetch_and_score_success(_override_db_session):
    """POST fetch-and-score with valid config returns job result."""
    mock_job = _make_mock_job(total_selected=3)

    mock_service = AsyncMock()
    mock_service.run_custom_search = AsyncMock(return_value=mock_job)

    client, p = _client_with_settings()
    try:
        with patch(
            "app.api.v1.routers.cowork.get_keepa_service",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ), patch(
            "app.api.v1.routers.cowork.AutoSourcingService",
            return_value=mock_service,
        ):
            response = client.post(
                "/api/v1/cowork/fetch-and-score",
                json={"roi_min": 25.0, "max_results": 10},
                headers=_auth_header(),
            )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == str(mock_job.id)
        assert data["status"] == "success"
        assert data["picks_count"] == 3
        assert data["message"] == "Search completed successfully"
    finally:
        p.stop()


def test_fetch_and_score_merges_defaults(_override_db_session):
    """POST fetch-and-score with partial params merges with DEFAULT_PROFILE."""
    mock_job = _make_mock_job()

    mock_service = AsyncMock()
    mock_service.run_custom_search = AsyncMock(return_value=mock_job)

    client, p = _client_with_settings()
    try:
        with patch(
            "app.api.v1.routers.cowork.get_keepa_service",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ), patch(
            "app.api.v1.routers.cowork.AutoSourcingService",
            return_value=mock_service,
        ):
            # Send only roi_min, other params should come from defaults
            response = client.post(
                "/api/v1/cowork/fetch-and-score",
                json={"roi_min": 15.0},
                headers=_auth_header(),
            )
        assert response.status_code == 200
        # Verify the service was called with merged config
        call_kwargs = mock_service.run_custom_search.call_args
        assert call_kwargs is not None
    finally:
        p.stop()


def test_fetch_and_score_insufficient_tokens(_override_db_session):
    """POST fetch-and-score with insufficient tokens returns 402."""
    from app.core.exceptions import InsufficientTokensError

    mock_service = AsyncMock()
    mock_service.run_custom_search = AsyncMock(
        side_effect=InsufficientTokensError(current_balance=0, required_tokens=100)
    )

    client, p = _client_with_settings()
    try:
        with patch(
            "app.api.v1.routers.cowork.get_keepa_service",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ), patch(
            "app.api.v1.routers.cowork.AutoSourcingService",
            return_value=mock_service,
        ):
            response = client.post(
                "/api/v1/cowork/fetch-and-score",
                json={},
                headers=_auth_header(),
            )
        assert response.status_code == 402
    finally:
        p.stop()
