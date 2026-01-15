"""Tests for condition_filter in keepa ingest endpoint."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_ingest_passes_condition_filter_to_analyze_product():
    """Test that /keepa/ingest passes condition_filter to analyze_product."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Mock dependencies
    with patch('app.api.v1.routers.keepa.get_keepa_service') as mock_keepa, \
         patch('app.api.v1.routers.keepa.get_business_config_service') as mock_config, \
         patch('app.api.v1.routers.keepa.analyze_product') as mock_analyze:

        # Setup Keepa service mock
        mock_service = AsyncMock()
        mock_service.get_product_data = AsyncMock(return_value={
            'asin': 'B00TEST123',
            'title': 'Test Book',
            'domainId': 1,
            'stats': {'current': [None] * 20},
            'offers': [],
        })
        mock_service.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service.__aexit__ = AsyncMock(return_value=None)
        mock_keepa.return_value = mock_service

        # Setup config service mock
        mock_config_service = AsyncMock()
        mock_config_service.get_effective_config = AsyncMock(return_value={
            'roi': {'target_roi_percent': 30},
            'amazon_fee_pct': 15,
        })
        mock_config.return_value = mock_config_service

        # Setup analyze_product mock to return valid AnalysisResult
        mock_analysis = MagicMock()
        mock_analysis.asin = 'B00TEST123'
        mock_analysis.title = 'Test Book'
        mock_analysis.current_price = 19.99
        mock_analysis.current_bsr = 50000
        mock_analysis.pricing = {}
        mock_analysis.roi = {'roi_percentage': 35.0}
        mock_analysis.velocity = {'velocity_score': 60}
        mock_analysis.velocity_score = 60
        mock_analysis.price_stability_score = 70
        mock_analysis.confidence_score = 80
        mock_analysis.overall_rating = 'GOOD'
        mock_analysis.score_breakdown = {}
        mock_analysis.readable_summary = 'Test summary'
        mock_analysis.strategy_profile = 'balanced'
        mock_analysis.calculation_method = 'direct'
        mock_analysis.recommendation = 'BUY'
        mock_analysis.risk_factors = []
        mock_analyze.return_value = mock_analysis

        # Request with condition_filter
        response = client.post(
            "/api/v1/keepa/ingest",
            json={
                "identifiers": ["B00TEST123"],
                "condition_filter": ["new", "very_good", "good"]
            }
        )

        # Verify response is successful
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # Verify analyze_product was called with condition_filter
        mock_analyze.assert_called_once()
        call_kwargs = mock_analyze.call_args.kwargs
        assert 'condition_filter' in call_kwargs, "condition_filter not passed to analyze_product"
        assert call_kwargs['condition_filter'] == ['new', 'very_good', 'good'], \
            f"Expected ['new', 'very_good', 'good'], got {call_kwargs.get('condition_filter')}"


