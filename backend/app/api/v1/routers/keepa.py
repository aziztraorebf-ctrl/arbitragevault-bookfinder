"""
Keepa integration endpoints - Main Router (Facade)
==================================================
This module acts as a facade, importing from specialized sub-modules
for better SRP compliance and maintainability.

Sub-modules:
- keepa_schemas: Pydantic request/response schemas
- keepa_utils: Utility functions (trace_id, normalize, analyze)
- keepa_debug: Debug/Health/Test endpoints
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List

from fastapi import APIRouter, Query, Depends, HTTPException, BackgroundTasks, Request

from app.services.keepa_service import KeepaService, get_keepa_service
from app.services.business_config_service import BusinessConfigService, get_business_config_service

# Import from specialized modules - maintain backward compatibility
from .keepa_schemas import (
    IngestBatchRequest,
    ConfigAudit,
    KeepaMetadata,
    ScoreBreakdown,
    PricingDetail,
    AnalysisResult,
    MetricsResponse,
    BatchResult,
    IngestResponse,
    StandardError,
)

from .keepa_utils import (
    generate_trace_id,
    normalize_identifier,
    analyze_product,
)

from .keepa_debug import (
    router as debug_router,
    process_batch_async,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Include debug router endpoints
router.include_router(debug_router, tags=["keepa-debug"])


# === MAIN ENDPOINTS ===

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
            domain_id=1,
            category="books"
        )

        # DEV/TEST ONLY: Feature flags override via header
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
                        source_price=request.source_price
                    )

                    # DEV/TEST ONLY: Validation logging if feature flags overridden
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
                data_freshness_hours=1.0
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


# Backward compatibility exports
__all__ = [
    # Router
    'router',

    # Schemas (re-exported)
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

    # Utilities (re-exported)
    'generate_trace_id',
    'normalize_identifier',
    'analyze_product',
]
