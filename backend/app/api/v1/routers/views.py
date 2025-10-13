"""
Views Router - View-Specific Product Scoring Endpoints

Provides endpoints for scoring products with view-specific weights.
Supports adaptive scoring based on frontend context (dashboard, mes_niches, etc.)

Phase 2 of Strategy Refactor (strategy_refactor_v2_phase2_views)
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
import logging

from app.services.keepa_service import KeepaService, get_keepa_service
from app.services.keepa_parser_v2 import parse_keepa_product
from app.services.scoring_v2 import (
    compute_view_score,
    validate_view_type,
    get_available_views,
    VIEW_WEIGHTS
)
from app.services.business_config_service import BusinessConfigService, get_business_config_service
from app.services.amazon_check_service import check_amazon_presence  # Phase 2.5A
from app.core.calculations import (
    calculate_roi_metrics,
    calculate_velocity_score,
    calculate_max_buy_price,  # Phase 2.5A Hybrid solution
    VelocityData
)
from decimal import Decimal

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Pydantic Schemas
# ============================================================================

class ViewScoreRequest(BaseModel):
    """Request body for view scoring endpoint."""

    identifiers: List[str] = Field(
        ...,
        description="List of ASINs or ISBNs to score",
        min_items=1,
        max_items=100,
        example=["0593655036", "B08N5WRWNW"]
    )
    strategy: Optional[str] = Field(
        None,
        description="Strategy profile for boost application (textbook/velocity/balanced)",
        example="textbook"
    )

    @validator("identifiers")
    def validate_identifiers(cls, v):
        """Ensure identifiers are non-empty strings."""
        if not all(isinstance(x, str) and x.strip() for x in v):
            raise ValueError("All identifiers must be non-empty strings")
        return [x.strip() for x in v]

    @validator("strategy")
    def validate_strategy(cls, v):
        """Validate strategy is valid enum value."""
        if v is not None and v not in ["textbook", "velocity", "balanced"]:
            raise ValueError("Strategy must be one of: textbook, velocity, balanced")
        return v


class ProductScore(BaseModel):
    """Individual product score result."""

    asin: str = Field(..., description="Product ASIN")
    score: float = Field(..., description="Computed view score (0-100)")
    rank: int = Field(..., description="Rank within result set (1-based)")
    strategy_profile: Optional[str] = Field(None, description="Strategy detected/applied")
    weights_applied: Dict[str, float] = Field(..., description="Weights used for this view")
    components: Dict[str, float] = Field(
        ...,
        description="Score breakdown (roi/velocity/stability contributions)"
    )
    raw_metrics: Dict[str, float] = Field(
        ...,
        description="Raw input metrics (roi_pct, velocity_score, stability_score)"
    )
    error: Optional[str] = Field(None, description="Error message if scoring failed")

    # Phase 2.5A - Amazon Check (optional fields)
    amazon_on_listing: bool = Field(
        False,
        description="Amazon has any offer on this product (Phase 2.5A)"
    )
    amazon_buybox: bool = Field(
        False,
        description="Amazon currently owns the Buy Box (Phase 2.5A)"
    )
    title: Optional[str] = Field(None, description="Product title from Keepa")


class ViewScoreMetadata(BaseModel):
    """Metadata for view score response."""

    view_type: str = Field(..., description="View type used for scoring")
    weights_used: Dict[str, float] = Field(..., description="Weight matrix for this view")
    total_products: int = Field(..., description="Total products scored")
    successful_scores: int = Field(..., description="Number of successfully scored products")
    failed_scores: int = Field(..., description="Number of failed scorings")
    avg_score: float = Field(..., description="Average score across all products")
    strategy_requested: Optional[str] = Field(None, description="Strategy profile requested")


class ViewScoreResponse(BaseModel):
    """Complete response for view scoring endpoint."""

    products: List[ProductScore] = Field(
        ...,
        description="Scored products, sorted by score descending"
    )
    metadata: ViewScoreMetadata = Field(..., description="Response metadata")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/views/{view_type}", response_model=ViewScoreResponse)
async def score_products_for_view(
    view_type: str,
    request: ViewScoreRequest,
    http_request: Request,
    keepa_service: KeepaService = Depends(get_keepa_service),
    config_service: BusinessConfigService = Depends(get_business_config_service)
):
    """
    Score products with view-specific weights.

    This endpoint adapts product scoring based on frontend view context.
    Each view has distinct priorities for ROI, velocity, and stability metrics.

    **Available Views:**
    - `dashboard`: Balanced overview (ROI=0.5, Velocity=0.5, Stability=0.3)
    - `mes_niches`: ROI priority (ROI=0.6, Velocity=0.4, Stability=0.5)
    - `analyse_strategique`: Velocity priority (ROI=0.4, Velocity=0.6, Stability=0.2)
    - `auto_sourcing`: Maximum velocity (ROI=0.3, Velocity=0.7, Stability=0.1)
    - `stock_estimates`: Stability priority (ROI=0.45, Velocity=0.45, Stability=0.6)
    - `niche_discovery`: Balanced exploration (ROI=0.5, Velocity=0.5, Stability=0.4)

    **Feature Flag:**
    Requires `view_specific_scoring: true` in config or via header override.

    **Args:**
    - **view_type** (path): View identifier (see available views above)
    - **identifiers** (body): List of ASINs/ISBNs to score (1-100 items)
    - **strategy** (body, optional): Strategy boost (textbook/velocity/balanced)

    **Returns:**
    - Products sorted by score descending
    - Metadata with scoring statistics
    - Components breakdown for each product

    **Example Request:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/views/mes_niches" \\
      -H "Content-Type: application/json" \\
      -H 'X-Feature-Flags-Override: {"view_specific_scoring":true}' \\
      -d '{"identifiers":["0593655036","B08N5WRWNW"],"strategy":"textbook"}'
    ```

    **Example Response:**
    ```json
    {
      "products": [
        {
          "asin": "0593655036",
          "score": 78.5,
          "rank": 1,
          "strategy_profile": "textbook",
          "weights_applied": {"roi": 0.6, "velocity": 0.4, "stability": 0.5},
          "components": {
            "roi_contribution": 48.0,
            "velocity_contribution": 24.0,
            "stability_contribution": 30.0
          },
          "raw_metrics": {"roi_pct": 80.0, "velocity_score": 60.0, "stability_score": 60.0}
        }
      ],
      "metadata": {
        "view_type": "mes_niches",
        "total_products": 2,
        "successful_scores": 2,
        "avg_score": 72.3
      }
    }
    ```
    """
    # 1. Validate view_type
    if not validate_view_type(view_type):
        available = ", ".join(get_available_views())
        raise HTTPException(
            status_code=400,
            detail=f"Invalid view_type '{view_type}'. Available: {available}"
        )

    # 2. Get effective config (with feature flag check)
    config = await config_service.get_effective_config(domain_id=1, category="books")

    # Check if view_specific_scoring is enabled
    feature_flags = config.get("feature_flags", {})
    view_scoring_enabled = feature_flags.get("view_specific_scoring", False)

    # DEV/TEST ONLY: Feature flags override via header
    if "X-Feature-Flags-Override" in http_request.headers:
        import json
        try:
            override_flags = json.loads(http_request.headers["X-Feature-Flags-Override"])
            feature_flags.update(override_flags)
            view_scoring_enabled = feature_flags.get("view_specific_scoring", False)
            logger.info(f"[DEV] Feature flags overridden for view scoring: {override_flags}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"[DEV] Invalid feature flags override header: {e}")

    if not view_scoring_enabled:
        raise HTTPException(
            status_code=403,
            detail="View-specific scoring not enabled. Set 'view_specific_scoring: true' in config."
        )

    # 3. Fetch Keepa data for all identifiers
    logger.info(
        f"Scoring {len(request.identifiers)} products for view '{view_type}' "
        f"(strategy={request.strategy})"
    )

    try:
        async with keepa_service:
            # 4. Fetch and score each product
            scored_products = []
            successful_scores = 0
            failed_scores = 0

            for identifier in request.identifiers:
                try:
                    # Fetch Keepa data for this product
                    product_data = await keepa_service.get_product_data(identifier, force_refresh=False)

                    if not product_data:
                        logger.warning(f"No Keepa data found for {identifier}")
                        failed_scores += 1
                        scored_products.append({
                            "asin": identifier,
                            "score": 0.0,
                            "rank": 0,
                            "strategy_profile": None,
                            "weights_applied": {},
                            "components": {},
                            "raw_metrics": {},
                            "error": "No data available from Keepa",
                            "amazon_on_listing": False,  # Phase 2.5A default
                            "amazon_buybox": False,  # Phase 2.5A default
                            "title": None
                        })
                        continue

                    # Parse Keepa product data
                    parsed = parse_keepa_product(product_data)
                    asin = parsed.get("asin", identifier)
                    title = parsed.get("title")

                    # Phase 2.5A FIX: Calculate ROI and Velocity metrics
                    # These were missing from parse_keepa_product(), causing all scores = 0
                    try:
                        # Extract prices for ROI calculation
                        current_price = parsed.get("current_price")
                        fba_price = parsed.get("current_fba_price")

                        # Calculate ROI if prices available
                        if current_price and fba_price:
                            roi_result = calculate_roi_metrics(
                                current_price=Decimal(str(current_price)),
                                estimated_buy_cost=Decimal(str(fba_price)),
                                category="books",
                                config=config
                            )
                            parsed["roi"] = {
                                "roi_percentage": roi_result.get("roi_percentage", 0.0)
                            }
                            logger.debug(f"[ROI] {asin}: {roi_result.get('roi_percentage', 0)}%")
                        else:
                            parsed["roi"] = {"roi_percentage": 0.0}
                            logger.debug(f"[ROI] {asin}: No price data, defaulting to 0%")

                        # Calculate Velocity if BSR history available
                        current_bsr = parsed.get("current_bsr")
                        bsr_history = parsed.get("bsr_history", [])

                        if current_bsr and bsr_history:
                            velocity_data = VelocityData(
                                current_bsr=current_bsr,
                                bsr_history=bsr_history,
                                price_history=parsed.get("price_history", []),
                                buybox_history=[],
                                offers_history=[]
                            )
                            velocity_result = calculate_velocity_score(velocity_data, config=config)
                            parsed["velocity_score"] = velocity_result.get("velocity_score", 0.0)
                            logger.debug(f"[VELOCITY] {asin}: {velocity_result.get('velocity_score', 0)}")
                        else:
                            parsed["velocity_score"] = 0.0
                            logger.debug(f"[VELOCITY] {asin}: No BSR data, defaulting to 0")

                    except Exception as calc_error:
                        logger.warning(f"[CALC_ERROR] {asin}: {calc_error}, defaulting ROI/Velocity to 0")
                        parsed["roi"] = {"roi_percentage": 0.0}
                        parsed["velocity_score"] = 0.0
                        velocity_result = {}

                    # Phase 2.5A HYBRID: Calculate Max Buy Price (35% ROI target)
                    max_buy_price_35pct = Decimal("0.00")
                    market_sell_price = Decimal("0.00")
                    market_buy_price = Decimal("0.00")

                    try:
                        if current_price and current_price > 0:
                            market_sell_price = Decimal(str(current_price))
                            max_buy_price_35pct = calculate_max_buy_price(
                                sell_price=market_sell_price,
                                target_roi_pct=35.0,
                                category="books",
                                config=config
                            )
                            logger.debug(f"[MAX_BUY] {asin}: ${max_buy_price_35pct}")

                        if fba_price and fba_price > 0:
                            market_buy_price = Decimal(str(fba_price))

                    except Exception as max_buy_error:
                        logger.warning(f"[MAX_BUY_ERROR] {asin}: {max_buy_error}, defaulting to 0")

                    # Phase 2.5A HYBRID: Enrich velocity breakdown with estimated sales
                    velocity_breakdown = velocity_result.copy() if velocity_result else {}
                    rank_drops = velocity_result.get("rank_drops_30d", 0) if velocity_result else 0
                    estimated_sales_30d = int(rank_drops * 1.5) if rank_drops else 0
                    velocity_breakdown["estimated_sales_30d"] = estimated_sales_30d

                    # Compute view-specific score
                    score_result = compute_view_score(
                        parsed_data=parsed,
                        view_type=view_type,
                        strategy_profile=request.strategy
                    )

                    # Phase 2.5A: Amazon Check (if feature enabled)
                    amazon_check_enabled = feature_flags.get("amazon_check_enabled", False)
                    amazon_on_listing = False
                    amazon_buybox = False

                    if amazon_check_enabled:
                        amazon_result = check_amazon_presence(product_data)
                        amazon_on_listing = amazon_result.get("amazon_on_listing", False)
                        amazon_buybox = amazon_result.get("amazon_buybox", False)

                    scored_products.append({
                        "asin": asin,
                        "score": score_result["score"],
                        "rank": 0,  # Will be assigned after sorting
                        "strategy_profile": score_result["strategy_profile"],
                        "weights_applied": score_result["weights_applied"],
                        "components": score_result["components"],
                        "raw_metrics": score_result["raw_metrics"],
                        "error": None,
                        "amazon_on_listing": amazon_on_listing,  # Phase 2.5A
                        "amazon_buybox": amazon_buybox,  # Phase 2.5A
                        "title": title,
                        # Phase 2.5A HYBRID - Market Analysis + Recommendations
                        "market_sell_price": float(market_sell_price),
                        "market_buy_price": float(market_buy_price),
                        "current_roi_pct": score_result["raw_metrics"].get("roi_pct", 0.0),
                        "max_buy_price_35pct": float(max_buy_price_35pct),
                        "velocity_breakdown": velocity_breakdown
                    })
                    successful_scores += 1

                except Exception as e:
                    logger.error(f"Failed to score product {identifier}: {e}")
                    failed_scores += 1
                    scored_products.append({
                        "asin": identifier,
                        "score": 0.0,
                        "rank": 0,
                        "strategy_profile": None,
                        "weights_applied": {},
                        "components": {},
                        "raw_metrics": {},
                        "error": str(e),
                        "amazon_on_listing": False,  # Phase 2.5A default
                        "amazon_buybox": False,  # Phase 2.5A default
                        "title": None
                    })

            # 5. Sort by score descending and assign ranks
            scored_products.sort(key=lambda x: x["score"], reverse=True)
            for idx, product in enumerate(scored_products, start=1):
                product["rank"] = idx

            # 6. Calculate metadata
            valid_scores = [p["score"] for p in scored_products if p["error"] is None]
            avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

            weights = VIEW_WEIGHTS[view_type]
            metadata = ViewScoreMetadata(
                view_type=view_type,
                weights_used={
                    "roi": weights["roi"],
                    "velocity": weights["velocity"],
                    "stability": weights["stability"]
                },
                total_products=len(scored_products),
                successful_scores=successful_scores,
                failed_scores=failed_scores,
                avg_score=round(avg_score, 2),
                strategy_requested=request.strategy
            )

            # 7. Log summary for monitoring
            logger.info(
                f"[VIEW_SCORING] view={view_type} | "
                f"total={len(scored_products)} | "
                f"success={successful_scores} | "
                f"fail={failed_scores} | "
                f"avg_score={avg_score:.2f}"
            )

            return ViewScoreResponse(
                products=[ProductScore(**p) for p in scored_products],
                metadata=metadata
            )
    except Exception as e:
        logger.error(f"Failed to fetch Keepa data: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch product data from Keepa: {str(e)}"
        )


@router.get("/views", response_model=Dict[str, Any])
async def list_available_views():
    """
    List all available view types with their weight configurations.

    **Returns:**
    - Dictionary mapping view types to their weight configurations
    - Each view includes roi/velocity/stability weights + description

    **Example Response:**
    ```json
    {
      "dashboard": {
        "roi": 0.5,
        "velocity": 0.5,
        "stability": 0.3,
        "description": "Balanced overview - Equal ROI/Velocity priority"
      },
      "mes_niches": {
        "roi": 0.6,
        "velocity": 0.4,
        "stability": 0.5,
        "description": "Niche management - ROI priority with stability"
      }
    }
    ```
    """
    return {"views": VIEW_WEIGHTS}
