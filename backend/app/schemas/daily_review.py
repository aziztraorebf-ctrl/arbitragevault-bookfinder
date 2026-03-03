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


class ActionableBuyItem(BaseModel):
    asin: str
    title: str = ""
    category: Optional[str] = None
    current_price: Optional[float] = None
    estimated_buy_price: Optional[float] = None
    roi_percentage: float = 0.0
    stability_score: float = 0.0
    confidence_score: float = 0.0
    velocity_score: float = 0.0
    bsr: Optional[int] = None
    overall_rating: float = 0.0
    classification: str = "STABLE"
    action_recommendation: str = "BUY"

    class Config:
        from_attributes = True


class ActionableBuyList(BaseModel):
    items: List[ActionableBuyItem] = Field(default_factory=list)
    total_found: int = 0
    filters_applied: dict = Field(default_factory=dict)
    generated_at: str = ""

    class Config:
        from_attributes = True


class DailyReviewResponse(BaseModel):
    review_date: str
    total: int = 0
    counts: DailyReviewCounts
    top_opportunities: List[ClassifiedProductResponse] = Field(default_factory=list)
    summary: str = ""

    class Config:
        from_attributes = True
