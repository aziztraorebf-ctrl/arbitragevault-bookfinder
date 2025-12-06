"""
Configuration schemas for dynamic business parameters.

This module defines the configuration structure for fees, ROI thresholds,
velocity tiers, and other business parameters that can be adjusted without
code changes.
"""

from typing import Dict, Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime


class FeeConfig(BaseModel):
    """Fee configuration for different product categories."""

    referral_fee_percent: Decimal = Field(
        default=Decimal("15.0"),
        description="Amazon referral fee percentage",
        ge=0,
        le=50
    )
    fba_base_fee: Decimal = Field(
        default=Decimal("3.00"),
        description="Base FBA fulfillment fee",
        ge=0,
        le=20
    )
    fba_per_pound: Decimal = Field(
        default=Decimal("0.40"),
        description="FBA fee per pound of weight",
        ge=0,
        le=5
    )
    closing_fee: Decimal = Field(
        default=Decimal("1.80"),
        description="Amazon closing fee for media items",
        ge=0,
        le=10
    )
    prep_fee: Decimal = Field(
        default=Decimal("0.20"),
        description="Item preparation fee",
        ge=0,
        le=5
    )
    shipping_cost: Decimal = Field(
        default=Decimal("0.40"),
        description="Inbound shipping cost estimate",
        ge=0,
        le=5
    )

    model_config = {
        "json_encoders": {
            Decimal: lambda v: float(v)
        }
    }


class ROIConfig(BaseModel):
    """ROI calculation and threshold configuration."""

    min_acceptable: Decimal = Field(
        default=Decimal("15.0"),
        description="Minimum ROI % to consider product viable",
        ge=0,
        le=100
    )
    target: Decimal = Field(
        default=Decimal("30.0"),
        description="Target ROI % for ideal products",
        ge=0,
        le=200
    )
    excellent_threshold: Decimal = Field(
        default=Decimal("50.0"),
        description="ROI % threshold for excellent rating",
        ge=0,
        le=300
    )
    source_price_factor: Decimal = Field(
        default=Decimal("0.50"),
        description="Factor to estimate source price from Buy Box (0.50 = 50% of Buy Box). "
                    "Amazon FBM->FBA arbitrage: buy FBM at ~50% of FBA price, aligned with guide.",
        ge=0.1,
        le=0.9
    )

    model_config = {
        "json_encoders": {
            Decimal: lambda v: float(v)
        }
    }

    @model_validator(mode='after')
    def validate_roi_thresholds(self):
        """Validate that ROI thresholds are logically ordered."""
        if self.target < self.min_acceptable:
            raise ValueError(
                f"ROI target ({self.target}%) must be >= min_acceptable ({self.min_acceptable}%)"
            )
        if self.excellent_threshold < self.target:
            raise ValueError(
                f"ROI excellent_threshold ({self.excellent_threshold}%) must be >= target ({self.target}%)"
            )
        return self


class VelocityTier(BaseModel):
    """Single velocity tier definition."""

    name: str = Field(description="Tier name (e.g., PREMIUM, HIGH)")
    min_score: int = Field(ge=0, le=100, description="Minimum score for this tier")
    max_score: int = Field(ge=0, le=100, description="Maximum score for this tier")
    bsr_threshold: int = Field(ge=1, description="Maximum BSR for this tier")
    description: str = Field(default="", description="Tier description")

    @model_validator(mode='after')
    def validate_score_range(self):
        """Validate that score range is logical."""
        if self.max_score < self.min_score:
            raise ValueError(
                f"max_score ({self.max_score}) must be >= min_score ({self.min_score})"
            )
        return self


class VelocityConfig(BaseModel):
    """Velocity scoring configuration."""

    tiers: List[VelocityTier] = Field(
        default=[
            VelocityTier(
                name="PREMIUM",
                min_score=80,
                max_score=100,
                bsr_threshold=10000,
                description="Top selling products"
            ),
            VelocityTier(
                name="HIGH",
                min_score=60,
                max_score=79,
                bsr_threshold=50000,
                description="Fast moving products"
            ),
            VelocityTier(
                name="MEDIUM",
                min_score=40,
                max_score=59,
                bsr_threshold=100000,
                description="Moderate velocity"
            ),
            VelocityTier(
                name="LOW",
                min_score=20,
                max_score=39,
                bsr_threshold=500000,
                description="Slow moving products"
            ),
            VelocityTier(
                name="DEAD",
                min_score=0,
                max_score=19,
                bsr_threshold=999999999,
                description="Very slow or dead stock"
            )
        ]
    )

    history_days: int = Field(
        default=30,
        description="Number of days to analyze for velocity calculation",
        ge=7,
        le=180
    )

    rank_drop_multiplier: Decimal = Field(
        default=Decimal("1.5"),
        description="Multiplier for rank drop significance",
        ge=1,
        le=5
    )

    @model_validator(mode='after')
    def validate_velocity_tiers(self):
        """Validate that velocity tiers don't overlap and are properly ordered."""
        if not self.tiers:
            raise ValueError("At least one velocity tier must be defined")

        # Sort tiers by min_score descending
        sorted_tiers = sorted(self.tiers, key=lambda t: t.min_score, reverse=True)

        # Check for overlaps
        for i in range(len(sorted_tiers) - 1):
            current = sorted_tiers[i]
            next_tier = sorted_tiers[i + 1]

            if current.min_score <= next_tier.max_score:
                raise ValueError(
                    f"Velocity tier overlap detected: {current.name} (min: {current.min_score}) "
                    f"overlaps with {next_tier.name} (max: {next_tier.max_score})"
                )

        return self


