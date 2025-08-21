"""Analysis schemas for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, Field, validator


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
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True