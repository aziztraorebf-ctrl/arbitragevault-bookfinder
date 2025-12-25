"""
Hostile tests for AdvancedAnalyticsService - Phase 8 Audit
Testing edge cases, zero values, None inputs, extreme values.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app.services.advanced_analytics_service import AdvancedAnalyticsService


class TestVelocityIntelligenceHostile:
    """Test calculate_velocity_intelligence with hostile inputs."""

    def test_zero_bsr_returns_no_data(self):
        """BSR=0 should return velocity_score=0 and risk_level=NO_DATA."""
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=0, bsr_history=[], category='books'
        )
        assert result['velocity_score'] == 0
        assert result['risk_level'] == 'NO_DATA'

    def test_none_bsr_returns_no_data(self):
        """BSR=None should return velocity_score=0 and risk_level=NO_DATA."""
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=None, bsr_history=[], category='books'
        )
        assert result['velocity_score'] == 0
        assert result['risk_level'] == 'NO_DATA'

    def test_negative_bsr_returns_no_data(self):
        """BSR=-100 should return velocity_score=0 and risk_level=NO_DATA."""
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=-100, bsr_history=[], category='books'
        )
        assert result['velocity_score'] == 0
        assert result['risk_level'] == 'NO_DATA'

    def test_empty_history_uses_current_bsr(self):
        """Empty bsr_history should still work with valid BSR."""
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=10000, bsr_history=[], category='books'
        )
        assert result['velocity_score'] == 100
        assert result['bsr_current'] == 10000
        assert result['risk_level'] == 'LOW'

    def test_unknown_category_defaults_gracefully(self):
        """Unknown category should not crash."""
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=5000, bsr_history=[], category='unknown_weird_category'
        )
        assert result['velocity_score'] >= 0
        assert result['velocity_score'] <= 100

    def test_malformed_history_items_ignored(self):
        """History items with missing bsr should be ignored, not crash."""
        history = [
            {'timestamp': datetime.now(timezone.utc).isoformat()},  # missing bsr
            {},  # empty dict
        ]
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=10000, bsr_history=history, category='books'
        )
        assert result['velocity_score'] == 100
        assert result['trend_7d'] is None  # Not enough valid data


class TestPriceStabilityHostile:
    """Test calculate_price_stability_score with hostile inputs."""

    def test_empty_history_returns_default(self):
        """Empty price history should return stability_score=50."""
        result = AdvancedAnalyticsService.calculate_price_stability_score([])
        assert result['stability_score'] == 50
        assert result['price_volatility'] == 'UNKNOWN'

    def test_single_price_insufficient_data(self):
        """Single price should return UNKNOWN (less than 2 items in history)."""
        result = AdvancedAnalyticsService.calculate_price_stability_score([{'price': 10.0}])
        assert result['stability_score'] == 50
        assert result['price_volatility'] == 'UNKNOWN'

    def test_zero_prices_in_history(self):
        """Zero prices should be filtered out or handled."""
        result = AdvancedAnalyticsService.calculate_price_stability_score([
            {'price': 0},
            {'price': 10.0},
            {'price': 11.0}
        ])
        # Zero should be filtered (falsy), only 10 and 11 used
        assert result['stability_score'] > 0
        assert result['avg_price'] > 0

    def test_none_prices_in_history(self):
        """None prices should be filtered out."""
        result = AdvancedAnalyticsService.calculate_price_stability_score([
            {'price': None},
            {'price': 10.0},
            {'price': 11.0}
        ])
        assert result['avg_price'] == 10.5

    def test_identical_prices_perfect_stability(self):
        """Identical prices should give high stability (low variance)."""
        result = AdvancedAnalyticsService.calculate_price_stability_score([
            {'price': 20.0},
            {'price': 20.0},
            {'price': 20.0}
        ])
        assert result['stability_score'] == 100
        assert result['coefficient_variation'] == 0
        assert result['price_volatility'] == 'LOW'


class TestROINetHostile:
    """Test calculate_roi_net with hostile inputs."""

    def test_zero_buy_price_no_division_error(self):
        """Zero buy price should not cause division by zero."""
        result = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('0'),
            estimated_sell_price=Decimal('10.00')
        )
        assert result['roi_percentage'] == 0
        assert result['gross_profit'] == 10.0

    def test_negative_margin_calculated(self):
        """When sell < buy, profit should be negative."""
        result = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('20.00'),
            estimated_sell_price=Decimal('10.00')
        )
        assert result['net_profit'] < 0
        assert result['roi_percentage'] < 0

    def test_zero_sell_price_handled(self):
        """Zero sell price should not crash."""
        result = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('10.00'),
            estimated_sell_price=Decimal('0')
        )
        assert result['gross_profit'] == -10.0
        assert result['roi_percentage'] < 0

    def test_very_large_prices(self):
        """Very large prices should not overflow."""
        result = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('99999999.99'),
            estimated_sell_price=Decimal('199999999.99')
        )
        assert result['gross_profit'] == 100000000.0
        assert result['roi_percentage'] > 0

    def test_zero_sale_cycle_days(self):
        """Zero sale cycle days should handle storage cost division."""
        result = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('10.00'),
            estimated_sell_price=Decimal('20.00'),
            sale_cycle_days=0
        )
        assert result['storage_cost'] == 0


class TestCompetitionScoreHostile:
    """Test calculate_competition_score with hostile inputs."""

    def test_none_seller_count_unknown(self):
        """None seller count should return UNKNOWN."""
        result = AdvancedAnalyticsService.calculate_competition_score(
            seller_count=None, fba_seller_count=None
        )
        assert result['competition_level'] == 'UNKNOWN'
        assert result['amazon_risk'] == 'UNKNOWN'

    def test_extreme_seller_count(self):
        """Very high seller count should cap score, resulting in MEDIUM level."""
        result = AdvancedAnalyticsService.calculate_competition_score(
            seller_count=10000, fba_seller_count=5000
        )
        assert result['competition_score'] >= 0
        assert result['competition_score'] <= 100
        assert result['competition_level'] in ['MEDIUM', 'HIGH']


class TestDeadInventoryHostile:
    """Test detect_dead_inventory with hostile inputs."""

    def test_none_bsr_no_crash(self):
        """None BSR should not crash and return safe defaults."""
        result = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=None, category='books'
        )
        assert result['is_dead_risk'] == False
        assert result['reason'] == 'NO_BSR_DATA'

    def test_unknown_category_uses_default_threshold(self):
        """Unknown category should use default threshold 100000."""
        result = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=150000, category='some_weird_category'
        )
        assert result['threshold'] == 100000
        assert result['is_dead_risk'] == True
