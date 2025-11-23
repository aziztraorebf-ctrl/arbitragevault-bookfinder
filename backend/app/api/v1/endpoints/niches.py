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
from app.services.keepa_product_finder import KeepaProductFinderService
from app.services.niche_templates import discover_curated_niches
from app.core.config import settings
from app.api.v1.endpoints.products import DiscoverWithScoringResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Timeout protection for Keepa endpoints
ENDPOINT_TIMEOUT = 30  # seconds


@router.get("/discover", response_model=DiscoverWithScoringResponse)
@require_tokens("surprise_me")
async def discover_niches_auto(
    count: int = Query(3, ge=1, le=5, description="Number of niches to discover"),
    shuffle: bool = Query(True, description="Randomize template selection"),
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

        # Initialize services
        keepa_service = KeepaService(api_key=settings.KEEPA_API_KEY)
        config_service = ConfigService(db)
        finder_service = KeepaProductFinderService(keepa_service, config_service, db)

        # Log token balance BEFORE operation
        balance_before = await keepa_service.check_api_balance()
        logger.info(f"Niche discovery started - Token balance: {balance_before}")

        # Discover curated niches with timeout protection
        try:
            niches = await asyncio.wait_for(
                discover_curated_niches(
                    db=db,
                    product_finder=finder_service,
                    count=count,
                    shuffle=shuffle
                ),
                timeout=ENDPOINT_TIMEOUT
            )
        except asyncio.TimeoutError:
            await keepa_service.close()
            raise HTTPException(
                status_code=408,
                detail=f"Niche discovery timed out after {ENDPOINT_TIMEOUT}s. Try reducing count parameter."
            )

        # Log token balance AFTER operation
        balance_after = await keepa_service.check_api_balance()
        tokens_consumed = balance_before - balance_after
        logger.info(f"Niche discovery completed - Tokens consumed: {tokens_consumed} (balance: {balance_after})")

        await keepa_service.close()

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
        import traceback
        import sys

        # Log full traceback to file
        error_log_path = "logs/niche_endpoint_error.log"
        with open(error_log_path, "w", encoding="utf-8") as f:
            f.write(f"Exception: {type(e).__name__}\n")
            f.write(f"Message: {str(e)}\n\n")
            f.write(f"Full traceback:\n")
            traceback.print_exc(file=f)

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
