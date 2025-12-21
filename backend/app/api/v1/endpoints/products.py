"""
Products Discovery API Endpoints - Phase 2 Jour 5
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.db import get_db_session
from app.services.keepa_service import KeepaService, get_keepa_service
from app.services.config_service import ConfigService
from app.services.keepa_product_finder import KeepaProductFinderService
from app.services.verification_service import VerificationService
from app.schemas.verification import VerificationRequest, VerificationResponse
from app.core.config import settings
from app.core.guards import require_tokens

router = APIRouter()


class DiscoverRequest(BaseModel):
    """Request for product discovery."""
    domain: int = Field(1, description="Amazon domain (1=US, 2=UK, etc.)")
    category: Optional[int] = Field(None, description="Keepa category ID")
    bsr_min: Optional[int] = Field(None, ge=1, description="Minimum BSR")
    bsr_max: Optional[int] = Field(None, ge=1, description="Maximum BSR")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price in dollars")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price in dollars")
    max_results: int = Field(50, ge=1, le=200, description="Max products to return")

    model_config = {
        "json_schema_extra": {
            "example": {
                "domain": 1,
                "category": 283155,  # Books
                "bsr_min": 10000,
                "bsr_max": 100000,
                "price_min": 10.0,
                "price_max": 50.0,
                "max_results": 20
            }
        }
    }


class DiscoverWithScoringRequest(BaseModel):
    """Request for product discovery with scoring."""
    domain: int = Field(1, description="Amazon domain")
    category: Optional[int] = Field(None, description="Keepa category ID")
    bsr_min: Optional[int] = Field(None, ge=1, description="Minimum BSR")
    bsr_max: Optional[int] = Field(None, ge=1, description="Maximum BSR")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price")
    min_roi: Optional[float] = Field(None, description="Minimum ROI %")
    min_velocity: Optional[float] = Field(None, ge=0, le=100, description="Minimum velocity score")
    max_results: int = Field(20, ge=1, le=100, description="Max products to return")
    force_refresh: bool = Field(False, description="Force refresh Keepa data (bypass cache)")
    strategy: Optional[str] = Field(
        None,
        description="Strategy for velocity/recommendation adjustments: textbooks_standard, textbooks_patience, smart_velocity"
    )


class ProductScore(BaseModel):
    """Product with scoring metrics."""
    asin: str
    title: str
    price: float
    bsr: int
    roi_percent: float
    velocity_score: float
    recommendation: str


class DiscoverResponse(BaseModel):
    """Response for product discovery."""
    asins: List[str]
    count: int
    query: dict


class DiscoverWithScoringResponse(BaseModel):
    """Response with scored products - matches frontend ProductDiscoveryResponseSchema."""
    products: List[ProductScore]
    total_count: int
    cache_hit: bool
    metadata: dict


@router.post("/discover", response_model=DiscoverResponse)
@require_tokens("manual_search")
async def discover_products(
    request: DiscoverRequest,
    db: AsyncSession = Depends(get_db_session),
    keepa: KeepaService = Depends(get_keepa_service)
):
    """
    Discover products matching criteria.

    Returns list of ASINs for further analysis.

    **Token Cost**:
    - Bestsellers: 50 tokens per category
    - Deals: 5 tokens per 150 deals

    **Use Cases**:
    - Find products in specific BSR range
    - Discover deals in price range
    - Get bestsellers for category
    """
    # Check API key
    if not settings.KEEPA_API_KEY:
        raise HTTPException(status_code=503, detail="Keepa API key not configured")

    try:
        # Initialize services - Use injected keepa instance from @require_tokens decorator
        config_service = ConfigService(db)
        finder_service = KeepaProductFinderService(keepa, config_service, db)

        # Discover products
        asins = await finder_service.discover_products(
            domain=request.domain,
            category=request.category,
            bsr_min=request.bsr_min,
            bsr_max=request.bsr_max,
            price_min=request.price_min,
            price_max=request.price_max,
            max_results=request.max_results
        )

        return DiscoverResponse(
            asins=asins,
            count=len(asins),
            query=request.model_dump(exclude_none=True)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Always close Keepa client to prevent connection leaks
        await keepa.close()


@router.post("/discover-with-scoring", response_model=DiscoverWithScoringResponse)
@require_tokens("manual_search")
async def discover_with_scoring(
    request: DiscoverWithScoringRequest,
    db: AsyncSession = Depends(get_db_session),
    keepa: KeepaService = Depends(get_keepa_service)
):
    """
    Discover and score products.

    Returns products with ROI and velocity scoring.

    **Token Cost**:
    - Discovery: 5-50 tokens
    - Product details: 1 token per product
    - Total: ~50-150 tokens typical

    **Scoring**:
    - ROI calculation using Config Service
    - Velocity score from BSR tiers
    - Recommendation: STRONG_BUY, BUY, CONSIDER, SKIP
    """
    # Check API key
    if not settings.KEEPA_API_KEY:
        raise HTTPException(status_code=503, detail="Keepa API key not configured")

    try:
        # Initialize services - Use injected keepa instance from @require_tokens decorator
        config_service = ConfigService(db)
        finder_service = KeepaProductFinderService(keepa, config_service, db)

        # Discover with scoring
        # Phase 8: Pass strategy for velocity/recommendation adjustments
        products = await finder_service.discover_with_scoring(
            domain=request.domain,
            category=request.category,
            bsr_min=request.bsr_min,
            bsr_max=request.bsr_max,
            price_min=request.price_min,
            price_max=request.price_max,
            min_roi=request.min_roi,
            min_velocity=request.min_velocity,
            max_results=request.max_results,
            force_refresh=request.force_refresh,
            strategy=request.strategy
        )

        # Convert to response models
        product_scores = [
            ProductScore(**product)
            for product in products
        ]

        # Determine cache status from actual cache usage in discover_with_scoring
        # If cache_service exists and products were returned, we can check metadata
        # Note: For accurate cache_hit, the service would need to return this info
        # For now, we assume cache was used if cache_service exists and is enabled
        cache_hit = (
            hasattr(finder_service, 'cache_service') and
            finder_service.cache_service is not None and
            not request.force_refresh  # force_refresh bypasses cache
        )

        return DiscoverWithScoringResponse(
            products=product_scores,
            total_count=len(product_scores),
            cache_hit=cache_hit,
            metadata={
                "filters_applied": request.model_dump(exclude_none=True),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "cache" if cache_hit else "keepa_api"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Always close Keepa client to prevent connection leaks
        await keepa.close()


@router.get("/categories")
async def get_popular_categories():
    """
    Get popular Keepa categories for discovery.

    Returns commonly used categories with their IDs.
    """
    categories = [
        {"id": 283155, "name": "Books", "domain": 1},
        {"id": 165793011, "name": "Baby Products", "domain": 1},
        {"id": 1055398, "name": "Home & Kitchen", "domain": 1},
        {"id": 16310091, "name": "Grocery & Gourmet Food", "domain": 1},
        {"id": 3760901, "name": "Health & Household", "domain": 1},
        {"id": 2619533011, "name": "Pet Supplies", "domain": 1},
        {"id": 3375251, "name": "Sports & Outdoors", "domain": 1},
        {"id": 468642, "name": "Tools & Home Improvement", "domain": 1},
        {"id": 15684181, "name": "Automotive", "domain": 1},
        {"id": 11091801, "name": "Musical Instruments", "domain": 1},
    ]

    return {"categories": categories}


@router.get("/health")
async def health_check():
    """
    Check Product Finder service health.
    """
    return {
        "status": "healthy",
        "service": "Product Finder",
        "api_key_configured": bool(settings.KEEPA_API_KEY),
        "endpoints": [
            "/products/discover",
            "/products/discover-with-scoring",
            "/products/categories",
            "/products/{asin}/verify"
        ]
    }


@router.post("/{asin}/verify", response_model=VerificationResponse)
async def verify_product(
    asin: str,
    request: VerificationRequest = None,
    keepa_service: KeepaService = Depends(get_keepa_service)
):
    """
    Verify a product's current status before purchase.

    Phase 8: Pre-purchase verification endpoint.
    Compares saved analysis data against current Keepa API data to detect:
    - Price changes (significant increase/decrease)
    - BSR changes (rank degradation)
    - Competition changes (more FBA sellers)
    - Amazon selling status (critical - avoid if Amazon enters)

    Returns:
        VerificationResponse with status (OK/CHANGED/AVOID), detected changes,
        and current product data.
    """
    from decimal import Decimal

    # Build request from path param and optional body
    if request is None:
        request = VerificationRequest(asin=asin)
    elif request.asin != asin:
        # Ensure ASIN in path matches body
        request = VerificationRequest(
            asin=asin,
            saved_price=request.saved_price,
            saved_bsr=request.saved_bsr,
            saved_fba_count=request.saved_fba_count
        )

    service = VerificationService(keepa_service=keepa_service)
    return await service.verify_product(request)