"""Keepa integration endpoints - Phase 4 complete implementation."""

import asyncio
import uuid
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field

from fastapi import APIRouter, Query, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field, validator

from app.services.keepa_service import KeepaService, get_keepa_service
from app.services.business_config_service import BusinessConfigService, get_business_config_service
from app.services.keepa_parser_v2 import parse_keepa_product
from app.services.unified_analysis import build_unified_product_v2  # Phase 4
from app.core.calculations import (
    calculate_roi_metrics, calculate_velocity_score, VelocityData,
    compute_advanced_velocity_score, compute_advanced_stability_score,
    compute_advanced_confidence_score, compute_overall_rating,
    generate_readable_summary, calculate_purchase_cost_from_strategy
)

router = APIRouter()
logger = logging.getLogger(__name__)

# === PYDANTIC SCHEMAS ===

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

# === UTILITY FUNCTIONS ===

def generate_trace_id() -> str:
    """Generate unique trace ID."""
    return uuid.uuid4().hex[:8]

def normalize_identifier(identifier: str) -> str:
    """Normalize ASIN/ISBN format."""
    return identifier.strip().replace("-", "").replace(" ", "").upper()

async def analyze_product(
    asin: str,
    keepa_data: Dict[str, Any],
    config: Dict[str, Any],
    keepa_service: KeepaService,
    source_price: Optional[float] = None  # Phase 4: Add source_price parameter
) -> AnalysisResult:
    """
    Analyze a single product with given config.
    *** PHASE 4: Uses build_unified_product_v2() for unified pricing extraction ***

    Args:
        asin: Product ASIN
        keepa_data: Raw Keepa API response
        config: Business configuration
        keepa_service: Keepa service instance
        source_price: Optional source/acquisition price override
    """
    try:
        # ====== PHASE 4: Use build_unified_product_v2() ======
        unified_product = await build_unified_product_v2(
            raw_keepa=keepa_data,
            keepa_service=keepa_service,
            config=config,
            view_type='analyse_manuelle',
            compute_score=False,
            source_price=source_price
        )

        # ====== PHASE 4: Map unified_product directly to AnalysisResult ======
        # build_unified_product_v2() now returns ALL required fields

        # Convert pricing structure to match AnalysisResult schema
        pricing_unified = unified_product.get('pricing', {})
        pricing_by_condition = pricing_unified.get('by_condition', {})

        # Map to PricingDetail format expected by AnalysisResult
        pricing_breakdown = {}
        for condition, details in pricing_by_condition.items():
            pricing_breakdown[condition] = PricingDetail(
                current_price=details.get('buy_price'),  # Current market buy price
                target_buy_price=details.get('max_buy_price', 0),
                roi_percentage=details.get('roi_pct', 0) * 100 if details.get('roi_pct') else None,
                net_profit=details.get('profit'),
                available=details.get('buy_price') is not None,
                recommended=details.get('is_recommended', False)
            )

        # Convert score_breakdown dict to ScoreBreakdown objects
        score_breakdown_raw = unified_product.get('score_breakdown', {})
        score_breakdown_typed = {}
        for key, breakdown in score_breakdown_raw.items():
            score_breakdown_typed[key] = ScoreBreakdown(
                score=breakdown.get('score', 0),
                raw=breakdown.get('raw', 0.0),
                level=breakdown.get('level', 'unknown'),
                notes=breakdown.get('notes', '')
            )

        # Extract current price from unified pricing
        current_price_raw = pricing_unified.get('current_prices', {}).get('amazon')
        if not current_price_raw:
            current_price_raw = pricing_unified.get('current_prices', {}).get('used')

        return AnalysisResult(
            asin=asin,
            title=unified_product.get('title'),
            current_price=current_price_raw,
            current_bsr=unified_product.get('current_bsr'),

            # Pricing breakdown
            pricing=pricing_breakdown,

            # ROI and velocity (legacy format for compatibility)
            roi=unified_product.get('velocity', {}),  # Velocity metrics contain ROI data
            velocity=unified_product.get('velocity', {}),

            # Advanced scoring (0-100 scale)
            velocity_score=unified_product.get('velocity_score', 0),
            price_stability_score=unified_product.get('price_stability_score', 0),
            confidence_score=unified_product.get('confidence_score', 0),
            overall_rating=unified_product.get('overall_rating', 'PASS'),
            score_breakdown=score_breakdown_typed,
            readable_summary=unified_product.get('readable_summary', ''),

            # Strategy profile
            strategy_profile=unified_product.get('strategy_profile'),
            calculation_method=None,  # Not used in unified builder

            # Recommendation and risk factors
            recommendation=unified_product.get('recommendation', 'PASS'),
            risk_factors=unified_product.get('risk_factors', [])
        )

    except Exception as e:
        # Error handling with complete AnalysisResult structure
        logger.error(f"[PHASE4] Error analyzing {asin}: {str(e)}", exc_info=True)
        return AnalysisResult(
            asin=asin,
            title=None,
            current_price=None,
            current_bsr=None,

            # Empty pricing
            pricing={},

            roi={"error": str(e)},
            velocity={"error": str(e)},

            # Error state for advanced scoring
            velocity_score=0,
            price_stability_score=0,
            confidence_score=0,
            overall_rating="ERROR",
            score_breakdown={
                "velocity": ScoreBreakdown(score=0, raw=0.0, level="error", notes=f"Analysis failed: {str(e)}"),
                "stability": ScoreBreakdown(score=0, raw=0.0, level="error", notes=f"Analysis failed: {str(e)}"),
                "confidence": ScoreBreakdown(score=0, raw=0.0, level="error", notes=f"Analysis failed: {str(e)}")
            },
            readable_summary=f"❌ Analysis failed: {str(e)}",

            # Strategy and recommendation
            strategy_profile=None,
            calculation_method=None,
            recommendation="ERROR",
            risk_factors=["Analysis failed"]
        )

