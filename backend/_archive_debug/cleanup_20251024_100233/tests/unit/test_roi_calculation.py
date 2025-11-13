"""
Unit tests for ROI calculation with strategy-based purchase cost.

Tests verify that the inverse ROI formula correctly calculates purchase costs
to guarantee exact ROI percentages for each strategy.
"""

import pytest
from decimal import Decimal
from app.core.calculations import calculate_purchase_cost_from_strategy
from app.core.fees_config import calculate_profit_metrics


class TestPurchaseCostFromStrategy:
    """Test suite for calculate_purchase_cost_from_strategy function."""

    @pytest.fixture
    def mock_config(self):
        """Mock business configuration with strategy definitions."""
        return {
            "strategies": {
                "aggressive": {
                    "roi_min": 40,
                    "velocity_min": 70,
                    "stability_min": 80
                },
                "balanced": {
                    "roi_min": 25,
                    "velocity_min": 80,
                    "stability_min": 60
                },
                "conservative": {
                    "roi_min": 35,
                    "velocity_min": 60,
                    "stability_min": 85
                }
            }
        }

    def test_balanced_strategy_roi_exactness(self, mock_config):
        """
        Test that balanced strategy (25% ROI target) produces exact ROI.

        Given:
            - sell_price = $100
            - strategy = 'balanced' (roi_min: 25%)

        Then:
            - Calculated purchase cost should produce exactly 25% ROI
        """
        sell_price = Decimal("100.00")
        strategy = "balanced"

        # Calculate purchase cost
        purchase_cost = calculate_purchase_cost_from_strategy(
            sell_price=sell_price,
            strategy=strategy,
            config=mock_config
        )

        # Verify purchase cost is reasonable
        assert purchase_cost > 0, "Purchase cost must be positive"
        assert purchase_cost < sell_price, "Purchase cost must be less than sell price"

        # Calculate actual ROI using the same profit metrics function
        metrics = calculate_profit_metrics(
            sell_price=sell_price,
            buy_cost=purchase_cost,
            weight_lbs=Decimal("1.0"),
            category="books",
            buffer_pct=Decimal("5.0")
        )

        actual_roi = metrics["roi_percentage"]
        expected_roi = Decimal("25")

        # Allow 0.1% tolerance for rounding
        assert abs(actual_roi - expected_roi) < Decimal("0.1"), \
            f"ROI should be {expected_roi}%, got {actual_roi}%"

    def test_all_strategies_distinct_purchase_costs(self, mock_config):
        """
        Test that different strategies produce distinct purchase costs.

        Given:
            - Same sell_price for all strategies
            - Different ROI targets (Aggressive: 40%, Balanced: 25%, Conservative: 35%)

        Then:
            - Purchase costs should be ordered: Aggressive < Conservative < Balanced
            - (Lower ROI target allows higher purchase cost)
        """
        sell_price = Decimal("100.00")

        aggressive_cost = calculate_purchase_cost_from_strategy(
            sell_price=sell_price,
            strategy="aggressive",
            config=mock_config
        )

        balanced_cost = calculate_purchase_cost_from_strategy(
            sell_price=sell_price,
            strategy="balanced",
            config=mock_config
        )

        conservative_cost = calculate_purchase_cost_from_strategy(
            sell_price=sell_price,
            strategy="conservative",
            config=mock_config
        )

        # Higher ROI target → lower purchase cost allowed
        # aggressive (40%) < conservative (35%) < balanced (25%)
        assert aggressive_cost < conservative_cost, \
            "Aggressive (40% ROI) should have lower purchase cost than Conservative (35%)"
        assert conservative_cost < balanced_cost, \
            "Conservative (35% ROI) should have lower purchase cost than Balanced (25%)"

        # All should be positive and less than sell price
        assert all(cost > 0 for cost in [aggressive_cost, balanced_cost, conservative_cost]), \
            "All purchase costs must be positive"
        assert all(cost < sell_price for cost in [aggressive_cost, balanced_cost, conservative_cost]), \
            "All purchase costs must be less than sell price"

    def test_edge_cases(self, mock_config):
        """
        Test edge cases: very low prices, very high prices.

        Verifies that function handles extreme values gracefully.
        """
        # Test very low price (e.g., USED item)
        low_price = Decimal("2.30")
        low_cost = calculate_purchase_cost_from_strategy(
            sell_price=low_price,
            strategy="balanced",
            config=mock_config
        )

        # Should fallback to 50% when calculation produces invalid result
        # (because fees + buffer exceed sell price)
        assert low_cost > 0, "Purchase cost must be positive even for low prices"
        assert low_cost <= low_price, "Purchase cost cannot exceed sell price"

        # Test high price
        high_price = Decimal("500.00")
        high_cost = calculate_purchase_cost_from_strategy(
            sell_price=high_price,
            strategy="balanced",
            config=mock_config
        )

        assert high_cost > 0, "Purchase cost must be positive"
        assert high_cost < high_price, "Purchase cost must be less than sell price"

        # Verify realistic ROI on high price
        metrics = calculate_profit_metrics(
            sell_price=high_price,
            buy_cost=high_cost,
            weight_lbs=Decimal("1.0"),
            category="books",
            buffer_pct=Decimal("5.0")
        )

        # Should be close to 25% target
        assert abs(metrics["roi_percentage"] - Decimal("25")) < Decimal("1.0"), \
            "High price should still produce target ROI"

    def test_integration_with_analyze_product_flow(self, mock_config):
        """
        Test E2E integration simulating analyze_product workflow.

        Simulates:
            1. Keepa returns current_price
            2. calculate_purchase_cost_from_strategy calculates buy cost
            3. calculate_profit_metrics calculates ROI
            4. ROI should be positive and match strategy target
        """
        # Simulate Keepa price data
        keepa_current_price = Decimal("45.99")
        strategy = "balanced"

        # Step 1: Calculate purchase cost (replaces buggy line 185)
        purchase_cost = calculate_purchase_cost_from_strategy(
            sell_price=keepa_current_price,
            strategy=strategy,
            config=mock_config
        )

        # Step 2: Calculate ROI metrics (existing flow)
        roi_metrics = calculate_profit_metrics(
            sell_price=keepa_current_price,
            buy_cost=purchase_cost,
            weight_lbs=Decimal("1.0"),
            category="books",
            buffer_pct=Decimal("5.0")
        )

        # Assertions
        roi = roi_metrics["roi_percentage"]
        net_profit = roi_metrics["net_profit"]

        # ROI should be positive (fixing the -7845% bug)
        assert roi > 0, f"ROI must be positive, got {roi}%"

        # ROI should match strategy target (25% for balanced)
        assert abs(roi - Decimal("25")) < Decimal("0.5"), \
            f"ROI should be ~25% for balanced strategy, got {roi}%"

        # Profit should be positive
        assert net_profit > 0, f"Net profit must be positive, got {net_profit}"

        # Purchase cost should be realistic (not too high or too low)
        assert purchase_cost < keepa_current_price * Decimal("0.95"), \
            "Purchase cost should leave room for profit"
        assert purchase_cost > keepa_current_price * Decimal("0.30"), \
            "Purchase cost should be reasonable"


