"""Tests for unified config types."""

import pytest
from decimal import Decimal

from app.schemas.config_types import (
    ROIConfigUnified,
    FeeConfigUnified,
    VelocityConfigUnified,
    roi_schema_to_unified,
    fee_schema_to_unified,
    velocity_schema_to_unified,
)


class TestROIConfigUnified:
    """Test ROI config unified type."""

    def test_create_with_defaults(self):
        """Test creation with default values."""
        config = ROIConfigUnified()
        assert config.target_pct == Decimal("30.0")
        assert config.min_acceptable == Decimal("15.0")

    def test_create_with_custom_values(self):
        """Test creation with custom values."""
        config = ROIConfigUnified(
            target_pct=Decimal("35.0"),
            min_acceptable=Decimal("20.0"),
            excellent_threshold=Decimal("50.0")
        )
        assert config.target_pct == Decimal("35.0")

    def test_from_legacy_dict(self):
        """Test conversion from legacy business_config dict."""
        legacy = {
            "target_pct_default": 30.0,
            "min_for_buy": 15.0,
            "excellent_threshold": 50.0,
            "good_threshold": 30.0,
            "fair_threshold": 15.0
        }
        config = roi_schema_to_unified(legacy)
        assert config.target_pct == Decimal("30.0")
        assert config.min_acceptable == Decimal("15.0")

    def test_float_to_decimal_conversion(self):
        """Test that float values are converted to Decimal."""
        config = ROIConfigUnified(target_pct=35.5)
        assert isinstance(config.target_pct, Decimal)
        assert config.target_pct == Decimal("35.5")

    def test_from_config_schema_dict(self):
        """Test conversion from config.py schema dict format."""
        legacy = {
            "target": 30.0,
            "min_acceptable": 15.0,
            "excellent_threshold": 50.0,
        }
        config = roi_schema_to_unified(legacy)
        assert config.target_pct == Decimal("30.0")
        assert config.min_acceptable == Decimal("15.0")


class TestFeeConfigUnified:
    """Test Fee config unified type."""

    def test_create_with_defaults(self):
        """Test creation with default values."""
        config = FeeConfigUnified()
        assert config.referral_fee_pct == Decimal("15.0")
        assert config.closing_fee == Decimal("1.80")

    def test_from_legacy_dict_with_old_field_names(self):
        """Test conversion from legacy dict with different field names."""
        legacy = {
            "referral_fee_percent": 15.0,
            "closing_fee": 1.80,
            "fba_base_fee": 2.50,
            "fba_per_pound": 0.40,
        }
        config = fee_schema_to_unified(legacy)
        assert config.referral_fee_pct == Decimal("15.0")
        assert config.fba_fee_base == Decimal("2.50")

    def test_from_legacy_dict_with_new_field_names(self):
        """Test conversion from dict with current field names."""
        legacy = {
            "referral_fee_pct": 15.0,
            "closing_fee": 1.80,
            "fba_fee_base": 2.50,
            "fba_fee_per_lb": 0.40,
        }
        config = fee_schema_to_unified(legacy)
        assert config.referral_fee_pct == Decimal("15.0")
        assert config.fba_fee_base == Decimal("2.50")

    def test_from_config_schema_dict(self):
        """Test conversion from config.py schema dict format."""
        legacy = {
            "referral_fee_percent": 15.0,
            "fba_base_fee": 3.00,
            "fba_per_pound": 0.40,
            "closing_fee": 1.80,
            "prep_fee": 0.20,
            "shipping_cost": 0.40,
        }
        config = fee_schema_to_unified(legacy)
        assert config.referral_fee_pct == Decimal("15.0")
        assert config.fba_fee_base == Decimal("3.00")
        assert config.fba_fee_per_lb == Decimal("0.40")
        assert config.inbound_shipping == Decimal("0.40")


class TestVelocityConfigUnified:
    """Test Velocity config unified type."""

    def test_create_with_defaults(self):
        """Test creation with default values."""
        config = VelocityConfigUnified()
        assert config.fast_threshold == Decimal("80.0")
        assert config.medium_threshold == Decimal("60.0")
        assert config.slow_threshold == Decimal("40.0")

    def test_from_legacy_dict(self):
        """Test conversion from legacy dict."""
        legacy = {
            "fast_threshold": 85.0,
            "medium_threshold": 65.0,
            "slow_threshold": 45.0
        }
        config = velocity_schema_to_unified(legacy)
        assert config.fast_threshold == Decimal("85.0")

    def test_int_to_decimal_conversion(self):
        """Test that int values are converted to Decimal."""
        config = VelocityConfigUnified(fast_threshold=80)
        assert isinstance(config.fast_threshold, Decimal)
        assert config.fast_threshold == Decimal("80")


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_roi_empty_dict_uses_defaults(self):
        """Test that empty dict uses default values."""
        config = roi_schema_to_unified({})
        assert config.target_pct == Decimal("30.0")
        assert config.min_acceptable == Decimal("15.0")

    def test_fee_empty_dict_uses_defaults(self):
        """Test that empty dict uses default values."""
        config = fee_schema_to_unified({})
        assert config.referral_fee_pct == Decimal("15.0")
        assert config.closing_fee == Decimal("1.80")

    def test_velocity_empty_dict_uses_defaults(self):
        """Test that empty dict uses default values."""
        config = velocity_schema_to_unified({})
        assert config.fast_threshold == Decimal("80.0")

    def test_roi_partial_dict(self):
        """Test that partial dict fills missing with defaults."""
        legacy = {"target_pct_default": 40.0}
        config = roi_schema_to_unified(legacy)
        assert config.target_pct == Decimal("40.0")
        assert config.min_acceptable == Decimal("15.0")  # default

    def test_fee_partial_dict(self):
        """Test that partial dict fills missing with defaults."""
        legacy = {"closing_fee": 2.00}
        config = fee_schema_to_unified(legacy)
        assert config.closing_fee == Decimal("2.00")
        assert config.referral_fee_pct == Decimal("15.0")  # default

    def test_decimal_precision_preserved(self):
        """Test that decimal precision is preserved."""
        config = ROIConfigUnified(target_pct=Decimal("30.123456"))
        assert config.target_pct == Decimal("30.123456")
