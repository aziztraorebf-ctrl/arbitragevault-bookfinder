"""
Golden tests for Phase 8 Analytics.
These tests use realistic values to validate business logic correctness.
"""
import pytest
from decimal import Decimal

from app.services.advanced_analytics_service import AdvancedAnalyticsService
from app.services.recommendation_engine_service import RecommendationEngineService


class TestAnalyticsGolden:
    """Golden tests with realistic book arbitrage scenarios."""

    def test_low_bsr_book_high_velocity(self):
        """
        BUSINESS RULE: A book with BSR < 10,000 sells quickly.
        Expected: velocity_score >= 80 (good velocity)

        Real-world context: BSR 5000 in Books means roughly top 0.01% of sales,
        typically sells within days.
        """
        result = AdvancedAnalyticsService.calculate_velocity_intelligence(
            bsr=5000,
            bsr_history=[],
            category='books'
        )

        assert result['velocity_score'] >= 80, \
            f"BSR 5000 should have velocity >= 80, got {result['velocity_score']}"
        assert result['risk_level'] == 'LOW', \
            f"BSR 5000 should be LOW risk, got {result['risk_level']}"

    def test_high_bsr_book_with_real_sales_data(self):
        """
        BUSINESS RULE: Use REAL Keepa salesDrops data, not arbitrary BSR thresholds.

        REFACTORED: Old test used detect_dead_inventory with arbitrary BSR thresholds.
        Real data shows BSR 150,000 can still have 15+ sales/month (NOT dead inventory).

        New test validates that velocity scoring uses the SalesVelocityService
        which bases risk on actual salesDrops data.
        """
        # Import the new function
        from app.api.v1.endpoints.analytics import _calculate_slow_velocity_risk

        # With real salesDrops data showing 10 sales/month
        result = _calculate_slow_velocity_risk(
            sales_drops_30=10,
            bsr=150000,
            category='books'
        )

        # 10 sales/month = LOW tier = 60 risk (not 90+ like old dead inventory)
        assert result['velocity_tier'] == 'LOW', \
            f"10 sales/month should be LOW tier, got {result['velocity_tier']}"
        assert result['monthly_sales_estimate'] >= 10, \
            f"Should estimate ~10 sales/month, got {result['monthly_sales_estimate']}"
        assert result['data_source'] == 'KEEPA_REAL', \
            f"Should use real data, got {result['data_source']}"
        # Risk should be moderate, not extreme like old "dead inventory" flag
        assert result['risk_score'] <= 70, \
            f"10 sales/month should not be high risk, got {result['risk_score']}"

    def test_roi_calculation_accuracy(self):
        """
        BUSINESS RULE: ROI must be calculated correctly with all fees.

        Scenario: Buy at $5, Sell at $20
        - Gross profit: $15
        - Referral fee (15%): $3.00
        - FBA fee: $2.50
        - Storage (1 month): $0.87
        - Returns (2%): $0.40
        - Total fees: ~$6.77
        - Net profit: ~$8.23
        - ROI: ~164.6%
        """
        result = AdvancedAnalyticsService.calculate_roi_net(
            estimated_buy_price=Decimal('5.00'),
            estimated_sell_price=Decimal('20.00'),
            referral_fee_percent=Decimal('15'),
            fba_fee=Decimal('2.50'),
            return_rate_percent=Decimal('2'),
            storage_cost_monthly=Decimal('0.87'),
            sale_cycle_days=30
        )

        # Verify gross profit
        assert result['gross_profit'] == 15.0, \
            f"Gross profit should be 15.0, got {result['gross_profit']}"

        # Verify referral fee (15% of $20 = $3)
        assert result['referral_fee'] == 3.0, \
            f"Referral fee should be 3.0, got {result['referral_fee']}"

        # Verify FBA fee
        assert result['fba_fee'] == 2.5, \
            f"FBA fee should be 2.5, got {result['fba_fee']}"

        # Verify net profit is positive and reasonable
        assert result['net_profit'] > 7.0, \
            f"Net profit should be > 7.0, got {result['net_profit']}"
        assert result['net_profit'] < 10.0, \
            f"Net profit should be < 10.0, got {result['net_profit']}"

        # Verify ROI percentage (net_profit / buy_price * 100)
        expected_roi_min = 140
        expected_roi_max = 180
        assert expected_roi_min <= result['roi_percentage'] <= expected_roi_max, \
            f"ROI should be between {expected_roi_min}-{expected_roi_max}%, got {result['roi_percentage']}"
