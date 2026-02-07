"""Pydantic schemas for Daily Review API responses."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ClassifiedProductResponse(BaseModel):
    asin: str
    title: str = ""
    roi_percentage: float = 0.0
    bsr: int = 0
    current_price: Optional[float] = None
    buy_price: Optional[float] = None
    amazon_on_listing: bool = False
    classification: str
    classification_label: str
    classification_action: str
    classification_color: str

    class Config:
        from_attributes = True


class DailyReviewCounts(BaseModel):
    STABLE: int = 0
    JACKPOT: int = 0
    REVENANT: int = 0
    FLUKE: int = 0
    REJECT: int = 0


class DailyReviewResponse(BaseModel):
    review_date: str
    total: int = 0
    counts: DailyReviewCounts
    top_opportunities: List[ClassifiedProductResponse] = Field(default_factory=list)
    summary: str = ""

    class Config:
        from_attributes = True
