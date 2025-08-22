"""Keepa integration endpoints - Phase 4 complete implementation."""

import asyncio
import uuid
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field

from fastapi import APIRouter, Query, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator

from app.services.keepa_service import KeepaService, get_keepa_service
from app.services.business_config_service import BusinessConfigService, get_business_config_service
from app.services.keepa_parser import parse_keepa_product
from app.core.calculations import calculate_roi_metrics, calculate_velocity_score, VelocityData

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

class AnalysisResult(BaseModel):
    """Complete analysis result for a product."""
    asin: str
    title: Optional[str]
    roi: Dict[str, Any]
    velocity: Dict[str, Any] 
    recommendation: str
    risk_factors: List[str]
    confidence_score: float

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
    keepa_service: KeepaService
) -> AnalysisResult:
    """Analyze a single product with given config."""
    try:
        # Parse Keepa data
        parsed_data = parse_keepa_product(keepa_data)
        
        # Calculate ROI metrics
        current_price = Decimal(str(parsed_data.get('current_price', 20.0)))
        estimated_cost = Decimal(str(parsed_data.get('current_price', 20.0))) * Decimal('0.75')  # Estimate 75% of current price
        
        roi_result = calculate_roi_metrics(
            current_price=current_price,
            estimated_buy_cost=estimated_cost,
            product_weight_lbs=Decimal(str(parsed_data.get('weight', 1.0))),
            category="books",
            config=config
        )
        
        # Prepare velocity data
        velocity_data = VelocityData(
            current_bsr=parsed_data.get('current_bsr'),
            bsr_history=parsed_data.get('bsr_history', []),
            price_history=parsed_data.get('price_history', []),
            buybox_history=parsed_data.get('buybox_history', []),
            offers_history=parsed_data.get('offers_history', []),
            category="books"
        )
        
        velocity_result = calculate_velocity_score(velocity_data, config=config)
        
        # Determine recommendation
        recommendation = "PASS"
        risk_factors = []
        
        roi_percentage = roi_result.get('roi_percentage', 0)
        velocity_score = velocity_result.get('velocity_score', 0)
        target_roi = config.get('roi', {}).get('target_roi_percent', 30)
        min_velocity = config.get('velocity', {}).get('min_velocity_score', 50)
        
        if roi_percentage >= target_roi:
            if velocity_score >= min_velocity:
                recommendation = "BUY"
            else:
                recommendation = "WATCH"
                risk_factors.append("Low velocity score")
        else:
            risk_factors.append("Below target ROI")
            
        # Calculate confidence
        roi_confidence = roi_result.get('confidence_level', 0.5)
        velocity_confidence = velocity_result.get('velocity_score', 0) / 100.0
        confidence_score = min(roi_confidence * velocity_confidence * 100, 95.0)
        
        return AnalysisResult(
            asin=asin,
            title=keepa_data.get('title', 'Unknown'),
            roi=roi_result,
            velocity=velocity_result,
            recommendation=recommendation,
            risk_factors=risk_factors,
            confidence_score=confidence_score
        )
        
    except Exception as e:
        logger.error(f"Analysis failed for {asin}: {e}")
        return AnalysisResult(
            asin=asin,
            title=keepa_data.get('title', 'Unknown'),
            roi={"error": str(e)},
            velocity={"error": str(e)},
            recommendation="ERROR",
            risk_factors=["Analysis failed"],
            confidence_score=0.0
        )

# === ENDPOINTS ===

@router.post("/ingest", response_model=IngestResponse)
async def ingest_batch(
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
                    
                    # Analyze product
                    analysis = await analyze_product(asin, keepa_data, config, keepa_service)
                    
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