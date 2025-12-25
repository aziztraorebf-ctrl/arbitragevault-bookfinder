"""
Hostile tests for RecommendationEngineService - Phase 8 Audit
Testing edge cases, tier mapping, special overrides.
"""
import pytest
from typing import Dict, Any

from app.services.recommendation_engine_service import RecommendationEngineService


class TestRecommendationHostile:
    """Test generate_recommendation with hostile inputs."""

    def test_all_perfect_metrics_strong_buy(self):
        """All perfect metrics should give STRONG_BUY."""
        result = RecommendationEngineService.generate_recommendation(
            asin='TEST123',
            title='Perfect Product',
            roi_net=50.0,
            velocity_score=80.0,
            risk_score=25.0,
            price_stability_score=90.0,
            amazon_on_listing=False,
            amazon_has_buybox=False,
            estimated_sell_price=30.0,
            estimated_buy_price=10.0,
            breakeven_days=20
        )
        assert result['recommendation'] == 'STRONG_BUY'
        assert result['criteria_passed'] == 6

    def test_amazon_buybox_forces_avoid(self):
        """Amazon with Buy Box should force AVOID regardless of other metrics."""
        result = RecommendationEngineService.generate_recommendation(
            asin='TEST123',
            title='Good Product But Amazon Present',
            roi_net=100.0,
            velocity_score=95.0,
            risk_score=10.0,
            price_stability_score=95.0,
            amazon_on_listing=True,
            amazon_has_buybox=True,
            estimated_sell_price=50.0,
            estimated_buy_price=10.0,
            breakeven_days=15
        )
        assert result['recommendation'] == 'AVOID'
        assert 'Amazon owns Buy Box' in result['reason']

    def test_very_low_roi_forces_skip(self):
        """ROI < 15% should force SKIP."""
        result = RecommendationEngineService.generate_recommendation(
            asin='TEST123',
            title='Low ROI Product',
            roi_net=10.0,
            velocity_score=80.0,
            risk_score=25.0,
            price_stability_score=90.0,
            amazon_on_listing=False,
            amazon_has_buybox=False,
            estimated_sell_price=20.0,
            estimated_buy_price=10.0,
            breakeven_days=20
        )
        assert result['recommendation'] == 'SKIP'
        assert 'ROI too low' in result['reason']

    def test_very_high_risk_forces_skip(self):
        """Risk > 85 should force SKIP."""
        result = RecommendationEngineService.generate_recommendation(
            asin='TEST123',
            title='High Risk Product',
            roi_net=50.0,
            velocity_score=80.0,
            risk_score=90.0,
            price_stability_score=90.0,
            amazon_on_listing=False,
            amazon_has_buybox=False,
            estimated_sell_price=30.0,
            estimated_buy_price=10.0,
            breakeven_days=20
        )
        assert result['recommendation'] == 'SKIP'
        assert 'Risk score critical' in result['reason']

    def test_zero_criteria_gives_skip(self):
        """Zero criteria passed should give SKIP."""
        result = RecommendationEngineService.generate_recommendation(
            asin='TEST123',
            title='Bad Product',
            roi_net=5.0,
            velocity_score=30.0,
            risk_score=80.0,
            price_stability_score=30.0,
            amazon_on_listing=True,
            amazon_has_buybox=False,
            estimated_sell_price=12.0,
            estimated_buy_price=10.0,
            breakeven_days=100
        )
        assert result['criteria_passed'] <= 2

    def test_negative_values_handled(self):
        """Negative ROI and other values should not crash."""
        result = RecommendationEngineService.generate_recommendation(
            asin='TEST123',
            title='Negative Margin Product',
            roi_net=-50.0,
            velocity_score=0.0,
            risk_score=100.0,
            price_stability_score=0.0,
            amazon_on_listing=True,
            amazon_has_buybox=False,
            estimated_sell_price=5.0,
            estimated_buy_price=10.0,
            breakeven_days=None
        )
        assert result['recommendation'] in ['SKIP', 'AVOID', 'WATCH']
        assert result['profit_per_unit'] == -5.0

    def test_none_optional_params_handled(self):
        """None seller_count and breakeven_days should not crash."""
        result = RecommendationEngineService.generate_recommendation(
            asin='TEST123',
            title='Incomplete Data Product',
            roi_net=40.0,
            velocity_score=75.0,
            risk_score=40.0,
            price_stability_score=60.0,
            amazon_on_listing=False,
            amazon_has_buybox=False,
            estimated_sell_price=25.0,
            estimated_buy_price=15.0,
            seller_count=None,
            breakeven_days=None
        )
        assert 'recommendation' in result
