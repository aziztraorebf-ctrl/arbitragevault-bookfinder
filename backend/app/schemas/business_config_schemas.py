"""
Pydantic schemas for Business Configuration API.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator, root_validator


class RoiConfigSchema(BaseModel):
    """ROI configuration parameters."""
    target_pct_default: float = Field(30.0, ge=0, le=200, description="Default ROI target percentage")
    min_for_buy: float = Field(15.0, ge=0, le=100, description="Minimum ROI for BUY recommendation")
    excellent_threshold: float = Field(50.0, ge=0, le=200, description="ROI threshold for excellent tier")
    good_threshold: float = Field(30.0, ge=0, le=200, description="ROI threshold for good tier")
    fair_threshold: float = Field(15.0, ge=0, le=200, description="ROI threshold for fair tier")


class CombinedScoreConfigSchema(BaseModel):
    """Combined score weighting configuration."""
    roi_weight: float = Field(0.6, ge=0, le=1, description="ROI weight in combined score")
    velocity_weight: float = Field(0.4, ge=0, le=1, description="Velocity weight in combined score")
    
    @validator('velocity_weight')
    def weights_must_sum_to_one(cls, v, values):
        roi_weight = values.get('roi_weight', 0.6)
        total = roi_weight + v
        if abs(total - 1.0) > 0.001:
            raise ValueError(f'Combined weights must sum to 1.0 (got {total:.3f})')
        return v


class FeeConfigItemSchema(BaseModel):
    """Fee configuration for a specific category."""
    referral_fee_pct: float = Field(15.0, ge=0, le=50, description="Referral fee percentage")
    closing_fee: float = Field(1.80, ge=0, le=10, description="Fixed closing fee")
    fba_fee_base: float = Field(2.50, ge=0, le=20, description="Base FBA fee")
    fba_fee_per_lb: float = Field(0.40, ge=0, le=5, description="FBA fee per pound")
    inbound_shipping: float = Field(0.40, ge=0, le=5, description="Inbound shipping cost")
    prep_fee: float = Field(0.20, ge=0, le=5, description="Prep fee per item")


class FeesConfigSchema(BaseModel):
    """Fees configuration with category-specific settings."""
    buffer_pct_default: float = Field(5.0, ge=0, le=50, description="Safety buffer percentage")
    books: Optional[FeeConfigItemSchema] = None
    media: Optional[FeeConfigItemSchema] = None
    default: Optional[FeeConfigItemSchema] = None


class VelocityConfigSchema(BaseModel):
    """Velocity scoring configuration."""
    fast_threshold: float = Field(80.0, ge=0, le=100, description="Threshold for fast velocity tier")
    medium_threshold: float = Field(60.0, ge=0, le=100, description="Threshold for medium velocity tier")
    slow_threshold: float = Field(40.0, ge=0, le=100, description="Threshold for slow velocity tier")
    benchmarks: Optional[Dict[str, int]] = Field(None, description="BSR benchmarks by category")
    
    @root_validator
    def thresholds_must_be_ordered(cls, values):
        fast = values.get('fast_threshold', 80.0)
        medium = values.get('medium_threshold', 60.0)
        slow = values.get('slow_threshold', 40.0)
        
        if not (fast >= medium >= slow):
            raise ValueError('Velocity thresholds must be ordered: fast >= medium >= slow')
        return values


class RecommendationRuleSchema(BaseModel):
    """Single recommendation rule."""
    label: str = Field(..., description="Recommendation label (STRONG BUY, BUY, etc.)")
    min_roi: float = Field(0.0, ge=0, le=200, description="Minimum ROI for this recommendation")
    min_velocity: float = Field(0.0, ge=0, le=100, description="Minimum velocity for this recommendation")
    description: Optional[str] = Field(None, description="Human-readable description")


class MetaConfigSchema(BaseModel):
    """Configuration metadata."""
    version: Optional[str] = Field(None, description="Configuration version")
    created_by: Optional[str] = Field(None, description="Configuration creator")
    description: Optional[str] = Field(None, description="Configuration description")


class BusinessConfigSchema(BaseModel):
    """Complete business configuration schema."""
    roi: Optional[RoiConfigSchema] = None
    combined_score: Optional[CombinedScoreConfigSchema] = None
    fees: Optional[FeesConfigSchema] = None
    velocity: Optional[VelocityConfigSchema] = None
    recommendation_rules: Optional[List[RecommendationRuleSchema]] = None
    demo_asins: Optional[List[str]] = Field(None, description="Demo ASINs for preview testing")
    meta: Optional[MetaConfigSchema] = None
    
    class Config:
        extra = "allow"  # Allow additional fields for flexibility


class ConfigUpdateRequest(BaseModel):
    """Request schema for config updates."""
    config_patch: BusinessConfigSchema = Field(..., description="Configuration changes to apply")
    change_reason: Optional[str] = Field(None, description="Reason for configuration change")
    if_match_version: Optional[int] = Field(None, description="Expected version for optimistic locking")


class ConfigPreviewRequest(BaseModel):
    """Request schema for config preview (dry-run)."""
    config_patch: BusinessConfigSchema = Field(..., description="Configuration to preview")
    domain_id: int = Field(1, description="Domain ID for preview context")
    category: str = Field("books", description="Category for preview context")


class PreviewResult(BaseModel):
    """Single ASIN preview result."""
    asin: str = Field(..., description="Product ASIN")
    title: Optional[str] = Field(None, description="Product title")
    
    # Before/after comparison
    before: Dict[str, Any] = Field(..., description="Metrics with current config")
    after: Dict[str, Any] = Field(..., description="Metrics with new config")
    
    # Key changes
    changes: Dict[str, Any] = Field(..., description="Summary of key changes")


class ConfigPreviewResponse(BaseModel):
    """Response schema for config preview."""
    preview_results: List[PreviewResult] = Field(..., description="Preview results for demo ASINs")
    config_summary: Dict[str, Any] = Field(..., description="Summary of configuration changes")
    validation_warnings: List[str] = Field([], description="Validation warnings (non-blocking)")
    generated_at: datetime = Field(default_factory=datetime.now, description="Preview generation timestamp")


class BusinessConfigResponse(BaseModel):
    """Response schema for config retrieval."""
    scope: str = Field(..., description="Configuration scope")
    config: BusinessConfigSchema = Field(..., description="Configuration data")
    version: int = Field(..., description="Configuration version")
    effective_config: Optional[BusinessConfigSchema] = Field(None, description="Effective merged config")
    sources: Optional[Dict[str, bool]] = Field(None, description="Config source flags")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ConfigChangeResponse(BaseModel):
    """Response schema for config changes (audit trail)."""
    change_id: str = Field(..., description="Unique change ID")
    config_scope: str = Field(..., description="Scope that was changed")
    changed_by: str = Field(..., description="User who made the change")
    change_reason: Optional[str] = Field(None, description="Reason for change")
    change_source: str = Field(..., description="Source of change (api, system, etc.)")
    
    # Version info
    old_version: Optional[int] = Field(None, description="Previous version")
    new_version: int = Field(..., description="New version after change")
    
    # Change details
    diff_summary: str = Field(..., description="Human-readable change summary")
    diff_jsonpatch: List[Dict[str, Any]] = Field(..., description="JSONPatch diff")
    
    # Timestamps
    changed_at: datetime = Field(..., description="When change was made")


class ConfigStatsResponse(BaseModel):
    """Response schema for config service statistics."""
    cache_stats: Dict[str, Any] = Field(..., description="Cache performance statistics")
    total_configs: int = Field(..., description="Total number of configurations")
    active_configs: int = Field(..., description="Number of active configurations")
    recent_changes: int = Field(..., description="Number of recent changes")
    service_health: str = Field(..., description="Service health status")


# Error response schemas
class ConfigErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class ValidationErrorResponse(BaseModel):
    """Validation error response schema."""
    error: str = "Validation failed"
    validation_errors: List[str] = Field(..., description="List of validation error messages")
    invalid_fields: Optional[Dict[str, str]] = Field(None, description="Field-specific errors")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")