class TestStrategyConfigMissing:
    """Test behavior when strategy config is missing or incomplete."""

    def test_missing_strategy_uses_default(self):
        """Test that missing strategy falls back to default ROI target."""
        config = {"strategies": {}}  # Empty strategies

        sell_price = Decimal("100.00")
        purchase_cost = calculate_purchase_cost_from_strategy(
            sell_price=sell_price,
            strategy="nonexistent",
            config=config
        )

        # Should use default roi_min of 30%
        assert purchase_cost > 0
        assert purchase_cost < sell_price

        # Verify produces ~30% ROI
        metrics = calculate_profit_metrics(
            sell_price=sell_price,
            buy_cost=purchase_cost,
            weight_lbs=Decimal("1.0"),
            category="books"
        )

        assert abs(metrics["roi_percentage"] - Decimal("30")) < Decimal("1.0"), \
            "Should default to 30% ROI target"

    def test_missing_roi_min_uses_default(self):
        """Test that strategy without roi_min uses default."""
        config = {
            "strategies": {
                "incomplete": {
                    "velocity_min": 70
                    # No roi_min
                }
            }
        }

        sell_price = Decimal("100.00")
        purchase_cost = calculate_purchase_cost_from_strategy(
            sell_price=sell_price,
            strategy="incomplete",
            config=config
        )

        # Should use default roi_min of 30%
        assert purchase_cost > 0

        metrics = calculate_profit_metrics(
            sell_price=sell_price,
            buy_cost=purchase_cost,
            weight_lbs=Decimal("1.0"),
            category="books"
        )

        assert abs(metrics["roi_percentage"] - Decimal("30")) < Decimal("1.0")
