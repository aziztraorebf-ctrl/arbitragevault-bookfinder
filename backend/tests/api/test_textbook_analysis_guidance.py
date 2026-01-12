"""
API Tests for Textbook Analysis Endpoint - Buying Guidance Feature
===================================================================
Tests for the buying_guidance field in POST /api/v1/textbook/analyze response.

This tests Task 3 of the Textbook UX Simplification plan.

Run: pytest tests/api/test_textbook_analysis_guidance.py -v
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock

from app.main import app


class TestTextbookAnalysisBuyingGuidance:
    """Tests for buying_guidance field in textbook analysis response."""

    def _create_mock_setup(
        self,
        asin: str = "B08N5WRWNW",
        title: str = "Test Textbook",
        sell_price: float = 30.00,
        low_price: float = 25.00,
        high_price: float = 35.00,
        confidence: str = "HIGH",
        bsr: int = 45000,
        sales_per_month: float = 12.0,
    ):
        """Create common mock setup for tests."""
        mock_keepa_data = {
            "asin": asin,
            "title": title,
            "category": "Books > Education",
        }

        mock_parsed_data = {
            "asin": asin,
            "title": title,
            "category": "Books > Education",
            "bsr": bsr,
            "current_bsr": bsr,
            "price_history": [(datetime.now() - timedelta(days=i), sell_price) for i in range(100)],
            "sales_per_month": sales_per_month,
        }

        mock_intrinsic_result = {
            "sell_price": sell_price,
            "source": "intrinsic_median",
            "corridor": {
                "low": low_price,
                "median": sell_price,
                "high": high_price,
                "confidence": confidence,
                "volatility": 0.12,
                "data_points": 85,
                "window_days": 90,
                "reason": f"{confidence} confidence: 85 data points"
            },
            "warning": None
        }

        return mock_keepa_data, mock_parsed_data, mock_intrinsic_result

    def _setup_mocks(
        self,
        mock_get_keepa,
        mock_keepa_data,
        mock_parsed_data,
        mock_intrinsic_result
    ):
        """Set up all the mocks for the test."""
        # Keepa service mock
        mock_keepa_service = MagicMock()
        mock_keepa_service.__aenter__ = AsyncMock(return_value=mock_keepa_service)
        mock_keepa_service.__aexit__ = AsyncMock(return_value=None)
        mock_keepa_service.get_product_data = AsyncMock(return_value=mock_keepa_data)
        mock_get_keepa.return_value = mock_keepa_service

        return mock_keepa_service

    def test_response_includes_buying_guidance_section(self):
        """POST /api/v1/textbook/analyze response includes buying_guidance."""
        mock_keepa_data, mock_parsed_data, mock_intrinsic = self._create_mock_setup()

        with patch("app.api.v1.routers.textbook_analysis.get_keepa_service") as mock_get_keepa:
            self._setup_mocks(mock_get_keepa, mock_keepa_data, mock_parsed_data, mock_intrinsic)

            with patch("app.api.v1.routers.textbook_analysis.parse_keepa_product_unified") as mock_parse:
                mock_parse.return_value = mock_parsed_data

                with patch("app.api.v1.routers.textbook_analysis.get_sell_price_for_strategy") as mock_intrinsic_fn:
                    mock_intrinsic_fn.return_value = mock_intrinsic

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
                                    is_evergreen=False,
                                    evergreen_type="SEASONAL",
                                    confidence=0.5,
                                    reasons=[],
                                    recommended_stock_level=0,
                                    expected_monthly_sales=12.0
                                )

                                client = TestClient(app)
                                response = client.post(
                                    "/api/v1/textbook/analyze",
                                    json={"asin": "B08N5WRWNW", "source_price": 10.00}
                                )

                                assert response.status_code == 200
                                data = response.json()

                                # Main assertion: buying_guidance must be present
                                assert "buying_guidance" in data, "buying_guidance field must be in response"

                                # Verify it's not null/None
                                assert data["buying_guidance"] is not None, "buying_guidance must not be null"

    def test_buying_guidance_has_correct_recommendation(self):
        """POST /api/v1/textbook/analyze returns correct recommendation based on ROI."""
        # Setup: sell_price=$30, source_price=$10
        # Net after fees (22%): $30 * 0.78 = $23.40
        # Profit: $23.40 - $10 = $13.40
        # ROI: 134% -> should be BUY
        mock_keepa_data, mock_parsed_data, mock_intrinsic = self._create_mock_setup(
            sell_price=30.00,
            low_price=25.00,
            high_price=35.00,
            confidence="HIGH"
        )

        with patch("app.api.v1.routers.textbook_analysis.get_keepa_service") as mock_get_keepa:
            self._setup_mocks(mock_get_keepa, mock_keepa_data, mock_parsed_data, mock_intrinsic)

            with patch("app.api.v1.routers.textbook_analysis.parse_keepa_product_unified") as mock_parse:
                mock_parse.return_value = mock_parsed_data

                with patch("app.api.v1.routers.textbook_analysis.get_sell_price_for_strategy") as mock_intrinsic_fn:
                    mock_intrinsic_fn.return_value = mock_intrinsic

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
                                    is_evergreen=False,
                                    evergreen_type="SEASONAL",
                                    confidence=0.5,
                                    reasons=[],
                                    recommended_stock_level=0,
                                    expected_monthly_sales=12.0
                                )

                                client = TestClient(app)
                                response = client.post(
                                    "/api/v1/textbook/analyze",
                                    json={"asin": "B08N5WRWNW", "source_price": 10.00}
                                )

                                assert response.status_code == 200
                                data = response.json()

                                # Main assertion: recommendation should be BUY for high ROI
                                guidance = data["buying_guidance"]
                                assert guidance["recommendation"] == "BUY", \
                                    f"Expected BUY for high ROI, got {guidance['recommendation']}"

                                # ROI should be positive and high
                                assert guidance["estimated_roi_pct"] > 50, \
                                    f"Expected ROI > 50%, got {guidance['estimated_roi_pct']}%"

    def test_buying_guidance_includes_explanations_dict(self):
        """POST /api/v1/textbook/analyze buying_guidance includes explanations dict."""
        mock_keepa_data, mock_parsed_data, mock_intrinsic = self._create_mock_setup()

        with patch("app.api.v1.routers.textbook_analysis.get_keepa_service") as mock_get_keepa:
            self._setup_mocks(mock_get_keepa, mock_keepa_data, mock_parsed_data, mock_intrinsic)

            with patch("app.api.v1.routers.textbook_analysis.parse_keepa_product_unified") as mock_parse:
                mock_parse.return_value = mock_parsed_data

                with patch("app.api.v1.routers.textbook_analysis.get_sell_price_for_strategy") as mock_intrinsic_fn:
                    mock_intrinsic_fn.return_value = mock_intrinsic

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
                                    is_evergreen=False,
                                    evergreen_type="SEASONAL",
                                    confidence=0.5,
                                    reasons=[],
                                    recommended_stock_level=0,
                                    expected_monthly_sales=12.0
                                )

                                client = TestClient(app)
                                response = client.post(
                                    "/api/v1/textbook/analyze",
                                    json={"asin": "B08N5WRWNW", "source_price": 10.00}
                                )

                                assert response.status_code == 200
                                data = response.json()

                                guidance = data["buying_guidance"]

                                # Main assertion: explanations must be a dict
                                assert "explanations" in guidance, "explanations field must be in buying_guidance"
                                assert isinstance(guidance["explanations"], dict), \
                                    "explanations must be a dictionary"

                                # Should have expected keys for tooltips
                                expected_keys = [
                                    "max_buy_price",
                                    "target_sell_price",
                                    "estimated_profit",
                                    "estimated_roi_pct"
                                ]
                                for key in expected_keys:
                                    assert key in guidance["explanations"], \
                                        f"explanations should contain {key}"

    def test_buying_guidance_has_all_required_fields(self):
        """POST /api/v1/textbook/analyze buying_guidance has all required fields."""
        mock_keepa_data, mock_parsed_data, mock_intrinsic = self._create_mock_setup()

        with patch("app.api.v1.routers.textbook_analysis.get_keepa_service") as mock_get_keepa:
            self._setup_mocks(mock_get_keepa, mock_keepa_data, mock_parsed_data, mock_intrinsic)

            with patch("app.api.v1.routers.textbook_analysis.parse_keepa_product_unified") as mock_parse:
                mock_parse.return_value = mock_parsed_data

                with patch("app.api.v1.routers.textbook_analysis.get_sell_price_for_strategy") as mock_intrinsic_fn:
                    mock_intrinsic_fn.return_value = mock_intrinsic

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
                                    is_evergreen=False,
                                    evergreen_type="SEASONAL",
                                    confidence=0.5,
                                    reasons=[],
                                    recommended_stock_level=0,
                                    expected_monthly_sales=12.0
                                )

                                client = TestClient(app)
                                response = client.post(
                                    "/api/v1/textbook/analyze",
                                    json={"asin": "B08N5WRWNW", "source_price": 10.00}
                                )

                                assert response.status_code == 200
                                data = response.json()

                                guidance = data["buying_guidance"]

                                # All required fields from BuyingGuidanceSchema
                                required_fields = [
                                    "max_buy_price",
                                    "target_sell_price",
                                    "estimated_profit",
                                    "estimated_roi_pct",
                                    "price_range",
                                    "estimated_days_to_sell",
                                    "recommendation",
                                    "recommendation_reason",
                                    "confidence_label",
                                    "explanations"
                                ]

                                for field in required_fields:
                                    assert field in guidance, \
                                        f"buying_guidance must contain {field}"

    def test_buying_guidance_skip_for_insufficient_data(self):
        """POST /api/v1/textbook/analyze returns SKIP recommendation for insufficient data."""
        mock_keepa_data = {"asin": "B08N5WRWNW", "title": "Test Book"}
        mock_parsed_data = {
            "asin": "B08N5WRWNW",
            "title": "Test Book",
            "category": "Books",
            "bsr": 50000,
            "price_history": [],  # Empty - insufficient data
            "sales_per_month": 0,
        }
        mock_intrinsic = {
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
                "reason": "No price data"
            },
            "warning": "No data"
        }

        with patch("app.api.v1.routers.textbook_analysis.get_keepa_service") as mock_get_keepa:
            self._setup_mocks(mock_get_keepa, mock_keepa_data, mock_parsed_data, mock_intrinsic)

            with patch("app.api.v1.routers.textbook_analysis.parse_keepa_product_unified") as mock_parse:
                mock_parse.return_value = mock_parsed_data

                with patch("app.api.v1.routers.textbook_analysis.get_sell_price_for_strategy") as mock_intrinsic_fn:
                    mock_intrinsic_fn.return_value = mock_intrinsic

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
                                    expected_monthly_sales=0
                                )

                                client = TestClient(app)
                                response = client.post(
                                    "/api/v1/textbook/analyze",
                                    json={"asin": "B08N5WRWNW", "source_price": 10.00}
                                )

                                assert response.status_code == 200
                                data = response.json()

                                guidance = data["buying_guidance"]
                                assert guidance["recommendation"] == "SKIP", \
                                    "Should recommend SKIP for insufficient data"
                                assert guidance["confidence_label"] == "Donnees insuffisantes", \
                                    "Should show French label for insufficient data"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
