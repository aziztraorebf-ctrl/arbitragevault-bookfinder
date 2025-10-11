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
            keepa_response = await keepa_service.fetch_products(request.identifiers)

            # 4. Parse and score each product
            products_data = keepa_response.get("products", [])
            if not products_data:
                raise HTTPException(
                    status_code=404,
                    detail="No products found for the provided identifiers"
                )

            scored_products = []
            successful_scores = 0
            failed_scores = 0

            for product_data in products_data:
                try:
                    # Parse Keepa product data
                    parsed = parse_keepa_product(product_data)
                    asin = parsed.get("asin", "unknown")

                    # Compute view-specific score
                    score_result = compute_view_score(
                        parsed_data=parsed,
                        view_type=view_type,
                        strategy_profile=request.strategy
                    )

                    scored_products.append({
                        "asin": asin,
                        "score": score_result["score"],
                        "rank": 0,  # Will be assigned after sorting
                        "strategy_profile": score_result["strategy_profile"],
                        "weights_applied": score_result["weights_applied"],
                        "components": score_result["components"],
                        "raw_metrics": score_result["raw_metrics"],
                        "error": None
                    })
                    successful_scores += 1

                except Exception as e:
                    logger.error(f"Failed to score product: {e}")
                    failed_scores += 1
                    scored_products.append({
                        "asin": product_data.get("asin", "unknown"),
                        "score": 0.0,
                        "rank": 0,
                        "strategy_profile": None,
                        "weights_applied": {},
                        "components": {},
                        "raw_metrics": {},
                        "error": str(e)
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