# === ENDPOINTS ===

@router.post("/ingest", response_model=IngestResponse)
async def ingest_batch(
    http_request: Request,
    request: IngestBatchRequest,
    background_tasks: BackgroundTasks,
    keepa_service: KeepaService = Depends(get_keepa_service),
    config_service: BusinessConfigService = Depends(get_business_config_service)
) -> IngestResponse:
    """
    Ingest batch of identifiers for analysis.
    Supports both sync and async processing based on batch size.
    """
    trace_id = generate_trace_id()
    batch_id = request.batch_id or str(uuid.uuid4())

    logger.info(f"[{trace_id}] Starting batch ingestion", extra={
        "batch_id": batch_id,
        "count": len(request.identifiers),
        "profile": request.config_profile
    })

    try:
        # Get effective configuration
        config = await config_service.get_effective_config(
            domain_id=1,  # Default US domain
            category="books"
        )

        # ✨ DEV/TEST ONLY: Feature flags override via header
        if "X-Feature-Flags-Override" in http_request.headers:
            import json
            try:
                override_flags = json.loads(http_request.headers["X-Feature-Flags-Override"])
                if not config.get("feature_flags"):
                    config["feature_flags"] = {}
                config["feature_flags"].update(override_flags)
                logger.info(f"[DEV] Feature flags overridden: {override_flags}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"[DEV] Invalid feature flags override header: {e}")
        
        # Check if async mode needed
        if len(request.identifiers) > request.async_threshold:
            job_id = str(uuid.uuid4())
            
            # Start background job
            background_tasks.add_task(
                process_batch_async,
                job_id,
                request.identifiers,
                config,
                batch_id,
                trace_id,
                keepa_service
            )
            
            return IngestResponse(
                batch_id=batch_id,
                total_items=len(request.identifiers),
                processed=0,
                successful=0,
                failed=0,
                results=[],
                job_id=job_id,
                status_url=f"/api/v1/keepa/jobs/{job_id}",
                trace_id=trace_id
            )
        
        # Sync processing
        results = []
        successful = 0
        failed = 0
        
        async with keepa_service:
            for identifier in request.identifiers:
                try:
                    normalized_id = normalize_identifier(identifier)
                    
                    # Get product data
                    keepa_data = await keepa_service.get_product_data(
                        normalized_id,
                        force_refresh=request.force_refresh
                    )
                    
                    if keepa_data is None:
                        results.append(BatchResult(
                            identifier=identifier,
                            asin=None,
                            status="not_found",
                            analysis=None,
                            error="Product not found in Keepa"
                        ))
                        failed += 1
                        continue
                    
                    asin = keepa_data.get('asin', normalized_id)

                    # Analyze product with optional source_price override
                    analysis = await analyze_product(
                        asin,
                        keepa_data,
                        config,
                        keepa_service,
                        source_price=request.source_price  # Pass from request
                    )

                    # ✨ DEV/TEST ONLY: Validation logging if feature flags overridden
                    if "X-Feature-Flags-Override" in http_request.headers:
                        logger.info(
                            f"[VALIDATION] ASIN={asin} | "
                            f"strategy={analysis.strategy_profile} | "
                            f"method={analysis.calculation_method} | "
                            f"roi={analysis.roi.get('roi_percentage', 0):.1f}% | "
                            f"buy=${analysis.roi.get('buy_cost', 'N/A')} | "
                            f"sell=${analysis.current_price}"
                        )

                    results.append(BatchResult(
                        identifier=identifier,
                        asin=asin,
                        status="success",
                        analysis=analysis,
                        error=None
                    ))
                    successful += 1
                    
                except Exception as e:
                    logger.error(f"[{trace_id}] Failed processing {identifier}: {e}")
                    results.append(BatchResult(
                        identifier=identifier,
                        asin=None,
                        status="error",
                        analysis=None,
                        error=str(e)
                    ))
                    failed += 1
        
        return IngestResponse(
            batch_id=batch_id,
            total_items=len(request.identifiers),
            processed=len(results),
            successful=successful,
            failed=failed,
            results=results,
            trace_id=trace_id
        )
        
    except Exception as e:
        logger.error(f"[{trace_id}] Batch ingestion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BATCH_PROCESSING_FAILED",
                "message": "Failed to process batch",
                "details": {"error": str(e)},
                "trace_id": trace_id
            }
        )


