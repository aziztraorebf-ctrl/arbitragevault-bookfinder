"""
Integration tests for Phase 8.0 Analytics API endpoints.
Testing real HTTP requests through FastAPI TestClient.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

from app.main import app
from app.core.db import get_db_session


def override_get_db_session():
    """Override DB session dependency for testing."""
    async def _get_test_session():
        mock_session = AsyncMock(spec=AsyncSession)
        yield mock_session
    return _get_test_session


@pytest.fixture
def client():
    """Create test client with DB dependency override."""
    app.dependency_overrides[get_db_session] = override_get_db_session()
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


class TestAnalyticsEndpoints:
    """Integration tests for /api/v1/analytics endpoints."""

    def test_calculate_analytics_valid_request(self, client):
        """POST /calculate-analytics with valid data returns all components."""
        response = client.post(
            "/api/v1/analytics/calculate-analytics",
            json={
                "asin": "TEST123",
                "title": "Test Book",
                "estimated_buy_price": "5.00",
                "estimated_sell_price": "19.99",
                "bsr": 12000,
                "seller_count": 5
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data['asin'] == 'TEST123'
        assert 'velocity' in data
        assert 'price_stability' in data
        assert 'roi' in data
        assert 'competition' in data
        assert 'slow_velocity_risk' in data  # Renamed from dead_inventory_risk

    def test_calculate_risk_score_valid(self, client):
        """POST /calculate-risk-score returns proper risk assessment."""
        response = client.post(
            "/api/v1/analytics/calculate-risk-score",
            json={
                "asin": "RISK123",
                "estimated_buy_price": "10.00",
                "estimated_sell_price": "25.00",
                "bsr": 50000,
                "category": "books",
                "seller_count": 10,
                "amazon_on_listing": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data['asin'] == 'RISK123'
        assert 'risk_score' in data
        assert 'risk_level' in data
        assert data['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        assert 'components' in data
        assert 'recommendations' in data

    def test_generate_recommendation_valid(self, client):
        """POST /generate-recommendation returns valid recommendation tier."""
        response = client.post(
            "/api/v1/analytics/generate-recommendation",
            json={
                "asin": "REC123",
                "title": "Recommendation Test",
                "estimated_buy_price": "8.00",
                "estimated_sell_price": "24.00",
                "bsr": 15000,
                "seller_count": 3,
                "amazon_on_listing": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data['asin'] == 'REC123'
        assert 'recommendation' in data
        assert data['recommendation'] in ['STRONG_BUY', 'BUY', 'CONSIDER', 'WATCH', 'SKIP', 'AVOID']
        assert 'confidence_percent' in data
        assert 'criteria_passed' in data
        assert 'next_steps' in data

    def test_product_decision_valid(self, client):
        """POST /product-decision returns complete decision card."""
        response = client.post(
            "/api/v1/analytics/product-decision",
            json={
                "asin": "DEC123",
                "title": "Decision Test Product",
                "estimated_buy_price": "6.00",
                "estimated_sell_price": "22.00",
                "bsr": 8000,
                "seller_count": 4,
                "fba_seller_count": 2,
                "amazon_on_listing": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data['asin'] == 'DEC123'
        # Complete decision card has all sections
        assert 'velocity' in data
        assert 'price_stability' in data
        assert 'roi' in data
        assert 'competition' in data
        assert 'risk' in data
        assert 'recommendation' in data

    def test_missing_required_fields_returns_422(self, client):
        """Missing required fields should return 422 validation error."""
        response = client.post(
            "/api/v1/analytics/calculate-analytics",
            json={
                "asin": "TEST123"
                # Missing estimated_buy_price and estimated_sell_price
            }
        )
        assert response.status_code == 422

    def test_invalid_decimal_fields_handled(self, client):
        """Invalid decimal values should return 422."""
        response = client.post(
            "/api/v1/analytics/calculate-analytics",
            json={
                "asin": "TEST123",
                "estimated_buy_price": "not_a_number",
                "estimated_sell_price": "also_invalid"
            }
        )
        assert response.status_code == 422
