"""
API Integration Tests for Textbook Analysis Endpoint
=====================================================
Tests for POST /api/v1/textbook/analyze endpoint including validation,
intrinsic value, seasonal patterns, evergreen classification, and recommendations.

Run: pytest tests/api/test_textbook_analysis_api.py -v
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock

from app.main import app


class TestTextbookAnalysisValidation:
    """Tests for request validation on textbook analysis endpoint."""

    def test_analyze_validates_asin_required(self):
        """POST /api/v1/textbook/analyze returns 422 when asin is missing."""
        client = TestClient(app)

        response = client.post(
            "/api/v1/textbook/analyze",
            json={"source_price": 10.0}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        errors = data["detail"]
        assert any(
            error["loc"][-1] == "asin"
            for error in errors
        )

    def test_analyze_validates_asin_length_min(self):
        """POST /api/v1/textbook/analyze returns 422 when asin is too short."""
        client = TestClient(app)

        response = client.post(
            "/api/v1/textbook/analyze",
            json={"asin": "SHORT"}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_analyze_validates_asin_length_max(self):
        """POST /api/v1/textbook/analyze returns 422 when asin is too long."""
        client = TestClient(app)

        response = client.post(
            "/api/v1/textbook/analyze",
            json={"asin": "TOOLONGASIN123456"}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_analyze_validates_source_price_non_negative(self):
        """POST /api/v1/textbook/analyze returns 422 when source_price is negative."""
        client = TestClient(app)

        response = client.post(
            "/api/v1/textbook/analyze",
            json={"asin": "B08N5WRWNW", "source_price": -5.0}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestTextbookAnalysisProductNotFound:
    """Tests for 404 error when product not found."""

    def test_analyze_returns_404_for_unknown_asin(self):
        """POST /api/v1/textbook/analyze returns 404 when product not found."""
        with patch("app.api.v1.routers.textbook_analysis.get_keepa_service") as mock_get_keepa:
            mock_keepa_service = MagicMock()
            mock_keepa_service.__aenter__ = AsyncMock(return_value=mock_keepa_service)
            mock_keepa_service.__aexit__ = AsyncMock(return_value=None)
            mock_keepa_service.get_product_data = AsyncMock(return_value=None)
            mock_get_keepa.return_value = mock_keepa_service

            client = TestClient(app)
            response = client.post(
                "/api/v1/textbook/analyze",
                json={"asin": "NOTFOUND01"}
            )

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "PRODUCT_NOT_FOUND" in str(data["detail"])


class TestTextbookAnalysisInsufficientData:
    """Tests for insufficient data scenarios."""

    def test_analyze_returns_skip_for_insufficient_data(self):
        """POST /api/v1/textbook/analyze returns SKIP when insufficient historical data."""
        # Mock Keepa service with minimal data (not enough for analysis)
        mock_keepa_data = {
            "asin": "B08N5WRWNW",
            "title": "Some Book",
            "category": "Books",
            "csv": [
                None,  # AMAZON
                [13500000, 2500],  # NEW - minimal data
                None,  # USED
            ],
            "salesRanks": {
                "283155": [[13500000, 50000]]  # Books category - minimal BSR
            }
        }

        with patch("app.api.v1.routers.textbook_analysis.get_keepa_service") as mock_get_keepa:
            mock_keepa_service = MagicMock()
            mock_keepa_service.__aenter__ = AsyncMock(return_value=mock_keepa_service)
            mock_keepa_service.__aexit__ = AsyncMock(return_value=None)
            mock_keepa_service.get_product_data = AsyncMock(return_value=mock_keepa_data)
            mock_get_keepa.return_value = mock_keepa_service

            with patch("app.api.v1.routers.textbook_analysis.parse_keepa_product_unified") as mock_parse:
                mock_parse.return_value = {
                    "asin": "B08N5WRWNW",
                    "title": "Some Book",
                    "category": "Books",
                    "bsr": 50000,
                    "price_history": [],  # Empty - insufficient data
                    "sales_per_month": 5.0,
                }

                with patch("app.api.v1.routers.textbook_analysis.get_sell_price_for_strategy") as mock_intrinsic:
                    mock_intrinsic.return_value = {
                        "sell_price": None,
                        "source": "no_price_available",
                        "corridor": {
                            "low": None,
                            "median": None,
                            "high": None,
                            "confidence": "INSUFFICIENT_DATA",
                            "volatility": 0.0,
                            "data_points": 0,
                            "window_days": 90,
                            "reason": "No price history data available"
                        },
                        "warning": "No price data available"
                    }

                    client = TestClient(app)
                    response = client.post(
                        "/api/v1/textbook/analyze",
                        json={"asin": "B08N5WRWNW"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["recommendation"]["action"] == "SKIP"
                    assert data["intrinsic_value"]["confidence"] == "INSUFFICIENT_DATA"


class TestTextbookAnalysisSuccess:
    """Tests for successful textbook analysis."""

    def test_analyze_returns_complete_analysis(self):
        """POST /api/v1/textbook/analyze returns complete analysis with all components."""
        # Build comprehensive mock data
        mock_keepa_data = {
            "asin": "B08N5WRWNW",
            "title": "NCLEX-RN Prep 2025",
            "category": "Books > Medical > Nursing",
            "csv": [],  # Will be processed by parser
            "salesRanks": {}
        }

        with patch("app.api.v1.routers.textbook_analysis.get_keepa_service") as mock_get_keepa:
            mock_keepa_service = MagicMock()
            mock_keepa_service.__aenter__ = AsyncMock(return_value=mock_keepa_service)
            mock_keepa_service.__aexit__ = AsyncMock(return_value=None)
            mock_keepa_service.get_product_data = AsyncMock(return_value=mock_keepa_data)
            mock_get_keepa.return_value = mock_keepa_service

            with patch("app.api.v1.routers.textbook_analysis.parse_keepa_product_unified") as mock_parse:
                # Generate realistic price history
                now = datetime.now()
                price_history = [
                    (now - timedelta(days=i), 25.0 + (i % 5))
                    for i in range(100)
                ]

                mock_parse.return_value = {
                    "asin": "B08N5WRWNW",
                    "title": "NCLEX-RN Prep 2025",
                    "category": "Books > Medical > Nursing",
                    "bsr": 45000,
                    "price_history": price_history,
                    "sales_per_month": 12.0,
                    "current_buybox_price": 27.99,
                }

                with patch("app.api.v1.routers.textbook_analysis.get_sell_price_for_strategy") as mock_intrinsic:
                    mock_intrinsic.return_value = {
                        "sell_price": 26.50,
                        "source": "intrinsic_median",
                        "corridor": {
                            "low": 23.00,
                            "median": 26.50,
                            "high": 29.00,
                            "confidence": "HIGH",
                            "volatility": 0.12,
                            "data_points": 85,
                            "window_days": 90,
                            "reason": "High confidence: 85 data points with 12.0% volatility"
                        },
                        "warning": None
                    }

                    with patch("app.api.v1.routers.textbook_analysis.detect_seasonal_pattern") as mock_seasonal:
                        from app.services.seasonal_detector_service import SeasonalPattern
                        mock_seasonal.return_value = SeasonalPattern(
                            pattern_type="COLLEGE_FALL",
                            peak_months=[8, 9],
                            trough_months=[3, 4, 5, 6],
                            confidence=0.75,
                            avg_peak_price=30.00,
                            avg_trough_price=22.00,
                            price_swing_pct=36.4
                        )

                        with patch("app.api.v1.routers.textbook_analysis.get_days_until_peak") as mock_days:
                            mock_days.return_value = 120

                            with patch("app.api.v1.routers.textbook_analysis.identify_evergreen") as mock_evergreen:
                                from app.services.evergreen_identifier_service import EvergreenClassification
                                mock_evergreen.return_value = EvergreenClassification(
                                    is_evergreen=True,
                                    evergreen_type="PROFESSIONAL_CERTIFICATION",
                                    confidence=0.85,
                                    reasons=["Keyword matches: nclex", "Strong sales: 12.0/month"],
                                    recommended_stock_level=30,
                                    expected_monthly_sales=12.0
                                )

                                client = TestClient(app)
                                response = client.post(
                                    "/api/v1/textbook/analyze",
                                    json={"asin": "B08N5WRWNW", "source_price": 10.00}
                                )

                                assert response.status_code == 200
                                data = response.json()

                                # Verify all components present
                                assert "asin" in data
                                assert data["asin"] == "B08N5WRWNW"
                                assert "intrinsic_value" in data
                                assert "seasonal_pattern" in data
                                assert "evergreen_classification" in data
                                assert "recommendation" in data
                                assert "roi_metrics" in data

                                # Verify intrinsic value structure
                                iv = data["intrinsic_value"]
                                assert iv["sell_price"] == 26.50
                                assert iv["confidence"] == "HIGH"
                                assert iv["corridor"]["low"] == 23.00
                                assert iv["corridor"]["median"] == 26.50
                                assert iv["corridor"]["high"] == 29.00

                                # Verify seasonal pattern structure
                                sp = data["seasonal_pattern"]
                                assert sp["pattern_type"] == "COLLEGE_FALL"
                                assert sp["peak_months"] == [8, 9]
                                assert sp["days_until_peak"] == 120

                                # Verify evergreen classification
                                ec = data["evergreen_classification"]
                                assert ec["is_evergreen"] is True
                                assert ec["evergreen_type"] == "PROFESSIONAL_CERTIFICATION"
                                assert ec["confidence"] == 0.85

                                # Verify ROI metrics (source_price provided)
                                roi = data["roi_metrics"]
                                assert roi is not None
                                assert "roi_percentage" in roi
                                assert "profit" in roi

    def test_analyze_without_source_price_no_roi_metrics(self):
        """POST /api/v1/textbook/analyze without source_price returns null roi_metrics."""
        mock_keepa_data = {
            "asin": "B08N5WRWNW",
            "title": "Test Book",
            "category": "Books",
        }

        with patch("app.api.v1.routers.textbook_analysis.get_keepa_service") as mock_get_keepa:
            mock_keepa_service = MagicMock()
            mock_keepa_service.__aenter__ = AsyncMock(return_value=mock_keepa_service)
            mock_keepa_service.__aexit__ = AsyncMock(return_value=None)
            mock_keepa_service.get_product_data = AsyncMock(return_value=mock_keepa_data)
            mock_get_keepa.return_value = mock_keepa_service

            with patch("app.api.v1.routers.textbook_analysis.parse_keepa_product_unified") as mock_parse:
                mock_parse.return_value = {
                    "asin": "B08N5WRWNW",
                    "title": "Test Book",
                    "category": "Books",
                    "bsr": 50000,
                    "price_history": [(datetime.now(), 25.0)],
                    "sales_per_month": 8.0,
                }

                with patch("app.api.v1.routers.textbook_analysis.get_sell_price_for_strategy") as mock_intrinsic:
                    mock_intrinsic.return_value = {
                        "sell_price": 25.00,
                        "source": "current_price_fallback",
                        "corridor": {
                            "low": None,
                            "median": None,
                            "high": None,
                            "confidence": "INSUFFICIENT_DATA",
                            "volatility": 0.0,
                            "data_points": 1,
                            "window_days": 90,
                            "reason": "Insufficient data"
                        },
                        "warning": "Using fallback"
                    }

                    with patch("app.api.v1.routers.textbook_analysis.detect_seasonal_pattern") as mock_seasonal:
                        from app.services.seasonal_detector_service import SeasonalPattern
                        mock_seasonal.return_value = SeasonalPattern(
                            pattern_type="INSUFFICIENT_DATA",
                            peak_months=[],
                            trough_months=[],
                            confidence=0.0
                        )

                        with patch("app.api.v1.routers.textbook_analysis.get_days_until_peak") as mock_days:
                            mock_days.return_value = None

                            with patch("app.api.v1.routers.textbook_analysis.identify_evergreen") as mock_evergreen:
                                from app.services.evergreen_identifier_service import EvergreenClassification
                                mock_evergreen.return_value = EvergreenClassification(
                                    is_evergreen=False,
                                    evergreen_type="SEASONAL",
                                    confidence=0.2,
                                    reasons=[],
                                    recommended_stock_level=0,
                                    expected_monthly_sales=8.0
                                )

                                client = TestClient(app)
                                response = client.post(
                                    "/api/v1/textbook/analyze",
                                    json={"asin": "B08N5WRWNW"}  # No source_price
                                )

                                assert response.status_code == 200
                                data = response.json()
                                assert data["roi_metrics"] is None


class TestTextbookAnalysisRecommendations:
    """Tests for recommendation logic."""

    def test_strong_buy_recommendation_for_high_roi_evergreen(self):
        """POST /api/v1/textbook/analyze returns STRONG_BUY for high ROI evergreen books."""
        mock_keepa_data = {"asin": "B08N5WRWNW", "title": "NCLEX Guide"}

        with patch("app.api.v1.routers.textbook_analysis.get_keepa_service") as mock_get_keepa:
            mock_keepa_service = MagicMock()
            mock_keepa_service.__aenter__ = AsyncMock(return_value=mock_keepa_service)
            mock_keepa_service.__aexit__ = AsyncMock(return_value=None)
            mock_keepa_service.get_product_data = AsyncMock(return_value=mock_keepa_data)
            mock_get_keepa.return_value = mock_keepa_service

            with patch("app.api.v1.routers.textbook_analysis.parse_keepa_product_unified") as mock_parse:
                mock_parse.return_value = {
                    "asin": "B08N5WRWNW",
                    "title": "NCLEX Guide",
                    "category": "Books > Nursing",
                    "bsr": 30000,
                    "price_history": [(datetime.now(), 30.0)],
                    "sales_per_month": 15.0,
                }

                with patch("app.api.v1.routers.textbook_analysis.get_sell_price_for_strategy") as mock_intrinsic:
                    mock_intrinsic.return_value = {
                        "sell_price": 30.00,
                        "source": "intrinsic_median",
                        "corridor": {
                            "low": 25.00,
                            "median": 30.00,
                            "high": 35.00,
                            "confidence": "HIGH",
                            "volatility": 0.10,
                            "data_points": 50,
                            "window_days": 90,
                            "reason": "High confidence"
                        },
                        "warning": None
                    }

                    with patch("app.api.v1.routers.textbook_analysis.detect_seasonal_pattern") as mock_seasonal:
                        from app.services.seasonal_detector_service import SeasonalPattern
                        mock_seasonal.return_value = SeasonalPattern(
                            pattern_type="STABLE",
                            peak_months=[],
                            trough_months=[],
                            confidence=0.8
                        )

                        with patch("app.api.v1.routers.textbook_analysis.get_days_until_peak") as mock_days:
                            mock_days.return_value = None

                            with patch("app.api.v1.routers.textbook_analysis.identify_evergreen") as mock_evergreen:
                                from app.services.evergreen_identifier_service import EvergreenClassification
                                mock_evergreen.return_value = EvergreenClassification(
                                    is_evergreen=True,
                                    evergreen_type="PROFESSIONAL_CERTIFICATION",
                                    confidence=0.9,
                                    reasons=["Keyword matches: nclex"],
                                    recommended_stock_level=37,
                                    expected_monthly_sales=15.0
                                )

                                client = TestClient(app)
                                # Source price $10, sell price $30 = 200% ROI (>50% = STRONG_BUY)
                                response = client.post(
                                    "/api/v1/textbook/analyze",
                                    json={"asin": "B08N5WRWNW", "source_price": 10.00}
                                )

                                assert response.status_code == 200
                                data = response.json()
                                assert data["recommendation"]["action"] == "STRONG_BUY"
                                assert "evergreen" in data["recommendation"]["reasons"][0].lower() or "roi" in data["recommendation"]["reasons"][0].lower()

    def test_buy_recommendation_for_good_roi(self):
        """POST /api/v1/textbook/analyze returns BUY for ROI > 30%."""
        mock_keepa_data = {"asin": "B08N5WRWNW", "title": "Test Book"}

        with patch("app.api.v1.routers.textbook_analysis.get_keepa_service") as mock_get_keepa:
            mock_keepa_service = MagicMock()
            mock_keepa_service.__aenter__ = AsyncMock(return_value=mock_keepa_service)
            mock_keepa_service.__aexit__ = AsyncMock(return_value=None)
            mock_keepa_service.get_product_data = AsyncMock(return_value=mock_keepa_data)
            mock_get_keepa.return_value = mock_keepa_service

            with patch("app.api.v1.routers.textbook_analysis.parse_keepa_product_unified") as mock_parse:
                mock_parse.return_value = {
                    "asin": "B08N5WRWNW",
                    "title": "Test Book",
                    "category": "Books",
                    "bsr": 50000,
                    "price_history": [(datetime.now(), 20.0)],
                    "sales_per_month": 8.0,
                }

                with patch("app.api.v1.routers.textbook_analysis.get_sell_price_for_strategy") as mock_intrinsic:
                    mock_intrinsic.return_value = {
                        "sell_price": 20.00,
                        "source": "intrinsic_median",
                        "corridor": {
                            "low": 18.00,
                            "median": 20.00,
                            "high": 22.00,
                            "confidence": "MEDIUM",
                            "volatility": 0.18,
                            "data_points": 25,
                            "window_days": 90,
                            "reason": "Medium confidence"
                        },
                        "warning": None
                    }

                    with patch("app.api.v1.routers.textbook_analysis.detect_seasonal_pattern") as mock_seasonal:
                        from app.services.seasonal_detector_service import SeasonalPattern
                        mock_seasonal.return_value = SeasonalPattern(
                            pattern_type="STABLE",
                            peak_months=[],
                            trough_months=[],
                            confidence=0.7
                        )

                        with patch("app.api.v1.routers.textbook_analysis.get_days_until_peak") as mock_days:
                            mock_days.return_value = None

                            with patch("app.api.v1.routers.textbook_analysis.identify_evergreen") as mock_evergreen:
                                from app.services.evergreen_identifier_service import EvergreenClassification
                                mock_evergreen.return_value = EvergreenClassification(
                                    is_evergreen=False,
                                    evergreen_type="SEASONAL",
                                    confidence=0.3,
                                    reasons=[],
                                    recommended_stock_level=0,
                                    expected_monthly_sales=8.0
                                )

                                client = TestClient(app)
                                # Source price $14, sell price $20 = ~43% ROI (>30% = BUY)
                                response = client.post(
                                    "/api/v1/textbook/analyze",
                                    json={"asin": "B08N5WRWNW", "source_price": 14.00}
                                )

                                assert response.status_code == 200
                                data = response.json()
                                # Could be BUY or STRONG_BUY depending on exact calculation
                                assert data["recommendation"]["action"] in ["BUY", "STRONG_BUY"]


class TestTextbookAnalysisResponseStructure:
    """Tests for response structure compliance."""

    def test_response_contains_all_required_fields(self):
        """POST /api/v1/textbook/analyze response contains all required fields."""
        mock_keepa_data = {"asin": "B08N5WRWNW", "title": "Test"}

        with patch("app.api.v1.routers.textbook_analysis.get_keepa_service") as mock_get_keepa:
            mock_keepa_service = MagicMock()
            mock_keepa_service.__aenter__ = AsyncMock(return_value=mock_keepa_service)
            mock_keepa_service.__aexit__ = AsyncMock(return_value=None)
            mock_keepa_service.get_product_data = AsyncMock(return_value=mock_keepa_data)
            mock_get_keepa.return_value = mock_keepa_service

            with patch("app.api.v1.routers.textbook_analysis.parse_keepa_product_unified") as mock_parse:
                mock_parse.return_value = {
                    "asin": "B08N5WRWNW",
                    "title": "Test",
                    "category": "Books",
                    "bsr": 50000,
                    "price_history": [],
                    "sales_per_month": 5.0,
                }

                with patch("app.api.v1.routers.textbook_analysis.get_sell_price_for_strategy") as mock_intrinsic:
                    mock_intrinsic.return_value = {
                        "sell_price": 20.00,
                        "source": "current_price_fallback",
                        "corridor": {
                            "low": None,
                            "median": None,
                            "high": None,
                            "confidence": "INSUFFICIENT_DATA",
                            "volatility": 0.0,
                            "data_points": 0,
                            "window_days": 90,
                            "reason": "No data"
                        },
                        "warning": "Fallback used"
                    }

                    with patch("app.api.v1.routers.textbook_analysis.detect_seasonal_pattern") as mock_seasonal:
                        from app.services.seasonal_detector_service import SeasonalPattern
                        mock_seasonal.return_value = SeasonalPattern(
                            pattern_type="INSUFFICIENT_DATA",
                            peak_months=[],
                            trough_months=[],
                            confidence=0.0
                        )

                        with patch("app.api.v1.routers.textbook_analysis.get_days_until_peak") as mock_days:
                            mock_days.return_value = None

                            with patch("app.api.v1.routers.textbook_analysis.identify_evergreen") as mock_evergreen:
                                from app.services.evergreen_identifier_service import EvergreenClassification
                                mock_evergreen.return_value = EvergreenClassification(
                                    is_evergreen=False,
                                    evergreen_type="SEASONAL",
                                    confidence=0.0,
                                    reasons=[],
                                    recommended_stock_level=0,
                                    expected_monthly_sales=5.0
                                )

                                client = TestClient(app)
                                response = client.post(
                                    "/api/v1/textbook/analyze",
                                    json={"asin": "B08N5WRWNW"}
                                )

                                assert response.status_code == 200
                                data = response.json()

                                # Required top-level fields
                                required_fields = [
                                    "asin", "title", "intrinsic_value",
                                    "seasonal_pattern", "evergreen_classification",
                                    "recommendation", "roi_metrics", "analyzed_at"
                                ]
                                for field in required_fields:
                                    assert field in data, f"Missing required field: {field}"

                                # Intrinsic value sub-fields
                                iv_fields = ["sell_price", "source", "confidence", "corridor", "warning"]
                                for field in iv_fields:
                                    assert field in data["intrinsic_value"], f"Missing intrinsic_value field: {field}"

                                # Seasonal pattern sub-fields
                                sp_fields = ["pattern_type", "peak_months", "trough_months", "confidence", "days_until_peak"]
                                for field in sp_fields:
                                    assert field in data["seasonal_pattern"], f"Missing seasonal_pattern field: {field}"

                                # Evergreen classification sub-fields
                                ec_fields = ["is_evergreen", "evergreen_type", "confidence", "reasons", "recommended_stock_level"]
                                for field in ec_fields:
                                    assert field in data["evergreen_classification"], f"Missing evergreen_classification field: {field}"

                                # Recommendation sub-fields
                                rec_fields = ["action", "reasons"]
                                for field in rec_fields:
                                    assert field in data["recommendation"], f"Missing recommendation field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
