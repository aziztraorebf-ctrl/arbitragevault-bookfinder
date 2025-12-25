"""
Coherence tests for Phase 8 Analytics services.
Ensures services work together logically and don't produce absurd recommendations.
"""
import pytest
from decimal import Decimal

from app.services.advanced_analytics_service import AdvancedAnalyticsService
from app.services.risk_scoring_service import RiskScoringService
from app.services.recommendation_engine_service import RecommendationEngineService


class TestAnalyticsCoherence:
    """Test that analytics services produce coherent results when combined."""

    def test_high_risk_cannot_be_strong_buy(self):
        """A product with risk_score > 70 should NEVER be STRONG_BUY."""
        price_stability = {'stability_score': 20}
        dead_inventory = {'is_dead_risk': True, 'risk_score': 80}

        risk_data = RiskScoringService.calculate_risk_score(
            bsr=200000,
            category='books',
            seller_count=50,
            amazon_on_listing=True,
            price_stability_data=price_stability,
            dead_inventory_data=dead_inventory
        )

        recommendation = RecommendationEngineService.generate_recommendation(
            asin='COHERENCE_TEST_1',
            title='High Risk Test',
            roi_net=50.0,
            velocity_score=80.0,
            risk_score=risk_data['total_risk_score'],
            price_stability_score=20.0,
            amazon_on_listing=True,
            amazon_has_buybox=False,
            estimated_sell_price=30.0,
            estimated_buy_price=10.0
        )

        assert recommendation['recommendation'] != 'STRONG_BUY', \
            f"High risk ({risk_data['total_risk_score']}) should not result in STRONG_BUY"

    def test_low_velocity_low_roi_gives_skip(self):
        """Very poor metrics should result in SKIP or AVOID."""
        velocity_data = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=500000,
            bsr_history=[],
            category='books'
        )

        roi_data = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('15.00'),
            estimated_sell_price=Decimal('16.00'),
        )

        recommendation = RecommendationEngineService.generate_recommendation(
            asin='COHERENCE_TEST_2',
            title='Poor Metrics Test',
            roi_net=roi_data['roi_percentage'],
            velocity_score=velocity_data['velocity_score'],
            risk_score=60.0,
            price_stability_score=40.0,
            amazon_on_listing=False,
            amazon_has_buybox=False,
            estimated_sell_price=16.0,
            estimated_buy_price=15.0
        )

        assert recommendation['recommendation'] in ['SKIP', 'AVOID', 'WATCH'], \
            f"Poor metrics should give SKIP/AVOID/WATCH, got {recommendation['recommendation']}"

    def test_amazon_buybox_overrides_good_metrics(self):
        """Amazon with BuyBox should force AVOID regardless of other metrics."""
        recommendation = RecommendationEngineService.generate_recommendation(
            asin='COHERENCE_TEST_3',
            title='Amazon BuyBox Override Test',
            roi_net=150.0,
            velocity_score=95.0,
            risk_score=10.0,
            price_stability_score=95.0,
            amazon_on_listing=True,
            amazon_has_buybox=True,
            estimated_sell_price=50.0,
            estimated_buy_price=10.0
        )

        assert recommendation['recommendation'] == 'AVOID', \
            f"Amazon BuyBox should force AVOID, got {recommendation['recommendation']}"

    def test_all_green_metrics_gives_positive_recommendation(self):
        """All positive indicators should result in BUY or STRONG_BUY."""
        velocity_data = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=5000,
            bsr_history=[],
            category='books'
        )

        roi_data = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('5.00'),
            estimated_sell_price=Decimal('25.00'),
        )

        price_stability = AdvancedAnalyticsService.calculate_price_stability_score(
            price_history=[{'price': 25.0}, {'price': 24.5}, {'price': 25.5}]
        )

        dead_inventory = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=5000,
            category='books'
        )

        risk_data = RiskScoringService.calculate_risk_score(
            bsr=5000,
            category='books',
            seller_count=3,
            amazon_on_listing=False,
            price_stability_data=price_stability,
            dead_inventory_data=dead_inventory
        )

        recommendation = RecommendationEngineService.generate_recommendation(
            asin='COHERENCE_TEST_4',
            title='All Green Test',
            roi_net=roi_data['roi_percentage'],
            velocity_score=velocity_data['velocity_score'],
            risk_score=risk_data['total_risk_score'],
            price_stability_score=price_stability['stability_score'],
            amazon_on_listing=False,
            amazon_has_buybox=False,
            estimated_sell_price=25.0,
            estimated_buy_price=5.0,
            seller_count=3,
            breakeven_days=20
        )

        assert recommendation['recommendation'] in ['BUY', 'STRONG_BUY'], \
            f"All green metrics should give BUY/STRONG_BUY, got {recommendation['recommendation']}"
