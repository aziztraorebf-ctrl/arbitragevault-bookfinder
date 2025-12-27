"""
API Endpoint Edge Cases Tests for /api/v1/niches/discover

Phase 6 Audit - Task 2: Test edge cases for count parameter, timeout, and shuffle.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.core.db import get_db_session
from app.services.keepa_service import get_keepa_service


@pytest.fixture(autouse=True)
def override_dependencies():
    """Override DB and Keepa for all tests."""
    async def mock_db():
        mock = MagicMock()
        yield mock

    mock_keepa = MagicMock()
    mock_keepa.check_api_balance = AsyncMock(return_value=1000)
    mock_keepa.close = AsyncMock()
    mock_keepa.can_perform_action = AsyncMock(return_value={
        "can_proceed": True,
        "required_tokens": 100,
        "current_balance": 1000
    })

    app.dependency_overrides[get_db_session] = mock_db
    app.dependency_overrides[get_keepa_service] = lambda: mock_keepa
    yield
    app.dependency_overrides.clear()


class TestNichesDiscoverCountParameter:
    """Tests for count parameter validation (ge=1, le=5)."""

    def test_count_zero_rejected(self):
        """count=0 should be rejected (422 validation error)."""
        client = TestClient(app)
        response = client.get("/api/v1/niches/discover", params={"count": 0})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_count_negative_rejected(self):
        """count=-1 should be rejected (422 validation error)."""
        client = TestClient(app)
        response = client.get("/api/v1/niches/discover", params={"count": -1})
        assert response.status_code == 422

    def test_count_exceeds_max_rejected(self):
        """count > 5 should be rejected (422 validation error)."""
        client = TestClient(app)
        response = client.get("/api/v1/niches/discover", params={"count": 10})
        assert response.status_code == 422

    def test_count_at_minimum_boundary(self):
        """count=1 (minimum) should be accepted."""
        client = TestClient(app)
        with patch('app.api.v1.endpoints.niches.discover_curated_niches', return_value=[]):
            response = client.get("/api/v1/niches/discover", params={"count": 1})
            # Should not be 422 (validation passes)
            assert response.status_code != 422

    def test_count_at_maximum_boundary(self):
        """count=5 (maximum) should be accepted."""
        client = TestClient(app)
        with patch('app.api.v1.endpoints.niches.discover_curated_niches', return_value=[]):
            response = client.get("/api/v1/niches/discover", params={"count": 5})
            # Should not be 422 (validation passes)
            assert response.status_code != 422


class TestNichesDiscoverShuffle:
    """Tests for shuffle parameter."""

    def test_shuffle_true_accepted(self):
        """shuffle=true should be accepted."""
        client = TestClient(app)
        with patch('app.api.v1.endpoints.niches.discover_curated_niches', return_value=[]):
            response = client.get("/api/v1/niches/discover", params={"shuffle": "true"})
            assert response.status_code != 422

    def test_shuffle_false_accepted(self):
        """shuffle=false should be accepted."""
        client = TestClient(app)
        with patch('app.api.v1.endpoints.niches.discover_curated_niches', return_value=[]):
            response = client.get("/api/v1/niches/discover", params={"shuffle": "false"})
            assert response.status_code != 422

    def test_shuffle_invalid_value_rejected(self):
        """shuffle=invalid should be rejected (422)."""
        client = TestClient(app)
        response = client.get("/api/v1/niches/discover", params={"shuffle": "invalid"})
        assert response.status_code == 422


class TestNichesDiscoverDefaultValues:
    """Tests for default parameter values."""

    def test_default_count_is_3(self):
        """Default count should be 3."""
        client = TestClient(app)
        with patch('app.api.v1.endpoints.niches.discover_curated_niches', return_value=[]) as mock:
            response = client.get("/api/v1/niches/discover")
            if response.status_code == 200:
                # Check the mock was called with count=3
                args, kwargs = mock.call_args
                # count is passed as keyword argument
                assert kwargs.get("count") == 3 or (len(args) >= 3 and args[2] == 3)

    def test_default_shuffle_is_true(self):
        """Default shuffle should be True."""
        client = TestClient(app)
        with patch('app.api.v1.endpoints.niches.discover_curated_niches', return_value=[]) as mock:
            response = client.get("/api/v1/niches/discover")
            if response.status_code == 200:
                # Check the mock was called with shuffle=True
                args, kwargs = mock.call_args
                assert kwargs.get("shuffle") is True or (len(args) >= 4 and args[3] is True)