@router.get("/{asin}/metrics", response_model=MetricsResponse)
async def get_product_metrics(
    asin: str,
    config_profile: str = Query("default", description="Configuration profile"),
    force_refresh: bool = Query(False, description="Force refresh cached data"),
    keepa_service: KeepaService = Depends(get_keepa_service),
    config_service: BusinessConfigService = Depends(get_business_config_service)
) -> MetricsResponse:
    """
    Get complete analysis metrics for a product.
    Includes ROI, velocity, configuration audit, and Keepa metadata.
    """
    trace_id = generate_trace_id()
    asin = normalize_identifier(asin)
    
    logger.info(f"[{trace_id}] Getting metrics for {asin}")
    
    try:
        # Get effective configuration
        config = await config_service.get_effective_config(
            domain_id=1,
            category="books"
        )
        
        # Get Keepa data
        async with keepa_service:
            keepa_data = await keepa_service.get_product_data(asin, force_refresh=force_refresh)
            
            if keepa_data is None:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "code": "PRODUCT_NOT_FOUND",
                        "message": f"Product {asin} not found in Keepa",
                        "trace_id": trace_id
                    }
                )
            
            # Analyze product
            analysis = await analyze_product(asin, keepa_data, config, keepa_service)
            
            # Build audit info
            config_audit = ConfigAudit(
                version=config.get('_meta', {}).get('version', '1.0'),
                hash=str(hash(str(sorted(config.items())))),
                profile=config_profile,
                effective_at=datetime.now(),
                changes_applied=[]
            )
            
            # Build Keepa metadata
            cache_stats = keepa_service.get_cache_stats()
            keepa_metadata = KeepaMetadata(
                snapshot_at=datetime.now(),
                cache_hit=bool(cache_stats.get('hits', 0) > 0),
                tokens_used=keepa_service.metrics.tokens_used,
                tokens_remaining=keepa_service.metrics.tokens_remaining,
                data_freshness_hours=1.0  # Estimate based on cache TTL
            )
            
            return MetricsResponse(
                asin=asin,
                analysis=analysis,
                config_audit=config_audit,
                keepa_metadata=keepa_metadata,
                trace_id=trace_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{trace_id}] Metrics retrieval failed for {asin}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "METRICS_RETRIEVAL_FAILED",
                "message": "Failed to retrieve product metrics",
                "details": {"asin": asin, "error": str(e)},
                "trace_id": trace_id
            }
        )


