"""
Keepa Router - Debug/Health/Test Endpoints
==========================================
Debug, health check, and test endpoints for Keepa integration.

Separated from keepa.py for SRP compliance.
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List

from fastapi import APIRouter, Query, Depends

from app.services.keepa_service import KeepaService, get_keepa_service
from app.services.business_config_service import BusinessConfigService, get_business_config_service
from app.services.keepa_parser_v2 import parse_keepa_product
from app.core.calculations import (
    calculate_roi_metrics, calculate_velocity_score, VelocityData
)
from .keepa_utils import generate_trace_id, normalize_identifier

router = APIRouter()
logger = logging.getLogger(__name__)


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

    debug_trace = []

    try:
        debug_trace.append("=== STEP 1: Getting config ===")

        try:
            config = await config_service.get_effective_config(domain_id=1, category="books")
            debug_trace.append(f"Config loaded: {type(config)}")
        except Exception as e:
            config = {"roi": {"target_roi_percent": 30}, "velocity": {"min_velocity_score": 50}}
            debug_trace.append(f"Config fallback: {e}")

        debug_trace.append("=== STEP 2: Getting Keepa data ===")

        async with keepa_service:
            keepa_data = await keepa_service.get_product_data(asin, force_refresh=False)

            if not keepa_data:
                return {"error": "No Keepa data", "debug_trace": debug_trace}

            debug_trace.append(f"Keepa data: {len(keepa_data)} keys")

            debug_trace.append("=== STEP 3: Parsing Keepa data ===")

            parsed_data = parse_keepa_product(keepa_data)
            debug_trace.append(f"Parsing complete: {type(parsed_data)}")

            # Examine current_price
            current_price_raw = parsed_data.get('current_price')
            debug_trace.append(f"current_price_raw: {repr(current_price_raw)} (type: {type(current_price_raw)})")

            if hasattr(current_price_raw, '__len__') and not isinstance(current_price_raw, str):
                debug_trace.append(f"current_price_raw has length: {len(current_price_raw)}")
                if hasattr(current_price_raw, '__getitem__'):
                    debug_trace.append(f"current_price_raw content: {list(current_price_raw) if len(current_price_raw) < 10 else 'too long'}")

            debug_trace.append("=== STEP 4: Price validation ===")

            if current_price_raw is None:
                return {"error": "current_price is None", "debug_trace": debug_trace}
            elif current_price_raw <= 0:
                return {"error": "current_price <= 0", "debug_trace": debug_trace}

            debug_trace.append("=== STEP 5: Decimal conversion ===")

            try:
                current_price = Decimal(str(current_price_raw))
                debug_trace.append(f"Decimal conversion: {current_price} (type: {type(current_price)})")
            except Exception as decimal_error:
                debug_trace.append(f"Decimal conversion failed: {decimal_error}")
                debug_trace.append(f"str(current_price_raw): {repr(str(current_price_raw))}")
                return {
                    "error": f"Decimal conversion failed: {decimal_error}",
                    "debug_trace": debug_trace,
                    "stack_trace": traceback.format_exc()
                }

            debug_trace.append("=== STEP 6: Estimated cost calculation ===")

            try:
                estimated_cost = current_price * Decimal('0.75')
                debug_trace.append(f"Estimated cost: {estimated_cost}")
            except Exception as mult_error:
                debug_trace.append(f"MULTIPLICATION ERROR FOUND: {mult_error}")
                debug_trace.append(f"current_price type at multiplication: {type(current_price)}")
                debug_trace.append(f"current_price value at multiplication: {repr(current_price)}")
                return {
                    "error": f"Multiplication failed: {mult_error}",
                    "debug_trace": debug_trace,
                    "stack_trace": traceback.format_exc()
                }

            debug_trace.append("=== STEP 7: Weight handling ===")

            weight_raw = parsed_data.get('weight', 1.0)
            debug_trace.append(f"weight_raw: {repr(weight_raw)} (type: {type(weight_raw)})")

            try:
                weight_decimal = Decimal(str(weight_raw))
                debug_trace.append(f"Weight decimal: {weight_decimal}")
            except Exception as weight_error:
                debug_trace.append(f"Weight conversion failed: {weight_error}")
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
                debug_trace.append(f"ROI calculation success: {type(roi_result)}")
            except Exception as roi_error:
                debug_trace.append(f"ROI CALCULATION ERROR: {roi_error}")
                debug_trace.append(f"Parameters passed to ROI:")
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
                debug_trace.append(f"VelocityData created: {type(velocity_data)}")
            except Exception as vel_data_error:
                debug_trace.append(f"VelocityData creation failed: {vel_data_error}")
                return {
                    "error": f"VelocityData creation failed: {vel_data_error}",
                    "debug_trace": debug_trace,
                    "stack_trace": traceback.format_exc()
                }

            debug_trace.append("=== STEP 10: Velocity calculation ===")

            try:
                velocity_result = calculate_velocity_score(velocity_data, config=config)
                debug_trace.append(f"Velocity calculation success: {type(velocity_result)}")
            except Exception as vel_calc_error:
                debug_trace.append(f"VELOCITY CALCULATION ERROR: {vel_calc_error}")
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
        debug_trace.append(f"UNEXPECTED ERROR: {e}")
        import traceback
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "debug_trace": debug_trace,
            "stack_trace": traceback.format_exc()
        }


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

    Force balance refresh (bypass 60s cache) for accurate health status.
    """
    try:
        async with keepa_service:
            # Force balance refresh for accurate health check
            actual_balance = await keepa_service.check_api_balance()

            # Sync throttle with real-time balance
            keepa_service.throttle.set_tokens(actual_balance)

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
                    "remaining": actual_balance,
                    "refill_in_minutes": health_status.get("refill_in_minutes", 0),
                    "total_used": keepa_service.metrics.tokens_used,
                    "requests_made": keepa_service.metrics.requests_count
                },
                "cache": {
                    "hit_rate": round(hit_rate, 2),
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
                    "average_latency_ms": 0
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
    Enhanced with better error handling and tracing.
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


__all__ = [
    'router',
    'debug_analyze_endpoint',
    'process_batch_async',
    'keepa_health_check',
    'test_keepa_connection',
]
