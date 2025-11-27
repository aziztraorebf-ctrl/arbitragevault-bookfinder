"""
Keepa Router - Pydantic Schemas
===============================
Request/Response schemas for Keepa API endpoints.

Separated from keepa.py for SRP compliance.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field, validator


class IngestBatchRequest(BaseModel):
    """Request for batch ingestion of identifiers."""
    identifiers: List[str] = Field(..., min_items=1, max_items=1000, description="List of ASINs/ISBNs")
    batch_id: Optional[str] = Field(None, description="Optional batch ID for idempotency")
    config_profile: str = Field("default", description="Configuration profile to use")
    force_refresh: bool = Field(False, description="Force refresh cached data")
    async_threshold: int = Field(100, description="Use async job mode if > this many items")
    source_price: Optional[float] = Field(None, description="Acquisition cost per item (used for ROI calculation). If not provided, uses config default.")

    @validator('identifiers')
    def validate_identifiers(cls, v):
        """Basic validation of identifier format."""
        cleaned = []
        for identifier in v:
            clean_id = identifier.strip().replace("-", "").replace(" ", "")
            if len(clean_id) not in [10, 13]:
                raise ValueError(f"Invalid identifier format: {identifier}")
            cleaned.append(clean_id)
        return cleaned


class ConfigAudit(BaseModel):
    """Configuration audit information."""
    version: str
    hash: str
    profile: str
    effective_at: datetime
    changes_applied: List[Dict[str, Any]] = []


class KeepaMetadata(BaseModel):
    """Keepa API metadata."""
    snapshot_at: datetime
    cache_hit: bool
    tokens_used: int
    tokens_remaining: Optional[int]
    data_freshness_hours: Optional[float]


class ScoreBreakdown(BaseModel):
    """Breakdown of individual score calculation."""
    score: int
    raw: float
    level: str
    notes: str


class PricingDetail(BaseModel):
    """Pricing details for a specific condition (NEW or USED)."""
    current_price: Optional[float] = Field(None, description="Current market price for this condition")
    target_buy_price: float = Field(..., description="Target buy price for desired ROI")
    roi_percentage: Optional[float] = Field(None, description="ROI if bought at current price")
    net_profit: Optional[float] = Field(None, description="Net profit if bought at current price")
    available: bool = Field(..., description="Whether this condition is currently available")
    recommended: bool = Field(..., description="Whether this is the recommended buying option")


class AnalysisResult(BaseModel):
    """Complete analysis result for a product."""
    asin: str
    title: Optional[str]
    current_price: Optional[float] = Field(None, description="Current price from Keepa")
    current_bsr: Optional[int] = Field(None, description="Current sales rank")

    # NEW: Pricing breakdown USED vs NEW
    pricing: Dict[str, PricingDetail] = Field(
        default={},
        description="Separated pricing for 'used' and 'new' conditions"
    )
    roi: Dict[str, Any]
    velocity: Dict[str, Any]

    # NEW: Advanced Scoring (0-100 scale)
    velocity_score: int = Field(..., ge=0, le=100, description="Velocity score 0-100")
    price_stability_score: int = Field(..., ge=0, le=100, description="Price stability score 0-100")
    confidence_score: int = Field(..., ge=0, le=100, description="Data confidence score 0-100")
    overall_rating: str = Field(..., description="EXCELLENT/GOOD/FAIR/PASS")

    # Score breakdown and summary
    score_breakdown: Dict[str, ScoreBreakdown] = Field(..., description="Detailed score breakdown")
    readable_summary: str = Field(..., description="Human-readable summary")

    # NEW: Strategy Refactor V2 fields
    strategy_profile: Optional[str] = Field(None, description="Auto-selected strategy: textbook/velocity/balanced")
    calculation_method: Optional[str] = Field(None, description="ROI calculation method: direct_keepa_prices/inverse_formula_fallback/inverse_formula_legacy")

    # Legacy fields (maintained for compatibility)
    recommendation: str
    risk_factors: List[str]


class MetricsResponse(BaseModel):
    """Response for product metrics endpoint."""
    asin: str
    analysis: AnalysisResult
    config_audit: ConfigAudit
    keepa_metadata: KeepaMetadata
    trace_id: str


class BatchResult(BaseModel):
    """Result for a single item in batch processing."""
    identifier: str
    asin: Optional[str]
    status: str  # "success", "error", "not_found"
    analysis: Optional[AnalysisResult]
    error: Optional[str]


class IngestResponse(BaseModel):
    """Response for batch ingestion."""
    batch_id: str
    total_items: int
    processed: int
    successful: int
    failed: int
    results: List[BatchResult]
    job_id: Optional[str] = None  # Set if async mode
    status_url: Optional[str] = None  # Set if async mode
    trace_id: str


class StandardError(BaseModel):
    """Standard error format."""
    code: str
    message: str
    details: Dict[str, Any] = {}
    trace_id: str


__all__ = [
    'IngestBatchRequest',
    'ConfigAudit',
    'KeepaMetadata',
    'ScoreBreakdown',
    'PricingDetail',
    'AnalysisResult',
    'MetricsResponse',
    'BatchResult',
    'IngestResponse',
    'StandardError',
]