@pytest.mark.asyncio
async def test_ingest_without_condition_filter_passes_none():
    """Test that /keepa/ingest passes None when no condition_filter provided (backward compat)."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    with patch('app.api.v1.routers.keepa.get_keepa_service') as mock_keepa, \
         patch('app.api.v1.routers.keepa.get_business_config_service') as mock_config, \
         patch('app.api.v1.routers.keepa.analyze_product') as mock_analyze:

        # Setup mocks (same as above)
        mock_service = AsyncMock()
        mock_service.get_product_data = AsyncMock(return_value={
            'asin': 'B00TEST123',
            'title': 'Test Book',
            'domainId': 1,
            'stats': {'current': [None] * 20},
            'offers': [],
        })
        mock_service.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service.__aexit__ = AsyncMock(return_value=None)
        mock_keepa.return_value = mock_service

        mock_config_service = AsyncMock()
        mock_config_service.get_effective_config = AsyncMock(return_value={
            'roi': {'target_roi_percent': 30},
        })
        mock_config.return_value = mock_config_service

        mock_analysis = MagicMock()
        mock_analysis.asin = 'B00TEST123'
        mock_analysis.title = 'Test Book'
        mock_analysis.current_price = 19.99
        mock_analysis.current_bsr = 50000
        mock_analysis.pricing = {}
        mock_analysis.roi = {}
        mock_analysis.velocity = {}
        mock_analysis.velocity_score = 60
        mock_analysis.price_stability_score = 70
        mock_analysis.confidence_score = 80
        mock_analysis.overall_rating = 'GOOD'
        mock_analysis.score_breakdown = {}
        mock_analysis.readable_summary = 'Test'
        mock_analysis.strategy_profile = 'balanced'
        mock_analysis.calculation_method = None
        mock_analysis.recommendation = 'BUY'
        mock_analysis.risk_factors = []
        mock_analyze.return_value = mock_analysis

        # Request WITHOUT condition_filter
        response = client.post(
            "/api/v1/keepa/ingest",
            json={"identifiers": ["B00TEST123"]}
        )

        assert response.status_code == 200

        # Verify analyze_product was called with condition_filter=None
        mock_analyze.assert_called_once()
        call_kwargs = mock_analyze.call_args.kwargs
        assert call_kwargs.get('condition_filter') is None, \
            f"Expected None, got {call_kwargs.get('condition_filter')}"


@pytest.mark.asyncio
async def test_ingest_rejects_invalid_condition():
    """Test that /keepa/ingest rejects invalid condition values."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Request with invalid condition
    response = client.post(
        "/api/v1/keepa/ingest",
        json={
            "identifiers": ["B00TEST123"],
            "condition_filter": ["new", "invalid_condition"]
        }
    )

    # Should return 422 Unprocessable Entity (Pydantic validation error)
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    data = response.json()
    assert "detail" in data
    # Check that error mentions the invalid condition
    error_str = str(data)
    assert "invalid_condition" in error_str.lower() or "condition" in error_str.lower()


@pytest.mark.asyncio
async def test_ingest_accepts_single_condition():
    """Test that /keepa/ingest accepts a single condition filter."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    with patch('app.api.v1.routers.keepa.get_keepa_service') as mock_keepa, \
         patch('app.api.v1.routers.keepa.get_business_config_service') as mock_config, \
         patch('app.api.v1.routers.keepa.analyze_product') as mock_analyze:

        mock_service = AsyncMock()
        mock_service.get_product_data = AsyncMock(return_value={
            'asin': 'B00TEST123',
            'title': 'Test Book',
            'domainId': 1,
            'stats': {'current': [None] * 20},
            'offers': [],
        })
        mock_service.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service.__aexit__ = AsyncMock(return_value=None)
        mock_keepa.return_value = mock_service

        mock_config_service = AsyncMock()
        mock_config_service.get_effective_config = AsyncMock(return_value={})
        mock_config.return_value = mock_config_service

        mock_analysis = MagicMock()
        mock_analysis.asin = 'B00TEST123'
        mock_analysis.title = 'Test Book'
        mock_analysis.current_price = 19.99
        mock_analysis.current_bsr = 50000
        mock_analysis.pricing = {}
        mock_analysis.roi = {}
        mock_analysis.velocity = {}
        mock_analysis.velocity_score = 60
        mock_analysis.price_stability_score = 70
        mock_analysis.confidence_score = 80
        mock_analysis.overall_rating = 'GOOD'
        mock_analysis.score_breakdown = {}
        mock_analysis.readable_summary = 'Test'
        mock_analysis.strategy_profile = 'balanced'
        mock_analysis.calculation_method = None
        mock_analysis.recommendation = 'BUY'
        mock_analysis.risk_factors = []
        mock_analyze.return_value = mock_analysis

        # Request with single condition (only 'new')
        response = client.post(
            "/api/v1/keepa/ingest",
            json={
                "identifiers": ["B00TEST123"],
                "condition_filter": ["new"]
            }
        )

        assert response.status_code == 200

        # Verify condition_filter passed correctly
        call_kwargs = mock_analyze.call_args.kwargs
        assert call_kwargs['condition_filter'] == ['new']
