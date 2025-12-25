"""
Integration tests for Phase 8.2 ASIN History endpoints.
Testing real HTTP requests with mocked database.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.db import get_db_session


def create_mock_asin_history(asin: str, days_ago: int = 0, bsr: int = 10000, price: float = 15.99):
    """Create a mock ASINHistory object."""
    mock = MagicMock()
    mock.id = f"{asin}-{days_ago}"
    mock.asin = asin
    mock.tracked_at = datetime.utcnow() - timedelta(days=days_ago)
    mock.bsr = bsr
    mock.price = Decimal(str(price))
    mock.seller_count = 5
    mock.amazon_on_listing = False
    mock.extra_data = {}
    return mock


@pytest.fixture
def client():
    """Create test client with mocked DB."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create mock async DB session."""
    mock_session = AsyncMock()
    return mock_session


class TestASINHistoryTrends:
    """Tests for GET /api/v1/asin-history/trends/{asin}"""

    def test_trends_with_valid_data(self, client):
        """Trends endpoint returns valid trend analysis."""
        mock_records = [
            create_mock_asin_history("TEST123", days_ago=30, bsr=20000),
            create_mock_asin_history("TEST123", days_ago=15, bsr=15000),
            create_mock_asin_history("TEST123", days_ago=0, bsr=10000),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records

        async def mock_get_db():
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            yield mock_session

        app.dependency_overrides[get_db_session] = mock_get_db

        try:
            response = client.get("/api/v1/asin-history/trends/TEST123?days=90")
            assert response.status_code == 200
            data = response.json()
            assert data['asin'] == 'TEST123'
            assert data['data_points'] == 3
            assert 'bsr' in data
            assert data['bsr']['trend'] == 'improving'
        finally:
            app.dependency_overrides.clear()

    def test_trends_no_history_returns_404(self, client):
        """No history data returns 404."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        async def mock_get_db():
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            yield mock_session

        app.dependency_overrides[get_db_session] = mock_get_db

        try:
            response = client.get("/api/v1/asin-history/trends/NODATA123")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_trends_days_validation(self, client):
        """Days parameter is validated (1-365)."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        async def mock_get_db():
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            yield mock_session

        app.dependency_overrides[get_db_session] = mock_get_db

        try:
            response = client.get("/api/v1/asin-history/trends/TEST123?days=0")
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


class TestASINHistoryRecords:
    """Tests for GET /api/v1/asin-history/records/{asin}"""

    def test_records_returns_list(self, client):
        """Records endpoint returns list of history."""
        mock_records = [
            create_mock_asin_history("TEST123", days_ago=0),
            create_mock_asin_history("TEST123", days_ago=1),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records

        async def mock_get_db():
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            yield mock_session

        app.dependency_overrides[get_db_session] = mock_get_db

        try:
            response = client.get("/api/v1/asin-history/records/TEST123")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2
        finally:
            app.dependency_overrides.clear()

    def test_records_limit_validation(self, client):
        """Limit parameter is validated (1-1000)."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        async def mock_get_db():
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            yield mock_session

        app.dependency_overrides[get_db_session] = mock_get_db

        try:
            response = client.get("/api/v1/asin-history/records/TEST123?limit=0")
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_records_empty_returns_empty_list(self, client):
        """No records returns empty list."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        async def mock_get_db():
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            yield mock_session

        app.dependency_overrides[get_db_session] = mock_get_db

        try:
            response = client.get("/api/v1/asin-history/records/EMPTY123")
            assert response.status_code == 200
            data = response.json()
            assert data == []
        finally:
            app.dependency_overrides.clear()


class TestASINHistoryLatest:
    """Tests for GET /api/v1/asin-history/latest/{asin}"""

    def test_latest_returns_single_record(self, client):
        """Latest endpoint returns single most recent record."""
        mock_record = create_mock_asin_history("TEST123", days_ago=0)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_record

        async def mock_get_db():
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            yield mock_session

        app.dependency_overrides[get_db_session] = mock_get_db

        try:
            response = client.get("/api/v1/asin-history/latest/TEST123")
            assert response.status_code == 200
            data = response.json()
            assert data['asin'] == 'TEST123'
        finally:
            app.dependency_overrides.clear()

    def test_latest_not_found_returns_404(self, client):
        """No record found returns 404."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        async def mock_get_db():
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            yield mock_session

        app.dependency_overrides[get_db_session] = mock_get_db

        try:
            response = client.get("/api/v1/asin-history/latest/NOTFOUND123")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
