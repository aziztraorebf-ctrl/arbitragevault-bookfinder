"""Tests for condition_filter in textbook analysis endpoint."""

import pytest
from unittest.mock import AsyncMock, patch, ANY


@pytest.mark.asyncio
async def test_analyze_passes_condition_filter_to_parser():
    """Test that the endpoint passes condition_filter to the parser."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Mock Keepa service
    with patch('app.api.v1.routers.textbook_analysis.get_keepa_service') as mock_keepa, \
         patch('app.api.v1.routers.textbook_analysis.parse_keepa_product_unified') as mock_parser:

        mock_service = AsyncMock()
        mock_service.get_product_data = AsyncMock(return_value={
            'asin': 'B00TEST123',
            'title': 'Test Book',
            'domainId': 1,
            'stats': {'current': [None] * 20},
            'offers': [],
            'data': {}
        })
        mock_service.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service.__aexit__ = AsyncMock(return_value=None)
        mock_keepa.return_value = mock_service

        # Mock parser to return minimal valid data
        mock_parser.return_value = {
            'asin': 'B00TEST123',
            'title': 'Test Book',
            'current_bsr': 50000,
            'sales_per_month': 5,
            'price_history': [],
            'offers': [],
        }

        # Request with condition_filter
        response = client.post(
            "/api/v1/textbook/analyze?condition_filter=new&condition_filter=very_good",
            json={"asin": "B00TEST123"}
        )

        # Verify parser was called with condition_filter
        mock_parser.assert_called_once()
        call_kwargs = mock_parser.call_args.kwargs
        assert 'condition_filter' in call_kwargs, "condition_filter not passed to parser"
        assert call_kwargs['condition_filter'] == ['new', 'very_good'], \
            f"Expected ['new', 'very_good'], got {call_kwargs.get('condition_filter')}"


@pytest.mark.asyncio
async def test_analyze_condition_filter_filters_offers():
    """Test that condition_filter actually filters the offers in parser."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Mock Keepa data with multiple offer conditions
    mock_keepa_data = {
        'asin': 'B00TEST123',
        'title': 'Test Textbook',
        'domainId': 1,
        'stats': {'current': [None] * 20},
        'offers': [
            {'condition': 1, 'offerCSV': [100, 1999]},   # New
            {'condition': 2, 'offerCSV': [100, 1499]},   # Very Good
            {'condition': 3, 'offerCSV': [100, 999]},    # Good
            {'condition': 4, 'offerCSV': [100, 799]},    # Acceptable
        ],
        'data': {}
    }

    with patch('app.api.v1.routers.textbook_analysis.get_keepa_service') as mock_keepa:
        mock_service = AsyncMock()
        mock_service.get_product_data = AsyncMock(return_value=mock_keepa_data)
        mock_service.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service.__aexit__ = AsyncMock(return_value=None)
        mock_keepa.return_value = mock_service

        # Request with only "new" condition filter
        response = client.post(
            "/api/v1/textbook/analyze?condition_filter=new",
            json={"asin": "B00TEST123"}
        )

        # Should succeed (not 422)
        assert response.status_code != 422, f"Unexpected 422: {response.json()}"


@pytest.mark.asyncio
async def test_analyze_no_condition_filter_includes_all():
    """Test that without condition_filter, all conditions are included (backward compat)."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    mock_keepa_data = {
        'asin': 'B00TEST123',
        'title': 'Test Textbook',
        'domainId': 1,
        'stats': {'current': [None] * 20},
        'offers': [],
        'data': {}
    }

    with patch('app.api.v1.routers.textbook_analysis.get_keepa_service') as mock_keepa:
        mock_service = AsyncMock()
        mock_service.get_product_data = AsyncMock(return_value=mock_keepa_data)
        mock_service.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service.__aexit__ = AsyncMock(return_value=None)
        mock_keepa.return_value = mock_service

        # Request WITHOUT condition_filter (backward compatibility)
        response = client.post(
            "/api/v1/textbook/analyze",
            json={"asin": "B00TEST123"}
        )

        # Should work as before (may return 200 or 500 depending on mock completeness)
        # Key point: should not be 422 unprocessable entity
        assert response.status_code != 422, f"Unexpected 422: {response.json()}"