@router.get("/{asin}/raw", response_model=Dict[str, Any])
async def get_raw_keepa_data(
    asin: str,
    force_refresh: bool = Query(False, description="Force refresh cached data"),
    keepa_service: KeepaService = Depends(get_keepa_service)
) -> Dict[str, Any]:
    """
    Get raw Keepa data for debugging and transparency.
    Returns unprocessed data directly from Keepa API.
    """
    trace_id = generate_trace_id()
    asin = normalize_identifier(asin)
    
    logger.info(f"[{trace_id}] Getting raw data for {asin}")
    
    try:
        async with keepa_service:
            keepa_data = await keepa_service.get_product_data(asin, force_refresh=force_refresh)
            
            if keepa_data is None:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "code": "PRODUCT_NOT_FOUND",
                        "message": f"Product {asin} not found in Keepa",
                        "trace_id": trace_id
                    }
                )
            
            # Add metadata to raw response
            cache_stats = keepa_service.get_cache_stats()
            
            return {
                "_metadata": {
                    "asin": asin,
                    "retrieved_at": datetime.now().isoformat(),
                    "cache_hit": bool(cache_stats.get('hits', 0) > 0),
                    "tokens_remaining": keepa_service.metrics.tokens_remaining,
                    "trace_id": trace_id
                },
                "keepa_data": keepa_data
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{trace_id}] Raw data retrieval failed for {asin}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "RAW_DATA_RETRIEVAL_FAILED",
                "message": "Failed to retrieve raw Keepa data",
                "details": {"asin": asin, "error": str(e)},
                "trace_id": trace_id
            }
        )


# === DEBUG ENDPOINTS ===

