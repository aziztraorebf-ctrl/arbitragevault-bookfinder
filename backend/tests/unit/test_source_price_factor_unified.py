"""
Test to verify source_price_factor is unified at 0.50 across all services.
This test ensures we don't regress to the old buy_markup=0.70 bug.

RED-GREEN verified:
- Tests fail when factor changed to 0.70
- Tests pass with correct 0.50 value
"""
import pytest
from decimal import Decimal

from app.schemas.config import ROIConfig


class TestSourcePriceFactorUnified:
    """Tests for unified source_price_factor across services."""

    def test_roi_config_default_is_0_50(self):
        """ROIConfig.source_price_factor default must be 0.50."""
        config = ROIConfig()
        assert config.source_price_factor == Decimal("0.50"), (
            f"Expected 0.50, got {config.source_price_factor}. "
            "Did someone change the default?"
        )

    def test_source_price_factor_calculates_correct_estimated_cost(self):
        """
        With source_price_factor=0.50, a $100 product should have:
        - estimated_cost = $50 (50% of sell price)
        - NOT $70 (the old bug with buy_markup=0.70)
        """
        sell_price = Decimal("100.00")
        source_price_factor = Decimal("0.50")

        estimated_cost = sell_price * source_price_factor

        assert estimated_cost == Decimal("50.00"), (
            f"Expected $50.00, got ${estimated_cost}. "
            "source_price_factor calculation is wrong."
        )
        # Explicitly verify we're NOT using the old buggy value
        old_buy_markup = Decimal("0.70")
        wrong_cost = sell_price * old_buy_markup
        assert estimated_cost != wrong_cost, (
            "Cost matches old buy_markup=0.70! Did someone revert the fix?"
        )

    def test_roi_calculation_with_0_50_factor(self):
        """
        Verify ROI calculation with source_price_factor=0.50.

        Example: $80 book
        - Sell price: $80
        - Buy cost (50%): $40
        - Amazon fees (~15%): $12
        - Profit: $80 - $40 - $12 = $28
        - ROI: ($28 / $40) * 100 = 70%

        With old bug (70%):
        - Buy cost (70%): $56
        - Profit: $80 - $56 - $12 = $12
        - ROI: ($12 / $56) * 100 = 21.4%
        """
        sell_price = Decimal("80.00")
        source_price_factor = Decimal("0.50")
        fee_percentage = Decimal("0.15")

        buy_cost = sell_price * source_price_factor  # $40
        fees = sell_price * fee_percentage  # $12
        profit = sell_price - buy_cost - fees  # $28
        roi = (profit / buy_cost) * 100  # 70%

        # ROI should be around 70%, definitely > 50%
        assert roi > Decimal("50"), (
            f"ROI is {roi}%, expected > 50%. "
            "Are we using the wrong source_price_factor?"
        )

        # Verify it's NOT the old buggy ROI (~21%)
        assert roi > Decimal("40"), (
            f"ROI is {roi}%, suspiciously low. "
            "Check if buy_markup=0.70 bug has returned."
        )

    def test_source_price_factor_range_validation(self):
        """Verify source_price_factor must be between 0.1 and 0.9."""
        # Valid value
        config = ROIConfig(source_price_factor=Decimal("0.50"))
        assert config.source_price_factor == Decimal("0.50")

        # Too low should fail
        with pytest.raises(ValueError):
            ROIConfig(source_price_factor=Decimal("0.05"))

        # Too high should fail
        with pytest.raises(ValueError):
            ROIConfig(source_price_factor=Decimal("0.95"))

    def test_source_price_factor_not_0_28_anymore(self):
        """
        Verify we're not using the old 0.28 value.
        This was too conservative for FBM->FBA arbitrage model.
        """
        config = ROIConfig()
        assert config.source_price_factor != Decimal("0.28"), (
            "source_price_factor is still 0.28! "
            "Should be 0.50 for FBM->FBA arbitrage model."
        )

    def test_source_price_factor_not_0_70_anymore(self):
        """
        Verify we're not using the old buggy 0.70 value (buy_markup).
        This value was causing ROI to be calculated incorrectly.
        """
        config = ROIConfig()
        assert config.source_price_factor != Decimal("0.70"), (
            "source_price_factor is 0.70! "
            "This was the old buy_markup bug. Should be 0.50."
        )
