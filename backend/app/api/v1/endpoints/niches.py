"""
Niche Discovery API Endpoints - Phase 3 Day 9
"""

from typing import List, Optional
from datetime import datetime
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.core.guards import require_tokens
from app.services.keepa_service import KeepaService, get_keepa_service
from app.services.config_service import ConfigService
from app.services.keepa_product_finder import KeepaProductFinderService, estimate_discovery_cost
from app.services.niche_templates import discover_curated_niches
from app.core.config import settings
from app.api.v1.endpoints.products import DiscoverWithScoringResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Timeout protection for Keepa endpoints
ENDPOINT_TIMEOUT = 30  # seconds

# Phase 6: Budget Guard Configuration
MAX_ASINS_PER_NICHE = 100  # Reduced from 500 to save tokens


async def check_budget_before_discovery(
    count: int,
    keepa: KeepaService,
    max_asins_per_niche: int = MAX_ASINS_PER_NICHE
) -> bool:
    """
    Phase 6 Budget Guard: Check if sufficient tokens BEFORE consuming any.

    Raises HTTPException 429 if insufficient tokens with actionable details.

    Args:
        count: Number of niches to discover
        keepa: KeepaService instance
        max_asins_per_niche: Max ASINs to filter per niche

    Returns:
        True if budget sufficient

    Raises:
        HTTPException 429: If insufficient tokens
    """
    # Estimate cost
    estimated_cost = estimate_discovery_cost(count, max_asins_per_niche)

    # Get current balance
    current_balance = await keepa.check_api_balance()

    logger.info(
        f"[BUDGET_GUARD] Checking: count={count}, estimated={estimated_cost}, balance={current_balance}"
    )

    if current_balance < estimated_cost:
        deficit = estimated_cost - current_balance
        cost_per_niche = estimated_cost // count if count > 0 else 0

        # Calculate how many niches user CAN afford
        affordable_niches = current_balance // cost_per_niche if cost_per_niche > 0 else 0

        suggestion = (
            f"Try count={affordable_niches} (estimated: {affordable_niches * cost_per_niche} tokens)"
            if affordable_niches > 0
            else "Wait for token refresh or reduce count to 1"
        )

        logger.warning(
            f"[BUDGET_GUARD] Rejected: insufficient tokens. "
            f"Need {estimated_cost}, have {current_balance}, deficit {deficit}"
        )

        raise HTTPException(
            status_code=429,
            detail={
                "message": f"Insufficient tokens for {count} niches",
                "estimated_cost": estimated_cost,
                "current_balance": current_balance,
                "deficit": deficit,
                "suggestion": suggestion
            },
            headers={
                "X-Token-Balance": str(current_balance),
                "X-Token-Required": str(estimated_cost),
                "Retry-After": "3600"
            }
        )

    logger.info(f"[BUDGET_GUARD] Approved: {count} niches, estimated {estimated_cost} tokens")
    return True


@router.get("/discover", response_model=DiscoverWithScoringResponse)
@require_tokens("surprise_me")
async def discover_niches_auto(
    count: int = Query(3, ge=1, le=5, description="Number of niches to discover"),
    shuffle: bool = Query(True, description="Randomize template selection"),
    strategy: Optional[str] = Query(
        None,
        description="Strategy filter: textbooks_standard, textbooks_patience, smart_velocity, or None for all"
    ),
    db: AsyncSession = Depends(get_db_session),
    keepa: KeepaService = Depends(get_keepa_service)
):
    """
    Auto-discover curated niches - Phase 3 Day 9.

    Uses pre-defined niche templates validated with real-time Keepa data.
    Each template encodes market expertise (category clusters, BSR sweet spots, price ranges).

    **Returns**:
    - 3-5 validated niches with aggregate stats
    - Top 3 products per niche for preview
    - Real-time validation ensures niches are currently active (≥3 products threshold)

    **Example Response**:
    ```json
    {
      "products": [],
      "total_count": 0,
      "cache_hit": false,
      "metadata": {
        "mode": "auto",
        "niches": [
          {
            "id": "tech-books-python",
            "name": "[TECH] Python Books Beginners $20-50",
            "description": "...",
            "icon": "PYTHON",
            "products_found": 7,
            "avg_roi": 35.2,
            "avg_velocity": 68.5,
            "top_products": [...]
          }
        ],
        "niches_count": 3
      }
    }
    ```

    **Token Cost**:
    - Approx 50-150 tokens per niche validation
    - Cache reduces costs ~70% for repeated queries
    """
    try:
        # Check API key
        if not settings.KEEPA_API_KEY:
            raise HTTPException(status_code=503, detail="Keepa API key not configured")

        # Phase 6: Budget Guard - Check BEFORE consuming ANY tokens
        # This prevents the fire-and-forget token loss on timeout
        await check_budget_before_discovery(count=count, keepa=keepa)

        # Initialize services - Use injected keepa instance from @require_tokens decorator
        config_service = ConfigService(db)
        finder_service = KeepaProductFinderService(keepa, config_service, db)

        # Log token balance BEFORE operation
        balance_before = await keepa.check_api_balance()
        logger.info(f"Niche discovery started - Token balance: {balance_before}")

        # Discover curated niches with timeout protection
        try:
            niches = await asyncio.wait_for(
                discover_curated_niches(
                    db=db,
                    product_finder=finder_service,
                    count=count,
                    shuffle=shuffle,
                    strategy=strategy
                ),
                timeout=ENDPOINT_TIMEOUT
            )
        except asyncio.TimeoutError:
            await keepa.close()
            raise HTTPException(
                status_code=408,
                detail=f"Niche discovery timed out after {ENDPOINT_TIMEOUT}s. Try reducing count parameter."
            )

        # Log token balance AFTER operation
        balance_after = await keepa.check_api_balance()
        tokens_consumed = balance_before - balance_after
        logger.info(f"Niche discovery completed - Tokens consumed: {tokens_consumed} (balance: {balance_after})")

        await keepa.close()

        return DiscoverWithScoringResponse(
            products=[],  # Empty for auto mode
            total_count=0,
            cache_hit=False,
            metadata={
                "mode": "auto",
                "niches": niches,
                "niches_count": len(niches),
                "tokens_consumed": tokens_consumed,  # Add to response metadata
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "curated_templates"
            }
        )

    except asyncio.TimeoutError:
        # Already handled above, re-raise
        raise
    except Exception as e:
        # Log full traceback using Python logger (captured by Render automatically)
        logger.error(f"Niche discovery error: {type(e).__name__}: {str(e)}", exc_info=True)

        # Return safe ASCII-only error
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {repr(str(e)[:200])}")


@router.get("/health")
async def health_check():
    """Check Niche Discovery service health."""
    return {
        "status": "healthy",
        "service": "Niche Discovery",
        "api_key_configured": bool(settings.KEEPA_API_KEY),
        "endpoints": [
            "/niches/discover"
        ]
    }