@router.post("/debug-analyze")
async def debug_analyze_endpoint(
    asin: str = "B00FLIJJSA",
    keepa_service: KeepaService = Depends(get_keepa_service),
    config_service: BusinessConfigService = Depends(get_business_config_service)
) -> Dict[str, Any]:
    """
    DEBUG ENDPOINT: Trace every step of analyze_product to find the exact error.
    """
    import traceback
    from decimal import Decimal
    
    debug_trace = []
    
    try:
        debug_trace.append("=== STEP 1: Getting config ===")
        
        try:
            config = await config_service.get_effective_config(domain_id=1, category="books")
            debug_trace.append(f"✅ Config loaded: {type(config)}")
        except Exception as e:
            config = {"roi": {"target_roi_percent": 30}, "velocity": {"min_velocity_score": 50}}
            debug_trace.append(f"⚠️ Config fallback: {e}")
        
        debug_trace.append("=== STEP 2: Getting Keepa data ===")
        
        async with keepa_service:
            keepa_data = await keepa_service.get_product_data(asin, force_refresh=False)
            
            if not keepa_data:
                return {"error": "No Keepa data", "debug_trace": debug_trace}
            
            debug_trace.append(f"✅ Keepa data: {len(keepa_data)} keys")
            
            debug_trace.append("=== STEP 3: Parsing Keepa data ===")
            
            parsed_data = parse_keepa_product(keepa_data)
            debug_trace.append(f"✅ Parsing complete: {type(parsed_data)}")
            
            # CRITICAL: Examine current_price at this exact moment
            current_price_raw = parsed_data.get('current_price')
            debug_trace.append(f"🔍 current_price_raw: {repr(current_price_raw)} (type: {type(current_price_raw)})")
            
            if hasattr(current_price_raw, '__len__') and not isinstance(current_price_raw, str):
                debug_trace.append(f"🚨 current_price_raw has length: {len(current_price_raw)}")
                if hasattr(current_price_raw, '__getitem__'):
                    debug_trace.append(f"🔍 current_price_raw content: {list(current_price_raw) if len(current_price_raw) < 10 else 'too long'}")
            
            debug_trace.append("=== STEP 4: Price validation ===")
            
            if current_price_raw is None:
                return {"error": "current_price is None", "debug_trace": debug_trace}
            elif current_price_raw <= 0:
                return {"error": "current_price <= 0", "debug_trace": debug_trace}
            
            debug_trace.append("=== STEP 5: Decimal conversion ===")
            
            try:
                current_price = Decimal(str(current_price_raw))
                debug_trace.append(f"✅ Decimal conversion: {current_price} (type: {type(current_price)})")
            except Exception as decimal_error:
                debug_trace.append(f"❌ Decimal conversion failed: {decimal_error}")
                debug_trace.append(f"🔍 str(current_price_raw): {repr(str(current_price_raw))}")
                return {
                    "error": f"Decimal conversion failed: {decimal_error}",
                    "debug_trace": debug_trace,
                    "stack_trace": traceback.format_exc()
                }
            
            debug_trace.append("=== STEP 6: Estimated cost calculation ===")
            
            try:
                estimated_cost = current_price * Decimal('0.75')
                debug_trace.append(f"✅ Estimated cost: {estimated_cost}")
            except Exception as mult_error:
                debug_trace.append(f"❌ MULTIPLICATION ERROR FOUND: {mult_error}")
                debug_trace.append(f"🔍 current_price type at multiplication: {type(current_price)}")
                debug_trace.append(f"🔍 current_price value at multiplication: {repr(current_price)}")
                return {
                    "error": f"Multiplication failed: {mult_error}",
                    "debug_trace": debug_trace,
                    "stack_trace": traceback.format_exc()
                }
            
            debug_trace.append("=== STEP 7: Weight handling ===")
            
            weight_raw = parsed_data.get('weight', 1.0)
            debug_trace.append(f"🔍 weight_raw: {repr(weight_raw)} (type: {type(weight_raw)})")
            
            try:
                weight_decimal = Decimal(str(weight_raw))
                debug_trace.append(f"✅ Weight decimal: {weight_decimal}")
            except Exception as weight_error:
                debug_trace.append(f"❌ Weight conversion failed: {weight_error}")
                return {
                    "error": f"Weight conversion failed: {weight_error}",
                    "debug_trace": debug_trace,
                    "stack_trace": traceback.format_exc()
                }
            
            debug_trace.append("=== STEP 8: ROI calculation ===")
            
            try:
                roi_result = calculate_roi_metrics(
                    current_price=current_price,
                    estimated_buy_cost=estimated_cost,
                    product_weight_lbs=weight_decimal,
                    category="books",
                    config=config
                )
                debug_trace.append(f"✅ ROI calculation success: {type(roi_result)}")
            except Exception as roi_error:
                debug_trace.append(f"❌ ROI CALCULATION ERROR: {roi_error}")
                debug_trace.append(f"🔍 Parameters passed to ROI:")
                debug_trace.append(f"  current_price: {repr(current_price)} ({type(current_price)})")
                debug_trace.append(f"  estimated_buy_cost: {repr(estimated_cost)} ({type(estimated_cost)})")
                debug_trace.append(f"  weight_decimal: {repr(weight_decimal)} ({type(weight_decimal)})")
                debug_trace.append(f"  config: {type(config)}")
                return {
                    "error": f"ROI calculation failed: {roi_error}",
                    "debug_trace": debug_trace,
                    "stack_trace": traceback.format_exc()
                }
            
            debug_trace.append("=== STEP 9: Velocity data preparation ===")
            
            try:
                velocity_data = VelocityData(
                    current_bsr=parsed_data.get('current_bsr'),
                    bsr_history=parsed_data.get('bsr_history', []),
                    price_history=parsed_data.get('price_history', []),
                    buybox_history=parsed_data.get('buybox_history', []),
                    offers_history=parsed_data.get('offers_history', []),
                    category="books"
                )
                debug_trace.append(f"✅ VelocityData created: {type(velocity_data)}")
            except Exception as vel_data_error:
                debug_trace.append(f"❌ VelocityData creation failed: {vel_data_error}")
                return {
                    "error": f"VelocityData creation failed: {vel_data_error}",
                    "debug_trace": debug_trace,
                    "stack_trace": traceback.format_exc()
                }
            
            debug_trace.append("=== STEP 10: Velocity calculation ===")
            
            try:
                velocity_result = calculate_velocity_score(velocity_data, config=config)
                debug_trace.append(f"✅ Velocity calculation success: {type(velocity_result)}")
            except Exception as vel_calc_error:
                debug_trace.append(f"❌ VELOCITY CALCULATION ERROR: {vel_calc_error}")
                return {
                    "error": f"Velocity calculation failed: {vel_calc_error}",
                    "debug_trace": debug_trace,
                    "stack_trace": traceback.format_exc()
                }
            
            debug_trace.append("=== SUCCESS: All steps completed ===")
            
            return {
                "success": True,
                "asin": asin,
                "current_price": float(current_price),
                "roi_summary": roi_result.get('roi_percentage', 'unknown'),
                "velocity_summary": velocity_result.get('velocity_score', 'unknown'),
                "debug_trace": debug_trace
            }
            
    except Exception as e:
        debug_trace.append(f"❌ UNEXPECTED ERROR: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "debug_trace": debug_trace,
            "stack_trace": traceback.format_exc()
        }


# === BACKGROUND TASKS ===

