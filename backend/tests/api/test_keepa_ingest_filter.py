"""Tests for condition_filter in keepa ingest endpoint."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


def _make_mock_keepa_service():
    """Create a mock Keepa service returning test data."""
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
    return mock_service


def _make_mock_config_service(config=None):
    """Create a mock BusinessConfigService."""
    mock_config_service = AsyncMock()
    mock_config_service.get_effective_config = AsyncMock(return_value=config or {
        'roi': {'target_roi_percent': 30},
        'amazon_fee_pct': 15,
    })
    return mock_config_service


def _make_mock_analysis():
    """Create a mock AnalysisResult."""
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
    return mock_analysis


def test_ingest_passes_condition_filter_to_analyze_product():
    """Test that /keepa/ingest passes condition_filter to analyze_product."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.services.keepa_service import get_keepa_service
    from app.services.business_config_service import get_business_config_service

    mock_service = _make_mock_keepa_service()
    mock_config = _make_mock_config_service()

    app.dependency_overrides[get_keepa_service] = lambda: mock_service
    app.dependency_overrides[get_business_config_service] = lambda: mock_config

    try:
        with TestClient(app) as client, \
             patch('app.api.v1.routers.keepa.analyze_product') as mock_analyze:
            mock_analyze.return_value = _make_mock_analysis()

            response = client.post(
                "/api/v1/keepa/ingest",
                json={
                    "identifiers": ["B00TEST123"],
                    "condition_filter": ["new", "very_good", "good"]
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

            mock_analyze.assert_called_once()
            call_kwargs = mock_analyze.call_args.kwargs
            assert 'condition_filter' in call_kwargs, "condition_filter not passed to analyze_product"
            assert call_kwargs['condition_filter'] == ['new', 'very_good', 'good'], \
                f"Expected ['new', 'very_good', 'good'], got {call_kwargs.get('condition_filter')}"
    finally:
        app.dependency_overrides.pop(get_keepa_service, None)
        app.dependency_overrides.pop(get_business_config_service, None)


def test_ingest_without_condition_filter_passes_none():
    """Test that /keepa/ingest passes None when no condition_filter provided (backward compat)."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.services.keepa_service import get_keepa_service
    from app.services.business_config_service import get_business_config_service

    mock_service = _make_mock_keepa_service()
    mock_config = _make_mock_config_service()

    app.dependency_overrides[get_keepa_service] = lambda: mock_service
    app.dependency_overrides[get_business_config_service] = lambda: mock_config

    try:
        with TestClient(app) as client, \
             patch('app.api.v1.routers.keepa.analyze_product') as mock_analyze:
            mock_analyze.return_value = _make_mock_analysis()

            response = client.post(
                "/api/v1/keepa/ingest",
                json={"identifiers": ["B00TEST123"]}
            )

            assert response.status_code == 200

            mock_analyze.assert_called_once()
            call_kwargs = mock_analyze.call_args.kwargs
            assert call_kwargs.get('condition_filter') is None, \
                f"Expected None, got {call_kwargs.get('condition_filter')}"
    finally:
        app.dependency_overrides.pop(get_keepa_service, None)
        app.dependency_overrides.pop(get_business_config_service, None)


def test_ingest_rejects_invalid_condition():
    """Test that /keepa/ingest rejects invalid condition values."""
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/keepa/ingest",
            json={
                "identifiers": ["B00TEST123"],
                "condition_filter": ["new", "invalid_condition"]
            }
        )

        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        error_str = str(data)
        assert "invalid_condition" in error_str.lower() or "condition" in error_str.lower()


def test_ingest_accepts_single_condition():
    """Test that /keepa/ingest accepts a single condition filter."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.services.keepa_service import get_keepa_service
    from app.services.business_config_service import get_business_config_service

    mock_service = _make_mock_keepa_service()
    mock_config = _make_mock_config_service({})

    app.dependency_overrides[get_keepa_service] = lambda: mock_service
    app.dependency_overrides[get_business_config_service] = lambda: mock_config

    try:
        with TestClient(app) as client, \
             patch('app.api.v1.routers.keepa.analyze_product') as mock_analyze:
            mock_analyze.return_value = _make_mock_analysis()

            response = client.post(
                "/api/v1/keepa/ingest",
                json={
                    "identifiers": ["B00TEST123"],
                    "condition_filter": ["new"]
                }
            )

            assert response.status_code == 200

            call_kwargs = mock_analyze.call_args.kwargs
            assert call_kwargs['condition_filter'] == ['new']
    finally:
        app.dependency_overrides.pop(get_keepa_service, None)
        app.dependency_overrides.pop(get_business_config_service, None)
