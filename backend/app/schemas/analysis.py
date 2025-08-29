"""Analysis schemas for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from decimal import Decimal

from pydantic import BaseModel, Field, validator


class TargetPriceResultSchema(BaseModel):
    """Schema for target price calculation results."""
    target_price: float = Field(..., description="Calculated target selling price")
    roi_target: float = Field(..., description="ROI target used for calculation")
    safety_buffer_used: float = Field(..., description="Safety buffer percentage applied")
    is_achievable: bool = Field(..., description="Whether target price is achievable in current market")
    price_gap_percentage: float = Field(..., description="Gap between target and current market price")
    calculation_details: Dict[str, Any] = Field(..., description="Detailed calculation breakdown")


class StrategicViewSummarySchema(BaseModel):
    """Schema for strategic view summary statistics."""
    total_products: int = Field(..., description="Total number of products analyzed")
    achievable_opportunities: int = Field(..., description="Number of achievable opportunities")
    achievable_percentage: float = Field(..., description="Percentage of achievable opportunities")
    avg_target_price: float = Field(..., description="Average target price")
    avg_strategic_score: float = Field(..., description="Average strategic score")
    total_potential_profit: float = Field(..., description="Total potential profit")


class StrategicViewResponseSchema(BaseModel):
    """Schema for strategic view responses with target prices."""
    view_name: str = Field(..., description="Strategic view name")
    description: str = Field(..., description="View description")
    roi_target: float = Field(..., description="ROI target for this view")
    products_count: int = Field(..., description="Number of products analyzed")
    products: list[Dict[str, Any]] = Field(..., description="Enriched product data with target prices")
    summary: StrategicViewSummarySchema = Field(..., description="Summary statistics")


class TopAnalysisStrategy(str, Enum):
    """Strategy for ranking top analyses."""
    ROI = "roi"
    VELOCITY = "velocity" 
    BALANCED = "balanced"


class AnalysisCreate(BaseModel):
    """Schema for creating new analysis."""
    batch_id: str = Field(..., description="ID of the batch this analysis belongs to")
    isbn_or_asin: str = Field(..., min_length=10, max_length=20, description="ISBN/ASIN of the book")
    buy_price: Decimal = Field(..., ge=0, description="Buy price")
    fees: Decimal = Field(..., ge=0, description="Amazon fees")
    expected_sale_price: Decimal = Field(..., ge=0, description="Expected sale price")
    profit: Decimal = Field(..., description="Calculated profit")
    roi_percent: Decimal = Field(..., description="ROI percentage")
    velocity_score: Decimal = Field(..., ge=0, le=1, description="Velocity score 0-1")
    rank_snapshot: Optional[int] = Field(None, ge=1, description="Amazon sales rank snapshot")
    offers_count: Optional[int] = Field(None, ge=0, description="Number of offers")
    raw_keepa: Optional[dict] = Field(None, description="Raw Keepa API data")
    
    @validator('isbn_or_asin')
    def validate_isbn_or_asin(cls, v):
        """Validate ISBN/ASIN format."""
        if v:
            cleaned = v.replace('-', '').replace(' ', '')
            if not (len(cleaned) in [10, 13] and cleaned.isalnum()):
                raise ValueError('Invalid ISBN/ASIN format')
        return v


class AnalysisResponse(BaseModel):
    """Schema for analysis responses."""
    id: str
    batch_id: str
    isbn_or_asin: str
    buy_price: Decimal
    fees: Decimal
    expected_sale_price: Decimal
    profit: Decimal
    roi_percent: Decimal
    velocity_score: Decimal
    rank_snapshot: Optional[int]
    offers_count: Optional[int]
    target_price_data: Optional[Dict[str, Any]] = Field(None, description="Target price calculation data")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisResponseEnriched(AnalysisResponse):
    """Schema for enriched analysis responses with target price results."""
    target_price_result: Optional[TargetPriceResultSchema] = Field(None, description="Target price calculation result")
    strategic_score: Optional[float] = Field(None, description="Strategic score for current view")
    target_price: Optional[float] = Field(None, description="Convenience field for target price")
    price_achievable: Optional[bool] = Field(None, description="Convenience field for achievability")