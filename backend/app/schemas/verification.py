"""Verification schemas for pre-purchase product verification.

Phase 8: Implements verification workflow for checking product status
before purchase decision. Compares saved analysis data against current
Keepa API data to detect changes.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class VerificationStatus(str, Enum):
    """Status of product verification.

    OK: Product conditions unchanged, safe to buy
    CHANGED: Significant changes detected, review recommended
    AVOID: Critical changes detected, do not buy
    """
    OK = "ok"
    CHANGED = "changed"
    AVOID = "avoid"


class VerificationChange(BaseModel):
    """Single detected change between saved and current data."""
    field: str = Field(..., description="Field that changed")
    saved_value: Any = Field(..., description="Value from saved analysis")
    current_value: Any = Field(..., description="Current value from Keepa API")
    severity: str = Field(
        ...,
        description="Severity: info, warning, critical",
        pattern="^(info|warning|critical)$"
    )
    message: str = Field(..., description="Human-readable change description")


class VerificationRequest(BaseModel):
    """Request to verify a product before purchase."""
    asin: str = Field(..., min_length=10, max_length=10, description="ASIN to verify")
    saved_price: Optional[Decimal] = Field(
        None, ge=0, description="Price from saved analysis (for comparison)"
    )
    saved_bsr: Optional[int] = Field(
        None, ge=1, description="BSR from saved analysis (for comparison)"
    )
    saved_fba_count: Optional[int] = Field(
        None, ge=0, description="FBA seller count from saved analysis"
    )


class VerificationResponse(BaseModel):
    """Response from product verification."""
    asin: str = Field(..., description="Verified ASIN")
    status: VerificationStatus = Field(..., description="Overall verification status")
    message: str = Field(..., description="Summary message for user")
    verified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of verification"
    )

    # Current data from Keepa
    current_price: Optional[Decimal] = Field(None, description="Current price")
    current_bsr: Optional[int] = Field(None, description="Current BSR")
    current_fba_count: Optional[int] = Field(None, description="Current FBA seller count")
    amazon_selling: bool = Field(False, description="Whether Amazon is selling this product")

    # Changes detected
    changes: List[VerificationChange] = Field(
        default_factory=list,
        description="List of detected changes"
    )

    # Profit impact
    estimated_profit: Optional[Decimal] = Field(
        None, description="Estimated profit at current price"
    )
    profit_change_percent: Optional[float] = Field(
        None, description="Profit change vs saved analysis (%)"
    )

    # Buy opportunities from third-party sellers
    buy_opportunities: List["BuyOpportunity"] = Field(
        default_factory=list,
        description="Available buy opportunities from third-party sellers"
    )
    sell_price: Optional[Decimal] = Field(
        None, description="Current Amazon sell price (for reference)"
    )

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
    )


class BuyOpportunity(BaseModel):
    """A single buy opportunity from a third-party seller."""
    seller_id: str = Field(..., description="Seller ID on Amazon")
    condition: str = Field(..., description="Product condition (New, Used-Good, etc.)")
    condition_code: int = Field(..., description="Keepa condition code (1=New, 2-5=Used)")
    price: Decimal = Field(..., ge=0, description="Item price in USD")
    shipping: Decimal = Field(Decimal("0"), ge=0, description="Shipping cost in USD")
    total_cost: Decimal = Field(..., ge=0, description="Total buy cost (price + shipping)")
    profit: Decimal = Field(..., description="Estimated profit after fees")
    roi_percent: float = Field(..., description="Return on investment percentage")
    is_fba: bool = Field(False, description="Whether seller uses FBA")
    is_prime: bool = Field(False, description="Whether offer is Prime eligible")

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v)
        }
    )


class VerificationThresholds(BaseModel):
    """Configurable thresholds for verification warnings.

    Used to determine when changes trigger warnings vs critical alerts.
    """
    price_change_warning: float = Field(
        10.0, description="Price change % to trigger warning"
    )
    price_change_critical: float = Field(
        25.0, description="Price change % to trigger critical"
    )
    bsr_change_warning: float = Field(
        50.0, description="BSR change % to trigger warning"
    )
    bsr_change_critical: float = Field(
        100.0, description="BSR change % to trigger critical"
    )
    fba_count_warning: int = Field(
        3, description="FBA count increase to trigger warning"
    )
    fba_count_critical: int = Field(
        5, description="FBA count increase to trigger critical"
    )
