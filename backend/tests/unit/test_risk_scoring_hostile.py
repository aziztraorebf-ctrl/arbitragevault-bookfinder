"""
Hostile tests for RiskScoringService - Phase 8 Audit
Testing edge cases, component isolation, boundary values.
"""
import pytest
from typing import Dict, Any

from app.services.risk_scoring_service import RiskScoringService


class TestRiskScoreHostile:
    """Test calculate_risk_score with hostile inputs."""

    def test_all_none_inputs_no_crash(self):
        """All optional params as None should not crash."""
        result = RiskScoringService.calculate_risk_score(
            bsr=None,
            category='books',
            seller_count=None,
            amazon_on_listing=None,
            price_stability_data={'stability_score': 50},
            dead_inventory_data={'is_dead_risk': False, 'risk_score': 0}
        )
        assert 'total_risk_score' in result
        assert 'risk_level' in result
        assert result['total_risk_score'] >= 0
        assert result['total_risk_score'] <= 100

    def test_empty_price_stability_data(self):
        """Empty price stability dict should use default 50."""
        result = RiskScoringService.calculate_risk_score(
            bsr=10000,
            category='books',
            seller_count=5,
            amazon_on_listing=False,
            price_stability_data={},
            dead_inventory_data={'is_dead_risk': False, 'risk_score': 0}
        )
        assert result['components']['price_stability']['score'] == 50

    def test_empty_dead_inventory_data(self):
        """Empty dead inventory dict should not crash."""
        result = RiskScoringService.calculate_risk_score(
            bsr=10000,
            category='books',
            seller_count=5,
            amazon_on_listing=False,
            price_stability_data={'stability_score': 80},
            dead_inventory_data={}
        )
        assert result['components']['dead_inventory']['score'] == 0

    def test_unknown_category_uses_default(self):
        """Unknown category should use default risk factor 50."""
        result = RiskScoringService.calculate_risk_score(
            bsr=10000,
            category='some_weird_unknown_category',
            seller_count=5,
            amazon_on_listing=False,
            price_stability_data={'stability_score': 50},
            dead_inventory_data={'is_dead_risk': False, 'risk_score': 0}
        )
        assert result['components']['category']['score'] == 50

    def test_amazon_presence_true_high_risk(self):
        """Amazon on listing should give 95 risk for amazon_presence."""
        result = RiskScoringService.calculate_risk_score(
            bsr=10000,
            category='books',
            seller_count=5,
            amazon_on_listing=True,
            price_stability_data={'stability_score': 80},
            dead_inventory_data={'is_dead_risk': False, 'risk_score': 0}
        )
        assert result['components']['amazon_presence']['score'] == 95

    def test_amazon_presence_false_low_risk(self):
        """No Amazon should give 5 risk for amazon_presence."""
        result = RiskScoringService.calculate_risk_score(
            bsr=10000,
            category='books',
            seller_count=5,
            amazon_on_listing=False,
            price_stability_data={'stability_score': 80},
            dead_inventory_data={'is_dead_risk': False, 'risk_score': 0}
        )
        assert result['components']['amazon_presence']['score'] == 5

    def test_extreme_seller_count_capped(self):
        """Extreme seller count should be capped at 100."""
        result = RiskScoringService.calculate_risk_score(
            bsr=10000,
            category='books',
            seller_count=99999,
            amazon_on_listing=False,
            price_stability_data={'stability_score': 80},
            dead_inventory_data={'is_dead_risk': False, 'risk_score': 0}
        )
        assert result['components']['competition']['score'] <= 100


class TestRiskRecommendationsHostile:
    """Test get_risk_recommendations edge cases."""

    def test_boundary_critical_75(self):
        """Score 75 should give CRITICAL recommendation."""
        result = RiskScoringService.get_risk_recommendations(75.0, 'CRITICAL')
        assert 'HIGH RISK' in result