async def process_batch_async(
    job_id: str,
    identifiers: List[str],
    config: Dict[str, Any],
    batch_id: str,
    trace_id: str,
    keepa_service: KeepaService
):
    """Process large batch asynchronously."""
    logger.info(f"[{trace_id}] Starting async batch processing", extra={
        "job_id": job_id,
        "batch_id": batch_id,
        "count": len(identifiers)
    })
    
    # TODO: Implement async job processing with database persistence
    # For now, this is a placeholder for the async workflow
    
    try:
        # Process identifiers in chunks
        chunk_size = 10
        for i in range(0, len(identifiers), chunk_size):
            chunk = identifiers[i:i + chunk_size]
            
            async with keepa_service:
                for identifier in chunk:
                    try:
                        normalized_id = normalize_identifier(identifier)
                        keepa_data = await keepa_service.get_product_data(normalized_id)
                        
                        if keepa_data:
                            # Analyze and store result
                            # TODO: Store in database with job_id reference
                            pass
                            
                    except Exception as e:
                        logger.error(f"[{trace_id}] Async processing failed for {identifier}: {e}")
            
            # Small delay between chunks to be API-friendly
            await asyncio.sleep(1)
    
    except Exception as e:
        logger.error(f"[{trace_id}] Async batch processing failed: {e}")
        # TODO: Update job status in database


@router.get("/health")
async def keepa_health_check(
    keepa_service: KeepaService = Depends(get_keepa_service)
) -> Dict[str, Any]:
    """
    Enhanced health check with observability metrics.
    Includes token status, cache performance, and service metrics.
    """
    try:
        async with keepa_service:
            health_status = await keepa_service.health_check()
            cache_stats = keepa_service.get_cache_stats()
            
            # Calculate cache hit rate
            total_requests = cache_stats.get('hits', 0) + cache_stats.get('misses', 0)
            hit_rate = (cache_stats.get('hits', 0) / max(total_requests, 1)) * 100
            
            return {
                "service": "keepa",
                "timestamp": datetime.now().isoformat(),
                "status": health_status.get("status", "unknown"),
                "tokens": {
                    "remaining": health_status.get("api_tokens_left", 0),
                    "refill_in_minutes": health_status.get("refill_in_minutes", 0),
                    "total_used": keepa_service.metrics.tokens_used,
                    "requests_made": keepa_service.metrics.requests_count
                },
                "cache": {
                    "hit_rate": round(hit_rate, 2),  # Ajouté pour rétrocompatibilité
                    "hit_rate_percent": round(hit_rate, 2),
                    "total_entries": len(keepa_service._cache),
                    "hits": cache_stats.get('hits', 0),
                    "misses": cache_stats.get('misses', 0)
                },
                "circuit_breaker": {
                    "state": health_status.get("circuit_breaker_state", "unknown"),
                    "failure_count": getattr(keepa_service._circuit_breaker, 'failure_count', 0)
                },
                "performance": {
                    "concurrency_limit": keepa_service.concurrency,
                    "average_latency_ms": 0  # TODO: Track latencies
                }
            }
    
    except Exception as e:
        return {
            "service": "keepa",
            "timestamp": datetime.now().isoformat(),
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/test")
async def test_keepa_connection(
    identifier: str = Query(..., description="ASIN or ISBN to test with Keepa API"),
    keepa_service: KeepaService = Depends(get_keepa_service)
) -> Dict[str, Any]:
    """
    Test Keepa API connection with given identifier.
    Enhanced for Phase 4 with better error handling and tracing.
    """
    trace_id = generate_trace_id()
    cleaned_id = normalize_identifier(identifier)
    
    # Validate identifier format
    if not (len(cleaned_id) in [10, 13] or (len(cleaned_id) == 10 and cleaned_id.isalnum())):
        return {
            "success": False,
            "error": "Invalid ASIN/ISBN format",
            "identifier": identifier,
            "trace_id": trace_id
        }
    
    try:
        async with keepa_service:
            # Test actual Keepa API call
            product_data = await keepa_service.get_product_data(cleaned_id)
            
            if product_data is None:
                return {
                    "success": False,
                    "error": "Product not found in Keepa",
                    "identifier": cleaned_id,
                    "trace_id": trace_id
                }
            
            # Extract info for test response
            asin = product_data.get('asin', 'unknown')
            title = product_data.get('title', 'Unknown Title')
            
            return {
                "success": True,
                "identifier": cleaned_id,
                "resolved_asin": asin,
                "title": title,
                "message": "Keepa API connection successful",
                "phase": "PHASE_4_COMPLETE",
                "has_price_data": 'csv' in product_data,
                "has_stats": 'stats' in product_data,
                "tokens_remaining": keepa_service.metrics.tokens_remaining,
                "trace_id": trace_id
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Keepa API error: {str(e)}",
            "identifier": cleaned_id,
            "trace_id": trace_id
        }