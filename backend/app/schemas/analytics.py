"""
Pydantic schemas for Phase 8.0 Analytics API
"""
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class AnalyticsRequestSchema(BaseModel):
    """Request schema for analytics calculations."""
    asin: str
    title: Optional[str] = None
    category: Optional[str] = 'books'

    bsr: Optional[int] = None
    bsr_history: Optional[List[Dict[str, Any]]] = None

    # Keepa real data - used for accurate velocity calculation
    sales_drops_30: Optional[int] = None  # From Keepa salesRankDrops30
    sales_drops_90: Optional[int] = None  # From Keepa salesRankDrops90

    price_history: Optional[List[Dict[str, Any]]] = None
    estimated_buy_price: Decimal = Field(..., decimal_places=2)
    estimated_sell_price: Decimal = Field(..., decimal_places=2)

    seller_count: Optional[int] = None
    fba_seller_count: Optional[int] = None
    amazon_on_listing: Optional[bool] = False
    amazon_has_buybox: Optional[bool] = False

    referral_fee_percent: Optional[Decimal] = Field(default=15, decimal_places=2)
    fba_fee: Optional[Decimal] = Field(default=2.50, decimal_places=2)
    prep_fee: Optional[Decimal] = None
    return_rate_percent: Optional[Decimal] = Field(default=2, decimal_places=2)
    storage_cost_monthly: Optional[Decimal] = Field(default=0.87, decimal_places=2)
    estimated_sale_cycle_days: Optional[int] = 30

    class Config:
        json_schema_extra = {
            "example": {
                "asin": "B001234567",
                "title": "The Great Book",
                "category": "fiction",
                "bsr": 15000,
                "estimated_buy_price": "5.00",
                "estimated_sell_price": "19.99",
                "seller_count": 8,
                "fba_seller_count": 5,
                "amazon_on_listing": False,
                "estimated_sale_cycle_days": 30
            }
        }


class VelocityAnalyticsSchema(BaseModel):
    """Velocity intelligence response."""
    velocity_score: float
    trend_7d: Optional[float] = None
    trend_30d: Optional[float] = None
    trend_90d: Optional[float] = None
    bsr_current: Optional[int] = None
    risk_level: str


class PriceStabilitySchema(BaseModel):
    """Price stability analysis response."""
    stability_score: float
    coefficient_variation: Optional[float] = None
    price_volatility: str
    avg_price: Optional[float] = None
    std_deviation: Optional[float] = None


class ROIAnalysisSchema(BaseModel):
    """ROI net calculation response."""
    net_profit: float
    roi_percentage: float
    gross_profit: float
    referral_fee: float
    fba_fee: float
    prep_fee: float
    storage_cost: float
    return_losses: float
    total_fees: float
    breakeven_required_days: Optional[int] = None


class CompetitionAnalysisSchema(BaseModel):
    """Competition analysis response."""
    competition_score: float
    competition_level: str
    seller_count: Optional[int] = None
    fba_ratio: Optional[float] = None
    amazon_risk: str


class SlowVelocitySchema(BaseModel):
    """Slow velocity risk assessment based on real Keepa salesDrops data."""
    velocity_tier: str  # PREMIUM, HIGH, MEDIUM, LOW, DEAD
    monthly_sales_estimate: int
    risk_score: float  # 0-100, higher = slower/riskier
    tier_description: str
    data_source: str  # 'KEEPA_REAL' or 'ESTIMATED'


class RiskComponentSchema(BaseModel):
    """Single risk component with weight."""
    score: float
    weighted: float
    weight: float


class RiskScoreResponseSchema(BaseModel):
    """Risk score calculation response."""
    asin: str
    risk_score: float
    risk_level: str
    components: Dict[str, RiskComponentSchema]
    recommendations: str


class RecommendationResponseSchema(BaseModel):
    """Final recommendation response."""
    asin: str
    title: str
    recommendation: str
    confidence_percent: float
    criteria_passed: int
    criteria_total: int
    reason: str
    roi_net: float
    velocity_score: float
    risk_score: float
    profit_per_unit: float
    estimated_time_to_sell_days: Optional[int] = None
    suggested_action: str
    next_steps: List[str]


class ProductDecisionSchema(BaseModel):
    """Complete product decision card with all analytics."""
    asin: str
    title: str
    velocity: VelocityAnalyticsSchema
    price_stability: PriceStabilitySchema
    roi: ROIAnalysisSchema
    competition: CompetitionAnalysisSchema
    risk: RiskScoreResponseSchema
    recommendation: RecommendationResponseSchema


class AnalyticsHistorySchema(BaseModel):
    """Historical analytics record."""
    id: str
    asin: str
    tracked_at: str
    price: Optional[float] = None
    bsr: Optional[int] = None
    seller_count: Optional[int] = None
    amazon_on_listing: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class RunHistorySchema(BaseModel):
    """AutoSourcing run history record."""
    id: str
    job_id: str
    total_products_discovered: int
    total_picks_generated: int
    success_rate: Optional[float] = None
    tokens_consumed: int
    execution_time_seconds: Optional[float] = None
    executed_at: str


class DecisionOutcomeSchema(BaseModel):
    """Decision outcome tracking record."""
    id: str
    asin: str
    decision: str
    predicted_roi: Optional[float] = None
    predicted_velocity: Optional[float] = None
    actual_outcome: Optional[str] = None
    actual_roi: Optional[float] = None
    time_to_sell_days: Optional[int] = None
    outcome_date: Optional[str] = None
