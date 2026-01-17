# backend/tests/e2e/test_phase1_validation.py
"""
E2E Tests validating Phase 1 refactoring integrity.

These tests verify that:
1. ConfigServiceAdapter returns correct unified config types
2. Fee calculations use the canonical calculate_fees_from_unified_config
3. ROI calculations are consistent across discovery and analysis paths
4. Config changes propagate correctly to fee calculations

Phase 1 Components Tested:
- Phase 1A: Code simplification (implicit - code runs)
- Phase 1B: ConfigServiceAdapter (config retrieval)
- Phase 1C: Unified config types (type consistency)
- Phase 1D: Centralized fee calculations (fee accuracy)
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.config_adapter import ConfigServiceAdapter, get_config_adapter
from app.core.fees_config import calculate_total_fees, calculate_fees_from_unified_config
from app.schemas.config_types import (
    FeeConfigUnified,
    ROIConfigUnified,
    VelocityConfigUnified,
    fee_schema_to_unified,
)


class TestPhase1DFeeCentralization:
    """Test that fee calculations are centralized and consistent."""

    def test_canonical_fee_calculation_matches_direct(self):
        """
        CRITICAL: Verify canonical function produces same results as direct calculation.

        This validates Phase 1D: calculate_fees_from_unified_config must match
        calculate_total_fees for identical inputs.
        """
        # Setup
        sell_price = Decimal("25.00")
        weight_lbs = Decimal("1.5")

        # Create unified config matching books defaults
        unified_config = FeeConfigUnified(
            referral_fee_pct=Decimal("15.0"),
            closing_fee=Decimal("1.80"),
            fba_fee_base=Decimal("2.50"),
            fba_fee_per_lb=Decimal("0.40"),
            inbound_shipping=Decimal("0.40"),
            prep_fee=Decimal("0.20"),
        )

        # Calculate via canonical wrapper (Phase 1D)
        canonical_result = calculate_fees_from_unified_config(
            sell_price=sell_price,
            weight_lbs=weight_lbs,
            fee_config=unified_config,
            category="books"
        )

        # Calculate via direct function
        direct_result = calculate_total_fees(
            sell_price=sell_price,
            weight_lbs=weight_lbs,
            category="books"
        )

        # Assert key components match
        assert canonical_result["referral_fee"] == direct_result["referral_fee"], \
            f"Referral fee mismatch: {canonical_result['referral_fee']} vs {direct_result['referral_fee']}"
        assert canonical_result["closing_fee"] == direct_result["closing_fee"], \
            f"Closing fee mismatch: {canonical_result['closing_fee']} vs {direct_result['closing_fee']}"
        assert canonical_result["fba_fee"] == direct_result["fba_fee"], \
            f"FBA fee mismatch: {canonical_result['fba_fee']} vs {direct_result['fba_fee']}"
        assert canonical_result["total_fees"] == direct_result["total_fees"], \
            f"Total fees mismatch: {canonical_result['total_fees']} vs {direct_result['total_fees']}"

    def test_fee_calculation_all_components_present(self):
        """Verify all fee components are returned by canonical function."""
        config = FeeConfigUnified()
        result = calculate_fees_from_unified_config(
            sell_price=Decimal("20.00"),
            weight_lbs=Decimal("1.0"),
            fee_config=config
        )

        required_keys = [
            "referral_fee",
            "closing_fee",
            "fba_fee",
            "inbound_shipping",
            "prep_fee",
            "tax_amount",
            "total_fees",
        ]

        for key in required_keys:
            assert key in result, f"Missing required fee component: {key}"
            assert isinstance(result[key], Decimal), f"{key} should be Decimal, got {type(result[key])}"

    def test_fee_calculation_weight_scaling(self):
        """Verify FBA fee scales correctly with weight."""
        config = FeeConfigUnified(
            fba_fee_base=Decimal("2.50"),
            fba_fee_per_lb=Decimal("0.40"),
        )

        # 1 lb
        result_1lb = calculate_fees_from_unified_config(
            sell_price=Decimal("20.00"),
            weight_lbs=Decimal("1.0"),
            fee_config=config
        )

        # 5 lbs
        result_5lb = calculate_fees_from_unified_config(
            sell_price=Decimal("20.00"),
            weight_lbs=Decimal("5.0"),
            fee_config=config
        )

        # FBA fee difference should be 4 lbs * $0.40 = $1.60
        expected_diff = Decimal("1.60")
        actual_diff = result_5lb["fba_fee"] - result_1lb["fba_fee"]

        assert actual_diff == expected_diff, \
            f"FBA weight scaling incorrect: expected {expected_diff}, got {actual_diff}"


class TestPhase1CUnifiedConfigTypes:
    """Test unified config types from Phase 1C."""

    def test_fee_config_unified_defaults(self):
        """Verify FeeConfigUnified has sensible defaults."""
        config = FeeConfigUnified()

        assert config.referral_fee_pct == Decimal("15.0")
        assert config.closing_fee == Decimal("1.80")
        assert config.fba_fee_base == Decimal("2.50")
        assert config.fba_fee_per_lb == Decimal("0.40")
        assert config.inbound_shipping == Decimal("0.40")
        assert config.prep_fee == Decimal("0.20")

    def test_fee_config_unified_from_float(self):
        """Verify float values are converted to Decimal."""
        config = FeeConfigUnified(
            referral_fee_pct=15.0,  # float, not Decimal
            closing_fee=1.80,
        )

        assert isinstance(config.referral_fee_pct, Decimal)
        assert isinstance(config.closing_fee, Decimal)
        assert config.referral_fee_pct == Decimal("15.0")

    def test_fee_schema_to_unified_legacy_field_names(self):
        """Verify legacy field names are mapped correctly."""
        legacy_dict = {
            "referral_fee_percent": 15.0,  # Legacy name
            "fba_base_fee": 2.50,           # Legacy name
            "fba_per_pound": 0.40,          # Legacy name
            "shipping_cost": 0.40,          # Legacy name
        }

        unified = fee_schema_to_unified(legacy_dict)

        assert unified.referral_fee_pct == Decimal("15.0")
        assert unified.fba_fee_base == Decimal("2.50")
        assert unified.fba_fee_per_lb == Decimal("0.40")
        assert unified.inbound_shipping == Decimal("0.40")

    def test_roi_config_unified_defaults(self):
        """Verify ROIConfigUnified has sensible defaults."""
        config = ROIConfigUnified()

        assert config.target_pct == Decimal("30.0")
        assert config.min_acceptable == Decimal("15.0")
        assert config.excellent_threshold == Decimal("50.0")

    def test_velocity_config_unified_defaults(self):
        """Verify VelocityConfigUnified has sensible defaults."""
        config = VelocityConfigUnified()

        assert config.fast_threshold == Decimal("80.0")
        assert config.medium_threshold == Decimal("60.0")
        assert config.slow_threshold == Decimal("40.0")


class TestPhase1BConfigAdapter:
    """Test ConfigServiceAdapter from Phase 1B."""

    @pytest.mark.asyncio
    async def test_adapter_returns_unified_types(self):
        """Verify adapter returns proper unified config types."""
        mock_config = {
            "roi": {"target_pct_default": 30.0, "min_for_buy": 15.0},
            "fees": {"referral_fee_pct": 15.0, "closing_fee": 1.80},
            "velocity": {"fast_threshold": 80.0},
            "_meta": {"sources": {}}
        }

        with patch('app.services.config_adapter.get_business_config_service') as mock_get:
            mock_service = MagicMock()
            mock_service.get_effective_config = AsyncMock(return_value=mock_config)
            mock_get.return_value = mock_service

            adapter = ConfigServiceAdapter()
            result = await adapter.get_effective_config(category_id=283155)

            # Verify unified types
            assert isinstance(result.effective_fees, FeeConfigUnified)
            assert isinstance(result.effective_roi, ROIConfigUnified)
            assert isinstance(result.effective_velocity, VelocityConfigUnified)

    @pytest.mark.asyncio
    async def test_adapter_category_id_mapping(self):
        """Verify category IDs are mapped to names correctly."""
        adapter = ConfigServiceAdapter()

        # Known mapping (testing private method via public interface behavior)
        assert adapter._category_id_to_name(283155) == "books"

        # Unknown defaults to "default"
        assert adapter._category_id_to_name(999999) == "default"
        assert adapter._category_id_to_name(0) == "default"

    @pytest.mark.asyncio
    async def test_adapter_handles_none_config(self):
        """Verify adapter handles None response gracefully."""
        with patch('app.services.config_adapter.get_business_config_service') as mock_get:
            mock_service = MagicMock()
            mock_service.get_effective_config = AsyncMock(return_value=None)
            mock_get.return_value = mock_service

            adapter = ConfigServiceAdapter()
            result = await adapter.get_effective_config()

            # Should return default unified types
            assert isinstance(result.effective_fees, FeeConfigUnified)
            assert result.effective_fees.referral_fee_pct == Decimal("15.0")


class TestPhase1IntegrationFlow:
    """Integration tests verifying complete Phase 1 data flow."""

    @pytest.mark.asyncio
    async def test_config_to_fee_calculation_flow(self):
        """
        CRITICAL: Test complete flow from config retrieval to fee calculation.

        Flow:
        1. ConfigServiceAdapter retrieves config
        2. Config converted to FeeConfigUnified
        3. calculate_fees_from_unified_config computes fees
        4. Fees used for ROI calculation
        """
        # Mock business config service
        mock_config = {
            "roi": {"target_pct_default": 30.0},
            "fees": {
                "books": {
                    "referral_fee_pct": 15.0,
                    "closing_fee": 1.80,
                    "fba_fee_base": 2.50,
                    "fba_fee_per_lb": 0.40,
                    "inbound_shipping": 0.40,
                    "prep_fee": 0.20,
                }
            },
            "velocity": {"fast_threshold": 80.0},
            "_meta": {"sources": {"global": True}}
        }

        with patch('app.services.config_adapter.get_business_config_service') as mock_get:
            mock_service = MagicMock()
            mock_service.get_effective_config = AsyncMock(return_value=mock_config)
            mock_get.return_value = mock_service

            # Step 1: Get config via adapter
            adapter = ConfigServiceAdapter()
            config = await adapter.get_effective_config(category_id=283155)

            # Step 2: Use fee config for calculation
            fee_result = calculate_fees_from_unified_config(
                sell_price=Decimal("30.00"),
                weight_lbs=Decimal("1.0"),
                fee_config=config.effective_fees
            )

            # Step 3: Calculate ROI (simplified)
            buy_cost = Decimal("10.00")
            sell_price = Decimal("30.00")
            total_fees = fee_result["total_fees"]

            profit = sell_price - buy_cost - total_fees
            roi_pct = (profit / buy_cost) * Decimal("100")

            # Verify ROI is reasonable (should be positive with good margin)
            assert roi_pct > Decimal("0"), f"ROI should be positive, got {roi_pct}"

            # Verify config threshold comparison works
            target_roi = config.effective_roi.target_pct
            assert isinstance(target_roi, Decimal)

            # ROI should be compared against config threshold
            meets_target = roi_pct >= target_roi
            assert isinstance(meets_target, bool)

    def test_fee_consistency_across_categories(self):
        """Verify fee calculation is consistent for same inputs regardless of path."""
        # Same inputs
        sell_price = Decimal("25.00")
        weight = Decimal("1.0")

        # Path 1: Direct via calculate_total_fees
        direct = calculate_total_fees(sell_price, weight, "books")

        # Path 2: Via unified config
        unified = calculate_fees_from_unified_config(
            sell_price=sell_price,
            weight_lbs=weight,
            fee_config=FeeConfigUnified(),  # Uses same defaults as "books"
        )

        # Total fees must match
        assert direct["total_fees"] == unified["total_fees"], \
            f"Fee paths diverge: direct={direct['total_fees']}, unified={unified['total_fees']}"


class TestRegressionGuards:
    """Regression tests to catch future breaking changes."""

    def test_books_category_fee_values_stable(self):
        """
        GUARD: Ensure books category fees don't accidentally change.

        If this test fails, it means someone changed the default fee values.
        Update the expected values ONLY if the change is intentional.
        """
        result = calculate_total_fees(
            sell_price=Decimal("20.00"),
            weight_lbs=Decimal("1.0"),
            category="books"
        )

        # Expected values for books category (as of Phase 1D)
        assert result["referral_fee"] == Decimal("3.00"), "Referral fee changed unexpectedly"
        assert result["closing_fee"] == Decimal("1.80"), "Closing fee changed unexpectedly"
        assert result["fba_fee"] == Decimal("2.90"), "FBA fee changed unexpectedly"  # 2.50 + 1.0 * 0.40
        assert result["inbound_shipping"] == Decimal("0.40"), "Inbound shipping changed unexpectedly"
        assert result["prep_fee"] == Decimal("0.20"), "Prep fee changed unexpectedly"

    def test_unified_config_default_values_stable(self):
        """
        GUARD: Ensure unified config defaults don't accidentally change.
        """
        fee = FeeConfigUnified()
        roi = ROIConfigUnified()
        velocity = VelocityConfigUnified()

        # Fee defaults
        assert fee.referral_fee_pct == Decimal("15.0")
        assert fee.closing_fee == Decimal("1.80")

        # ROI defaults
        assert roi.target_pct == Decimal("30.0")
        assert roi.min_acceptable == Decimal("15.0")

        # Velocity defaults
        assert velocity.fast_threshold == Decimal("80.0")
        assert velocity.slow_threshold == Decimal("40.0")
