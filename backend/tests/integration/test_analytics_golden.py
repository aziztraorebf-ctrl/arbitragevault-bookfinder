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

    def test_high_bsr_book_indicates_slow_sales(self):
        """
        BUSINESS RULE: A book with BSR > 100,000 sells slowly.
        Expected: This is detected as potential slow-moving inventory.

        Real-world context: BSR 150,000 in Books might take weeks/months to sell.
        """
        dead_inventory = AdvancedAnalyticsService.detect_dead_inventory(
            bsr=150000,
            category='books'
        )

        # BSR 150k > threshold 50k for books = dead inventory risk
        assert dead_inventory['is_dead_risk'] == True, \
            f"BSR 150000 should be flagged as dead inventory risk"
        assert dead_inventory['threshold'] == 50000, \
            f"Books threshold should be 50000, got {dead_inventory['threshold']}"

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
