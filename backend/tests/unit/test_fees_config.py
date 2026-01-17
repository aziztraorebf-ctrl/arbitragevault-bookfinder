"""
Unit tests for fees_config.py

Tests for:
- calculate_fees_from_unified_config wrapper function
- Fee calculation consistency with unified config types
"""

from decimal import Decimal
import pytest


class TestCalculateFeesFromUnifiedConfig:
    """Test fee calculation with unified config type."""

    def test_calculate_fees_basic(self):
        """Test basic fee calculation with unified config."""
        from app.core.fees_config import calculate_fees_from_unified_config
        from app.schemas.config_types import FeeConfigUnified

        config = FeeConfigUnified(
            referral_fee_pct=Decimal("15.0"),
            closing_fee=Decimal("1.80"),
            fba_fee_base=Decimal("2.50"),
            fba_fee_per_lb=Decimal("0.40"),
            inbound_shipping=Decimal("0.40"),
            prep_fee=Decimal("0.20"),
        )

        result = calculate_fees_from_unified_config(
            sell_price=Decimal("25.00"),
            weight_lbs=Decimal("1.0"),
            fee_config=config
        )

        assert "total_fees" in result
        assert "referral_fee" in result
        assert result["referral_fee"] == Decimal("3.75")  # 15% of 25
        assert result["closing_fee"] == Decimal("1.80")

    def test_calculate_fees_returns_all_components(self):
        """Test that all fee components are returned."""
        from app.core.fees_config import calculate_fees_from_unified_config
        from app.schemas.config_types import FeeConfigUnified

        config = FeeConfigUnified()
        result = calculate_fees_from_unified_config(
            sell_price=Decimal("20.00"),
            weight_lbs=Decimal("1.5"),
            fee_config=config
        )

        expected_keys = ["referral_fee", "closing_fee", "fba_fee", "inbound_shipping", "prep_fee", "total_fees"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_calculate_fees_weight_based_fba(self):
        """Test FBA fee calculation with weight."""
        from app.core.fees_config import calculate_fees_from_unified_config
        from app.schemas.config_types import FeeConfigUnified

        config = FeeConfigUnified(
            fba_fee_base=Decimal("2.50"),
            fba_fee_per_lb=Decimal("0.50"),
        )

        # 1 pound
        result_1lb = calculate_fees_from_unified_config(
            sell_price=Decimal("20.00"),
            weight_lbs=Decimal("1.0"),
            fee_config=config
        )

        # 3 pounds
        result_3lb = calculate_fees_from_unified_config(
            sell_price=Decimal("20.00"),
            weight_lbs=Decimal("3.0"),
            fee_config=config
        )

        # FBA fee should be base + (weight * per_lb)
        assert result_1lb["fba_fee"] == Decimal("3.00")  # 2.50 + 1.0 * 0.50
        assert result_3lb["fba_fee"] == Decimal("4.00")  # 2.50 + 3.0 * 0.50

    def test_calculate_fees_total_sum(self):
        """Test that total_fees equals sum of all components."""
        from app.core.fees_config import calculate_fees_from_unified_config
        from app.schemas.config_types import FeeConfigUnified

        config = FeeConfigUnified(
            referral_fee_pct=Decimal("15.0"),
            closing_fee=Decimal("1.80"),
            fba_fee_base=Decimal("2.50"),
            fba_fee_per_lb=Decimal("0.40"),
            inbound_shipping=Decimal("0.40"),
            prep_fee=Decimal("0.20"),
        )

        result = calculate_fees_from_unified_config(
            sell_price=Decimal("30.00"),
            weight_lbs=Decimal("2.0"),
            fee_config=config
        )

        expected_total = (
            result["referral_fee"] +
            result["closing_fee"] +
            result["fba_fee"] +
            result["inbound_shipping"] +
            result["prep_fee"] +
            result["tax_amount"]
        )

        assert result["total_fees"] == expected_total

    def test_calculate_fees_category_in_result(self):
        """Test that category is included in result."""
        from app.core.fees_config import calculate_fees_from_unified_config
        from app.schemas.config_types import FeeConfigUnified

        config = FeeConfigUnified()
        result = calculate_fees_from_unified_config(
            sell_price=Decimal("20.00"),
            weight_lbs=Decimal("1.0"),
            fee_config=config,
            category="media"
        )

        assert result["category_used"] == "media"

    def test_calculate_fees_zero_price(self):
        """Test fee calculation with zero price."""
        from app.core.fees_config import calculate_fees_from_unified_config
        from app.schemas.config_types import FeeConfigUnified

        config = FeeConfigUnified()
        result = calculate_fees_from_unified_config(
            sell_price=Decimal("0.00"),
            weight_lbs=Decimal("1.0"),
            fee_config=config
        )

        # Referral fee should be 0 for zero price
        assert result["referral_fee"] == Decimal("0.00")
        # Fixed fees should still apply
        assert result["closing_fee"] == Decimal("1.80")