class CategoryConfig(BaseModel):
    """Category-specific configuration overrides."""

    category_id: int = Field(description="Keepa category ID")
    category_name: str = Field(description="Category name for reference")
    fees: Optional[FeeConfig] = None
    roi: Optional[ROIConfig] = None
    velocity: Optional[VelocityConfig] = None

    model_config = {
        "from_attributes": True
    }


class DataQualityThresholds(BaseModel):
    """Thresholds for data quality scoring."""

    min_bsr_points: int = Field(
        default=50,
        description="Minimum BSR history points for good quality",
        ge=10,
        le=500
    )
    min_price_history_days: int = Field(
        default=30,
        description="Minimum days of price history",
        ge=7,
        le=180
    )
    min_quality_score: int = Field(
        default=60,
        description="Minimum quality score to consider data reliable",
        ge=0,
        le=100
    )


class ProductFinderConfig(BaseModel):
    """Configuration for Keepa Product Finder integration."""

    max_results_per_search: int = Field(
        default=100,
        description="Maximum products to return per search",
        ge=10,
        le=500
    )
    default_bsr_range: tuple[int, int] = Field(
        default=(1000, 100000),
        description="Default BSR range for searches"
    )
    default_price_range: tuple[Decimal, Decimal] = Field(
        default=(Decimal("10.00"), Decimal("100.00")),
        description="Default price range for searches"
    )
    exclude_variations: bool = Field(
        default=True,
        description="Exclude product variations from results"
    )
    require_buy_box: bool = Field(
        default=True,
        description="Only include products with Buy Box price"
    )

    model_config = {
        "json_encoders": {
            Decimal: lambda v: float(v)
        }
    }


class ConfigCreate(BaseModel):
    """Schema for creating a new configuration."""

    name: str = Field(description="Configuration name")
    description: Optional[str] = Field(default=None)
    fees: FeeConfig = Field(default_factory=FeeConfig)
    roi: ROIConfig = Field(default_factory=ROIConfig)
    velocity: VelocityConfig = Field(default_factory=VelocityConfig)
    data_quality: DataQualityThresholds = Field(default_factory=DataQualityThresholds)
    product_finder: ProductFinderConfig = Field(default_factory=ProductFinderConfig)
    category_overrides: List[CategoryConfig] = Field(default_factory=list)
    is_active: bool = Field(default=False)


class ConfigUpdate(BaseModel):
    """Schema for updating configuration."""

    name: Optional[str] = None
    description: Optional[str] = None
    fees: Optional[FeeConfig] = None
    roi: Optional[ROIConfig] = None
    velocity: Optional[VelocityConfig] = None
    data_quality: Optional[DataQualityThresholds] = None
    product_finder: Optional[ProductFinderConfig] = None
    category_overrides: Optional[List[CategoryConfig]] = None
    is_active: Optional[bool] = None


class ConfigResponse(BaseModel):
    """Schema for configuration responses."""

    id: str
    name: str
    description: Optional[str]
    fees: FeeConfig
    roi: ROIConfig
    velocity: VelocityConfig
    data_quality: DataQualityThresholds
    product_finder: ProductFinderConfig
    category_overrides: List[CategoryConfig]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
    }


class EffectiveConfig(BaseModel):
    """
    Effective configuration after applying category overrides.
    This is what the application actually uses for calculations.
    """

    base_config: ConfigResponse
    category_id: Optional[int] = None
    effective_fees: FeeConfig
    effective_roi: ROIConfig
    effective_velocity: VelocityConfig
    applied_overrides: List[str] = Field(
        default_factory=list,
        description="List of overridden parameters"
    )

    model_config = {
        "json_encoders": {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
    }