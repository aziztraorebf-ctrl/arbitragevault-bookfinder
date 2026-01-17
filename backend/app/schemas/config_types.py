"""
Unified Configuration Types - Phase 1C

Single source of truth for all config schemas.
Provides conversion functions from legacy formats.

This module consolidates duplicate schema definitions from:
- app/schemas/config.py (FeeConfig, ROIConfig, VelocityConfig)
- app/schemas/business_config_schemas.py (RoiConfigSchema, FeeConfigItemSchema, VelocityConfigSchema)

Field name mappings handled:
- ROI: target_pct_default / target -> target_pct
- ROI: min_for_buy / min_acceptable -> min_acceptable
- Fee: referral_fee_percent / referral_fee_pct -> referral_fee_pct
- Fee: fba_base_fee / fba_fee_base -> fba_fee_base
- Fee: fba_per_pound / fba_fee_per_lb -> fba_fee_per_lb
- Fee: shipping_cost / inbound_shipping -> inbound_shipping
"""

from decimal import Decimal
from typing import Dict, Any
from pydantic import BaseModel, Field, field_validator, field_serializer


class ROIConfigUnified(BaseModel):
    """Unified ROI configuration.

    Consolidates:
    - config.py ROIConfig (target, min_acceptable, excellent_threshold, source_price_factor)
    - business_config_schemas.py RoiConfigSchema (target_pct_default, min_for_buy, excellent/good/fair_threshold)
    """

    target_pct: Decimal = Field(default=Decimal("30.0"), description="Target ROI percentage")
    min_acceptable: Decimal = Field(default=Decimal("15.0"), description="Minimum acceptable ROI")
    excellent_threshold: Decimal = Field(default=Decimal("50.0"), description="Excellent ROI threshold")
    good_threshold: Decimal = Field(default=Decimal("30.0"), description="Good ROI threshold")
    fair_threshold: Decimal = Field(default=Decimal("15.0"), description="Fair ROI threshold")
    source_price_factor: Decimal = Field(
        default=Decimal("0.50"),
        description="Factor to estimate source price from Buy Box (0.50 = 50%)"
    )

    @field_validator('target_pct', 'min_acceptable', 'excellent_threshold',
                     'good_threshold', 'fair_threshold', 'source_price_factor', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert int/float to Decimal for precision."""
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    @field_serializer('target_pct', 'min_acceptable', 'excellent_threshold',
                      'good_threshold', 'fair_threshold', 'source_price_factor')
    def serialize_decimal(self, v: Decimal) -> float:
        """Serialize Decimal to float for JSON."""
        return float(v)


class FeeConfigUnified(BaseModel):
    """Unified Fee configuration.

    Consolidates:
    - config.py FeeConfig (referral_fee_percent, fba_base_fee, fba_per_pound, closing_fee, prep_fee, shipping_cost)
    - business_config_schemas.py FeeConfigItemSchema (referral_fee_pct, fba_fee_base, fba_fee_per_lb, inbound_shipping)
    """

    referral_fee_pct: Decimal = Field(default=Decimal("15.0"), description="Referral fee percentage")
    closing_fee: Decimal = Field(default=Decimal("1.80"), description="Closing fee")
    fba_fee_base: Decimal = Field(default=Decimal("2.50"), description="FBA base fee")
    fba_fee_per_lb: Decimal = Field(default=Decimal("0.40"), description="FBA fee per pound")
    inbound_shipping: Decimal = Field(default=Decimal("0.40"), description="Inbound shipping cost")
    prep_fee: Decimal = Field(default=Decimal("0.20"), description="Prep fee")
    buffer_pct: Decimal = Field(default=Decimal("5.0"), description="Safety buffer percentage")

    @field_validator('referral_fee_pct', 'closing_fee', 'fba_fee_base', 'fba_fee_per_lb',
                     'inbound_shipping', 'prep_fee', 'buffer_pct', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert int/float to Decimal for precision."""
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    @field_serializer('referral_fee_pct', 'closing_fee', 'fba_fee_base', 'fba_fee_per_lb',
                      'inbound_shipping', 'prep_fee', 'buffer_pct')
    def serialize_decimal(self, v: Decimal) -> float:
        """Serialize Decimal to float for JSON."""
        return float(v)


class VelocityConfigUnified(BaseModel):
    """Unified Velocity configuration.

    Consolidates velocity threshold settings from:
    - business_config_schemas.py VelocityConfigSchema (fast_threshold, medium_threshold, slow_threshold)
    """

    fast_threshold: Decimal = Field(default=Decimal("80.0"), description="Fast velocity threshold")
    medium_threshold: Decimal = Field(default=Decimal("60.0"), description="Medium velocity threshold")
    slow_threshold: Decimal = Field(default=Decimal("40.0"), description="Slow velocity threshold")

    @field_validator('fast_threshold', 'medium_threshold', 'slow_threshold', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert int/float to Decimal for precision."""
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    @field_serializer('fast_threshold', 'medium_threshold', 'slow_threshold')
    def serialize_decimal(self, v: Decimal) -> float:
        """Serialize Decimal to float for JSON."""
        return float(v)


def roi_schema_to_unified(legacy: Dict[str, Any]) -> ROIConfigUnified:
    """Convert legacy ROI config dict to unified type.

    Handles field name variations:
    - target_pct_default (business_config_schemas) -> target_pct
    - target (config.py) -> target_pct
    - min_for_buy (business_config_schemas) -> min_acceptable
    - min_acceptable (config.py) -> min_acceptable

    Args:
        legacy: Dictionary with legacy field names

    Returns:
        ROIConfigUnified instance with normalized field names
    """
    return ROIConfigUnified(
        target_pct=legacy.get("target_pct_default", legacy.get("target_pct", legacy.get("target", 30.0))),
        min_acceptable=legacy.get("min_for_buy", legacy.get("min_acceptable", 15.0)),
        excellent_threshold=legacy.get("excellent_threshold", 50.0),
        good_threshold=legacy.get("good_threshold", 30.0),
        fair_threshold=legacy.get("fair_threshold", 15.0),
        source_price_factor=legacy.get("source_price_factor", 0.50),
    )


def fee_schema_to_unified(legacy: Dict[str, Any]) -> FeeConfigUnified:
    """Convert legacy Fee config dict to unified type.

    Handles field name variations:
    - referral_fee_percent (config.py) -> referral_fee_pct
    - referral_fee_pct (business_config_schemas) -> referral_fee_pct
    - fba_base_fee (config.py) -> fba_fee_base
    - fba_per_pound (config.py) -> fba_fee_per_lb
    - shipping_cost (config.py) -> inbound_shipping

    Args:
        legacy: Dictionary with legacy field names

    Returns:
        FeeConfigUnified instance with normalized field names
    """
    return FeeConfigUnified(
        referral_fee_pct=legacy.get("referral_fee_pct", legacy.get("referral_fee_percent", 15.0)),
        closing_fee=legacy.get("closing_fee", 1.80),
        fba_fee_base=legacy.get("fba_fee_base", legacy.get("fba_base_fee", 2.50)),
        fba_fee_per_lb=legacy.get("fba_fee_per_lb", legacy.get("fba_per_pound", 0.40)),
        inbound_shipping=legacy.get("inbound_shipping", legacy.get("shipping_cost", 0.40)),
        prep_fee=legacy.get("prep_fee", 0.20),
        buffer_pct=legacy.get("buffer_pct", legacy.get("buffer_pct_default", 5.0)),
    )


def velocity_schema_to_unified(legacy: Dict[str, Any]) -> VelocityConfigUnified:
    """Convert legacy Velocity config dict to unified type.

    Args:
        legacy: Dictionary with velocity threshold fields

    Returns:
        VelocityConfigUnified instance
    """
    return VelocityConfigUnified(
        fast_threshold=legacy.get("fast_threshold", 80.0),
        medium_threshold=legacy.get("medium_threshold", 60.0),
        slow_threshold=legacy.get("slow_threshold", 40.0),
    )
