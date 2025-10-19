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

        # If there was an error, return early
        if 'error' in unified_product:
            logger.error(f"[PHASE4] Error in unified builder for {asin}: {unified_product['error']}")
            return AnalysisResult(
                asin=asin,
                title=keepa_data.get('title', 'Unknown'),
                current_price=None,
                current_bsr=None,
                roi={"error": unified_product['error']},
                velocity={},
                velocity_score=50,
                price_stability_score=50,
                confidence_score=10,
                overall_rating="PASS",
            )

        # Extract data from unified product for backward compatibility
        current_price_raw = unified_product.get('pricing', {}).get('current_prices', {}).get('amazon')
        if not current_price_raw:
            current_price_raw = unified_product.get('pricing', {}).get('current_prices', {}).get('used')

        # Parse Keepa data (legacy, for backward compat)
        parsed_data = parse_keepa_product(keepa_data)
        
        # Handle case where no valid price is found
        if current_price_raw is None or current_price_raw <= 0:
            return AnalysisResult(
                asin=asin,
                title=keepa_data.get('title', 'Unknown'),
                current_price=None,
                current_bsr=parsed_data.get('current_bsr'),
                roi={"error": "No valid pricing data available"},
                velocity={"error": "No pricing data for velocity analysis"},
                
                # NEW: Default values for advanced scoring
                velocity_score=50,  # Neutral fallback
                price_stability_score=50,  # Neutral fallback
                confidence_score=10,  # Low confidence due to missing data
                overall_rating="PASS",
                score_breakdown={
                    "velocity": ScoreBreakdown(score=50, raw=0.5, level="unknown", notes="No pricing data"),
                    "stability": ScoreBreakdown(score=50, raw=0.5, level="unknown", notes="No pricing data"),
                    "confidence": ScoreBreakdown(score=10, raw=0.1, level="low", notes="No pricing data")
                },
                readable_summary="❌ No valid pricing data available",
                
                # Legacy fields
                recommendation="PASS",
                risk_factors=["No valid pricing data"]
            )
        
        # Calculate ROI metrics with valid price - EXACT SAME AS DEBUG ENDPOINT
        current_price = Decimal(str(current_price_raw))

        # *** STRATEGY REFACTOR V2: Direct ROI with real Keepa prices ***
        from app.services.keepa_parser_v2 import (
            _determine_target_sell_price,
            _determine_buy_cost_used,
            _auto_select_strategy
        )

        # Feature flag: use new direct ROI or fallback to inverse formula
        use_direct_roi = config.get("feature_flags", {}).get("direct_roi_calculation", False)

        if use_direct_roi:
            # Direct ROI: Extract real Keepa prices
            sell_price_raw = _determine_target_sell_price(parsed_data)
            buy_cost_raw = _determine_buy_cost_used(parsed_data)

            # Validation: buy_cost must be less than sell_price
            if sell_price_raw and buy_cost_raw and buy_cost_raw < sell_price_raw:
                current_price = sell_price_raw  # BuyBox USED target
                estimated_cost = buy_cost_raw    # FBA USED purchase cost
                calculation_method = "direct_keepa_prices"
                logger.info(f"ASIN {asin}: Direct ROI - sell=${sell_price_raw}, buy=${buy_cost_raw}")
            else:
                # Fallback: Inverse formula if prices invalid
                logger.warning(f"ASIN {asin}: Invalid Keepa prices (sell={sell_price_raw}, buy={buy_cost_raw}), using inverse formula")
                strategy = config.get("active_strategy", "balanced")
                estimated_cost = calculate_purchase_cost_from_strategy(
                    sell_price=current_price,
                    strategy=strategy,
                    config=config
                )
                calculation_method = "inverse_formula_fallback"
        else:
            # Legacy: Use strategy-based purchase cost calculation with inverse ROI formula
            strategy = config.get("active_strategy", "balanced")
            estimated_cost = calculate_purchase_cost_from_strategy(
                sell_price=current_price,
                strategy=strategy,
                config=config
            )
            calculation_method = "inverse_formula_legacy"
        
        # Weight handling - EXACT SAME AS DEBUG ENDPOINT  
        weight_raw = parsed_data.get('weight', 1.0)
        weight_decimal = Decimal(str(weight_raw))
        
        roi_result = calculate_roi_metrics(
            current_price=current_price,
            estimated_buy_cost=estimated_cost,
            product_weight_lbs=weight_decimal,
            category="books",
            config=config
        )
        
        # Velocity calculation - EXACT SAME AS DEBUG ENDPOINT
        velocity_data = VelocityData(
            current_bsr=parsed_data.get('current_bsr'),
            bsr_history=parsed_data.get('bsr_history', []),
            price_history=parsed_data.get('price_history', []),
            buybox_history=parsed_data.get('buybox_history', []),
            offers_history=parsed_data.get('offers_history', []),
            category="books"
        )
        
        velocity_result = calculate_velocity_score(velocity_data, config=config)
        
        # *** NEW: ADVANCED SCORING SYSTEM (v1.5.0) ***
        
        # Calculate advanced scores using our new functions
        velocity_raw, velocity_normalized, velocity_level, velocity_notes = compute_advanced_velocity_score(
            parsed_data.get('bsr_history', []), config
        )
        
        stability_raw, stability_normalized, stability_level, stability_notes = compute_advanced_stability_score(
            parsed_data.get('price_history', []), config
        )
        
        # Calculate data age for confidence score
        data_age_days = 1  # Assume recent data for now
        confidence_raw, confidence_normalized, confidence_level, confidence_notes = compute_advanced_confidence_score(
            parsed_data.get('price_history', []),
            parsed_data.get('bsr_history', []),
            data_age_days,
            config
        )
        
        # Calculate overall rating
        roi_percentage = roi_result.get('roi_percentage', 0)
        overall_rating = compute_overall_rating(
            roi_percentage, velocity_normalized, stability_normalized, confidence_normalized, config
        )
        
        # Build score breakdown
        score_breakdown = {
            "velocity": ScoreBreakdown(
                score=velocity_normalized,
                raw=velocity_raw,
                level=velocity_level,
                notes=velocity_notes
            ),
            "stability": ScoreBreakdown(
                score=stability_normalized,
                raw=stability_raw,
                level=stability_level,
                notes=stability_notes
            ),
            "confidence": ScoreBreakdown(
                score=confidence_normalized,
                raw=confidence_raw,
                level=confidence_level,
                notes=confidence_notes
            )
        }
        
        # Generate readable summary
        scores_dict = {
            "velocity": velocity_normalized,
            "stability": stability_normalized,
            "confidence": confidence_normalized
        }
        readable_summary = generate_readable_summary(roi_percentage, overall_rating, scores_dict, config)

        # *** STRATEGY REFACTOR V2: Auto-select strategy profile ***
        use_strategy_profiles = config.get("feature_flags", {}).get("strategy_profiles_v2", False)
        if use_strategy_profiles:
            strategy_profile = _auto_select_strategy(parsed_data)
        else:
            strategy_profile = config.get("active_strategy", "balanced")

        # *** NEW: USED vs NEW pricing breakdown ***
        pricing_breakdown = {}

        # Extract USED and NEW prices from parsed data
        used_price = parsed_data.get('current_used_price')
        new_price = parsed_data.get('current_fbm_price')  # NEW third-party price
        target_roi = config.get('roi', {}).get('target_roi_percent', 30)

        # Calculate USED pricing (RECOMMENDED for FBA arbitrage)
        if used_price and used_price > 0:
            used_roi = calculate_roi_metrics(
                current_price=current_price,
                estimated_buy_cost=Decimal(str(used_price)),
                product_weight_lbs=weight_decimal,
                category="books",
                config=config
            )
            # Calculate target buy price for USED
            target_buy_used = float(current_price) * (1 - target_roi / 100)

            pricing_breakdown['used'] = PricingDetail(
                current_price=float(used_price),
                target_buy_price=target_buy_used,
                roi_percentage=used_roi.get('roi_percentage'),
                net_profit=used_roi.get('net_profit'),
                available=True,
                recommended=True  # USED is recommended for FBA
            )
        else:
            # USED not available - show target price only
            target_buy_used = float(current_price) * (1 - target_roi / 100)
            pricing_breakdown['used'] = PricingDetail(
                current_price=None,
                target_buy_price=target_buy_used,
                roi_percentage=None,
                net_profit=None,
                available=False,
                recommended=True
            )

        # Calculate NEW pricing (ALTERNATIVE option)
        if new_price and new_price > 0:
            new_roi = calculate_roi_metrics(
                current_price=current_price,
                estimated_buy_cost=Decimal(str(new_price)),
                product_weight_lbs=weight_decimal,
                category="books",
                config=config
            )
            # Calculate target buy price for NEW
            target_buy_new = float(current_price) * (1 - target_roi / 100)

            pricing_breakdown['new'] = PricingDetail(
                current_price=float(new_price),
                target_buy_price=target_buy_new,
                roi_percentage=new_roi.get('roi_percentage'),
                net_profit=new_roi.get('net_profit'),
                available=True,
                recommended=False  # NEW is alternative, not recommended
            )
        else:
            # NEW not available - show target price only
            target_buy_new = float(current_price) * (1 - target_roi / 100)
            pricing_breakdown['new'] = PricingDetail(
                current_price=None,
                target_buy_price=target_buy_new,
                roi_percentage=None,
                net_profit=None,
                available=False,
                recommended=False
            )

        # Legacy recommendation logic (maintained for compatibility)
        recommendation = "PASS"
        risk_factors = []

        if overall_rating == "EXCELLENT":
            recommendation = "STRONG BUY"
        elif overall_rating == "GOOD":
            recommendation = "BUY"
        elif overall_rating == "FAIR":
            recommendation = "WATCH"
            risk_factors.append("Moderate metrics")
        else:
            recommendation = "PASS"
            risk_factors.append("Below thresholds")

        return AnalysisResult(
            asin=asin,
            title=keepa_data.get('title', 'Unknown'),
            current_price=float(current_price) if current_price else None,
            current_bsr=parsed_data.get('current_bsr'),

            # NEW: USED vs NEW pricing breakdown
            pricing=pricing_breakdown,

            roi=roi_result,
            velocity=velocity_result,

            # NEW: Advanced scoring fields
            velocity_score=velocity_normalized,
            price_stability_score=stability_normalized,
            confidence_score=confidence_normalized,
            overall_rating=overall_rating,
            score_breakdown=score_breakdown,
            readable_summary=readable_summary,

            # NEW: Strategy profile (v2)
            strategy_profile=strategy_profile,
            calculation_method=calculation_method,

            # Legacy fields (maintained for compatibility)
            recommendation=recommendation,
            risk_factors=risk_factors
        )
        
    except Exception as e:
        # No logger calls that might cause issues
        return AnalysisResult(
            asin=asin,
            title=keepa_data.get('title', 'Unknown'),
            current_price=None,
            current_bsr=None,
            roi={"error": str(e)},
            velocity={"error": str(e)},
            
            # NEW: Error state for advanced scoring
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
            
            # Legacy fields
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
                    "remaining": health_status.get("tokens_left", 0),
                    "refill_in_minutes": health_status.get("refill_in_minutes", 0),
                    "total_used": keepa_service.metrics.tokens_used,
                    "requests_made": keepa_service.metrics.requests_count
                },
                "cache": {
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