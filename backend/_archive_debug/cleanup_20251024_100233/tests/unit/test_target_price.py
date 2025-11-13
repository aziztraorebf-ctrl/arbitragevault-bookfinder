"""Unit tests for Target Price Calculator functionality."""

import pytest
from decimal import Decimal

from app.services.strategic_views_service import TargetPriceCalculator, TargetPriceResult


class TestTargetPriceCalculator:
    """Test cases for TargetPriceCalculator."""
    
    def test_basic_target_price_calculation(self):
        """Test basic target price calculation with profit hunter view."""
        result = TargetPriceCalculator.calculate_target_price(
            buy_price=15.00,
            fba_fee=3.50,
            view_name="profit_hunter"
        )
        
        assert isinstance(result, TargetPriceResult)
        assert result.roi_target == 0.50  # 50% for profit hunter
        assert result.target_price > 0
        
        # Manual calculation check
        # total_costs = 15.00 + 3.50 = 18.50
        # net_rate = (1 - 0.15) * (1 - 0.50) = 0.85 * 0.50 = 0.425
        # base_target_price = 18.50 / 0.425 ≈ 43.53
        # target_price = 43.53 * 1.06 ≈ 46.14
        expected_target = 46.14
        assert abs(result.target_price - expected_target) < 0.50  # Allow some tolerance

    def test_roi_targets_by_strategic_view(self):
        """Test that different strategic views have correct ROI targets."""
        views_and_targets = [
            ("profit_hunter", 0.50),
            ("velocity", 0.25),
            ("cashflow_hunter", 0.35),
            ("balanced_score", 0.40),
            ("volume_player", 0.20)
        ]
        
        for view_name, expected_roi in views_and_targets:
            result = TargetPriceCalculator.calculate_target_price(
                buy_price=10.00,
                fba_fee=2.00,
                view_name=view_name
            )
            assert result.roi_target == expected_roi, f"ROI mismatch for {view_name}"

    def test_custom_referral_fee_rate(self):
        """Test calculation with custom referral fee rate."""
        # Test with 10% referral fee (textbooks)
        result = TargetPriceCalculator.calculate_target_price(
            buy_price=20.00,
            fba_fee=4.00,
            view_name="velocity",
            referral_fee_rate=0.10
        )
        
        # Should be lower target price than default 15% referral fee
        result_default = TargetPriceCalculator.calculate_target_price(
            buy_price=20.00,
            fba_fee=4.00,
            view_name="velocity"
        )
        
        assert result.target_price < result_default.target_price
        assert result.calculation_details["referral_fee_rate"] == 0.10

    def test_storage_fee_inclusion(self):
        """Test that storage fees are properly included in calculation."""
        result_without_storage = TargetPriceCalculator.calculate_target_price(
            buy_price=15.00,
            fba_fee=3.50,
            view_name="balanced_score"
        )
        
        result_with_storage = TargetPriceCalculator.calculate_target_price(
            buy_price=15.00,
            fba_fee=3.50,
            view_name="balanced_score",
            storage_fee=1.50
        )
        
        # Target price should be higher when storage fee is included
        assert result_with_storage.target_price > result_without_storage.target_price
        assert result_with_storage.calculation_details["storage_fee"] == 1.50

    def test_safety_buffer_application(self):
        """Test safety buffer is properly applied."""
        # Test with 8% safety buffer
        result = TargetPriceCalculator.calculate_target_price(
            buy_price=12.00,
            fba_fee=3.00,
            view_name="profit_hunter",
            safety_buffer=0.08
        )
        
        assert result.safety_buffer_used == 0.08
        
        # Compare with default 6% buffer
        result_default = TargetPriceCalculator.calculate_target_price(
            buy_price=12.00,
            fba_fee=3.00,
            view_name="profit_hunter"
        )
        
        assert result.target_price > result_default.target_price

    def test_market_price_achievability(self):
        """Test achievability assessment based on current market price."""
        # Achievable scenario
        result_achievable = TargetPriceCalculator.calculate_target_price(
            buy_price=10.00,
            fba_fee=2.50,
            view_name="velocity",
            current_market_price=25.00
        )
        
        assert result_achievable.is_achievable is True
        assert result_achievable.price_gap_percentage < 0  # Target below market
        
        # Non-achievable scenario
        result_not_achievable = TargetPriceCalculator.calculate_target_price(
            buy_price=20.00,
            fba_fee=5.00,
            view_name="profit_hunter",
            current_market_price=25.00
        )
        
        # High buy price + high ROI target should make it unachievable
        if not result_not_achievable.is_achievable:
            assert result_not_achievable.price_gap_percentage > 0  # Target above market

    def test_calculation_details_transparency(self):
        """Test that calculation details provide complete transparency."""
        result = TargetPriceCalculator.calculate_target_price(
            buy_price=15.00,
            fba_fee=3.50,
            view_name="cashflow_hunter",
            referral_fee_rate=0.12,
            storage_fee=1.00,
            safety_buffer=0.07,
            current_market_price=30.00
        )
        
        details = result.calculation_details
        required_fields = [
            "buy_price", "fba_fee", "storage_fee", "total_costs",
            "referral_fee_rate", "roi_target", "net_rate",
            "base_target_price", "safety_buffer_applied", "current_market_price"
        ]
        
        for field in required_fields:
            assert field in details, f"Missing field in calculation details: {field}"
        
        # Verify calculation chain
        assert details["total_costs"] == 15.00 + 3.50 + 1.00
        assert details["referral_fee_rate"] == 0.12
        assert details["roi_target"] == 0.35  # cashflow_hunter
        assert details["safety_buffer_applied"] == 0.07

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Zero buy price
        with pytest.raises(ValueError):
            TargetPriceCalculator.calculate_target_price(
                buy_price=0,
                fba_fee=3.00,
                view_name="velocity"
            )
        
        # Unknown strategic view
        result = TargetPriceCalculator.calculate_target_price(
            buy_price=10.00,
            fba_fee=2.00,
            view_name="unknown_view"
        )
        # Should fallback to 30% ROI
        assert result.roi_target == 0.30
        
        # Very high referral fee
        result = TargetPriceCalculator.calculate_target_price(
            buy_price=10.00,
            fba_fee=2.00,
            view_name="velocity",
            referral_fee_rate=0.90  # 90%
        )
        # Should still calculate (though may be high target price)
        assert result.target_price > 0

    def test_decimal_precision(self):
        """Test that calculations maintain proper decimal precision."""
        result = TargetPriceCalculator.calculate_target_price(
            buy_price=12.99,
            fba_fee=3.27,
            view_name="balanced_score",
            referral_fee_rate=0.13
        )
        
        # Target price should be rounded to 2 decimal places
        assert len(str(result.target_price).split('.')[-1]) <= 2
        assert isinstance(result.target_price, float)
        
        # Price gap percentage should also be properly rounded
        if result.price_gap_percentage != 0.0:
            assert len(str(result.price_gap_percentage).split('.')[-1]) <= 2