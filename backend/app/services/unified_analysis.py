"""
Unified Analysis Service for all Keepa product endpoints.
Provides a single source of truth for product data structure and processing.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from decimal import Decimal
import logging
from datetime import datetime

from app.services.keepa_parser_v2 import parse_keepa_product, parse_keepa_product_unified
from app.services.amazon_check_service import check_amazon_presence
from app.services.pricing_service import (
    compute_pricing_breakdown,
    calculate_roi_metrics,
    calculate_velocity_score,
    calculate_pricing_metrics_unified,  # Phase 2
    calculate_pricing_metrics_with_intrinsic  # Phase 4 - Textbook Pivot
)
from app.services.buying_guidance_service import BuyingGuidanceService
from app.core.calculations import (
    calculate_max_buy_price,
    VelocityData,
    compute_advanced_velocity_score,
    compute_advanced_stability_score,
    compute_advanced_confidence_score,
    compute_overall_rating,
    generate_readable_summary
)
from app.services.scoring_v2 import VIEW_WEIGHTS

logger = logging.getLogger(__name__)


# ============================================================================
# Unified Pydantic Schema - Complete with ALL fields
# ============================================================================

class UnifiedProductSchema(BaseModel):
    """
    Complete unified product schema used across all endpoints.
    This schema ensures consistency across:
    - /api/v1/keepa/ingest (Analyse Manuelle)
    - /api/v1/views/mes_niches (Mes Niches)
    - /api/v1/views/autosourcing (AutoSourcing)
    """

    # Core identifiers
    asin: str = Field(..., description="Product ASIN")
    title: Optional[str] = Field(None, description="Product title from Keepa")

    # Scoring and ranking
    score: float = Field(0.0, description="Computed view score (0-100)")
    rank: int = Field(0, description="Rank within result set (1-based)")
    strategy_profile: Optional[str] = Field(None, description="Strategy detected/applied")

    # Scoring components
    weights_applied: Dict[str, float] = Field(
        default_factory=dict,
        description="Weights used for this view"
    )
    components: Dict[str, float] = Field(
        default_factory=dict,
        description="Score breakdown (roi/velocity/stability contributions)"
    )
    raw_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Raw input metrics (roi_pct, velocity_score, stability_score)"
    )

    # Amazon presence
    amazon_on_listing: bool = Field(
        False,
        description="Amazon has any offer on this product"
    )
    amazon_buybox: bool = Field(
        False,
        description="Amazon currently owns the Buy Box"
    )

    # Market pricing
    market_sell_price: Optional[float] = Field(
        None,
        description="Current market sell price (Amazon/marketplace)"
    )
    market_buy_price: Optional[float] = Field(
        None,
        description="Current FBA buy price (3rd party sellers)"
    )
    current_roi_pct: Optional[float] = Field(
        None,
        description="ROI percentage if buying/selling at current market prices"
    )
    max_buy_price_35pct: Optional[float] = Field(
        None,
        description="Recommended max buy price for 35% ROI target"
    )

    # Velocity metrics
    velocity_breakdown: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed velocity components for tooltip display"
    )

    # USED vs NEW pricing
    pricing: Optional[Dict[str, Any]] = Field(
        None,
        description="Separated pricing for 'used' and 'new' conditions with ROI breakdown"
    )

    # BSR (Best Seller Rank)
    current_bsr: Optional[int] = Field(
        None,
        description="Current Best Seller Rank (BSR) from Keepa data"
    )

    # Raw Keepa data prices
    current_price: Optional[float] = Field(None, description="Current Amazon price")
    current_fba_price: Optional[float] = Field(None, description="Current FBA price")
    current_used_price: Optional[float] = Field(None, description="Current USED price")
    current_fbm_price: Optional[float] = Field(None, description="Current NEW/FBM price")

    # Additional metadata
    weight: Optional[float] = Field(None, description="Product weight in lbs")
    error: Optional[str] = Field(None, description="Error message if processing failed")


# ============================================================================
# Main Unified Analysis Function
# ============================================================================

async def build_unified_product(
    raw_keepa: Dict[str, Any],
    keepa_service: Any,
    config: Dict[str, Any],
    view_type: str = "mes_niches",
    strategy: Optional[str] = None,
    compute_score: bool = True
) -> Dict[str, Any]:
    """
    Build a unified product response structure.

    This is THE SINGLE source of truth for product data extraction.
    ALL endpoints should use this function to ensure consistency.

    Args:
        raw_keepa: Raw Keepa API response data
        keepa_service: KeepaService instance (for potential additional calls)
        config: Business configuration
        view_type: View type for scoring ("mes_niches", "autosourcing", "analyse_manuelle")
        strategy: Optional strategy override ("textbook", "velocity", "balanced")
        compute_score: Whether to compute scoring (False for raw data only)

    Returns:
        Complete unified product dict ready for API response
    """

    identifier = raw_keepa.get('data', {}).get('asin', 'UNKNOWN')

    try:
        # Step 1: Parse Keepa data (extracts all basic fields including BSR)
        parsed = parse_keepa_product(raw_keepa)
        asin = parsed.get("asin", identifier)
        title = parsed.get("title")

        # Step 2: Force BSR extraction if missing (backup extraction)
        if not parsed.get("current_bsr") and raw_keepa:
            stats = raw_keepa.get('data', {}).get('stats', {})
            current_array = stats.get('current')
            if current_array and isinstance(current_array, (list, tuple)) and len(current_array) > 3:
                bsr_raw = current_array[3]
                if bsr_raw is not None and bsr_raw != -1:
                    parsed["current_bsr"] = bsr_raw
                    logger.info(f"[BSR BACKUP] {asin}: Extracted BSR={bsr_raw} from raw data")

        current_bsr = parsed.get("current_bsr")

        # Step 3: Amazon presence check
        amazon_result = check_amazon_presence(raw_keepa)
        amazon_on_listing = amazon_result.get("amazon_on_listing", False)
        amazon_buybox = amazon_result.get("amazon_buybox", False)

        # Step 4: Extract prices for calculations
        current_price = parsed.get("current_price")
        fba_price = parsed.get("current_fba_price")
        used_price = parsed.get("current_used_price")
        new_price = parsed.get("current_fbm_price")
        weight = parsed.get("weight", 1.0)

        # Step 5: Calculate ROI metrics
        roi_data = {"roi_percentage": 0.0}
        if current_price and fba_price:
            from app.core.calculations import calculate_roi_metrics as calc_roi
            roi_result = calc_roi(
                current_price=Decimal(str(current_price)),
                estimated_buy_cost=Decimal(str(fba_price)),
                product_weight_lbs=Decimal(str(weight)),
                category="books",
                config=config
            )
            roi_data = {
                "roi_percentage": roi_result.get("roi_percentage", 0.0),
                "net_profit": roi_result.get("net_profit", 0.0)
            }
            parsed["roi"] = roi_data

        # Step 6: Calculate velocity metrics
        velocity_score = 0.0
        velocity_breakdown = {}

        if current_bsr:
            velocity_result = calculate_velocity_score(
                parsed_data=parsed,
                config=config
            )
            velocity_score = velocity_result.get("velocity_score", 0.0)
            velocity_breakdown = velocity_result
            parsed["velocity_score"] = velocity_score

            # Add estimated sales
            rank_drops = velocity_result.get("rank_drops_30d", 0) if velocity_result else 0
            estimated_sales_30d = int(rank_drops * 1.5) if rank_drops else 0
            velocity_breakdown["estimated_sales_30d"] = estimated_sales_30d

        # Step 7: Calculate max buy price for 35% ROI
        max_buy_price_35pct = 0.0
        if current_price and current_price > 0:
            try:
                max_buy_price_35pct = calculate_max_buy_price(
                    sell_price=Decimal(str(current_price)),
                    target_roi_pct=35.0,
                    category="books",
                    config=config
                )
            except Exception as e:
                logger.warning(f"[MAX_BUY_ERROR] {asin}: {e}")

        # Step 8: Compute USED vs NEW pricing breakdown
        pricing_breakdown = compute_pricing_breakdown(parsed, amazon_result)

        # Add ROI calculations for USED and NEW
        target_roi = config.get('roi', {}).get('target_roi_percent', 30)

        if used_price and used_price > 0 and current_price:
            used_roi_metrics = calculate_roi_metrics(
                pricing_breakdown={'market_sell_price': current_price},
                source_price=used_price,
                config=config
            )
            pricing_breakdown.setdefault('used', {}).update({
                'roi_percentage': used_roi_metrics.get('current_roi_pct', 0) * 100,
                'net_profit': used_roi_metrics.get('current_roi_value', 0),
                'target_buy_price': float(current_price) * (1 - target_roi / 100)
            })

        if new_price and new_price > 0 and current_price:
            new_roi_metrics = calculate_roi_metrics(
                pricing_breakdown={'market_sell_price': current_price},
                source_price=new_price,
                config=config
            )
            pricing_breakdown.setdefault('new', {}).update({
                'roi_percentage': new_roi_metrics.get('current_roi_pct', 0) * 100,
                'net_profit': new_roi_metrics.get('current_roi_value', 0),
                'target_buy_price': float(current_price) * (1 - target_roi / 100)
            })

        # Step 9: Compute view-specific score if requested
        score_result = {
            "score": 0.0,
            "strategy_profile": strategy,
            "weights_applied": {},
            "components": {},
            "raw_metrics": {}
        }

        if compute_score:
            from app.services.scoring_v2 import compute_view_score
            score_result = compute_view_score(
                parsed_data=parsed,
                view_type=view_type,
                strategy_profile=strategy
            )

        # Step 10: Assemble unified product dict
        unified_product = {
            # Core identifiers
            "asin": asin,
            "title": title,

            # Scoring (only if computed)
            "score": score_result["score"],
            "rank": 0,  # Will be set by caller after sorting
            "strategy_profile": score_result["strategy_profile"],
            "weights_applied": score_result["weights_applied"],
            "components": score_result["components"],
            "raw_metrics": score_result["raw_metrics"],

            # Amazon presence
            "amazon_on_listing": amazon_on_listing,
            "amazon_buybox": amazon_buybox,

            # Market pricing
            "market_sell_price": float(current_price) if current_price else None,
            "market_buy_price": float(fba_price) if fba_price else None,
            "current_roi_pct": roi_data.get("roi_percentage", 0.0),
            "max_buy_price_35pct": float(max_buy_price_35pct),

            # Velocity
            "velocity_breakdown": velocity_breakdown,

            # USED vs NEW pricing
            "pricing": pricing_breakdown if pricing_breakdown else None,

            # BSR - CRITICAL FIELD
            "current_bsr": current_bsr if current_bsr is not None else None,

            # Raw prices (for backward compatibility)
            "current_price": current_price,
            "current_fba_price": fba_price,
            "current_used_price": used_price,
            "current_fbm_price": new_price,

            # Additional metadata
            "weight": weight,
            "error": None
        }

        logger.info(
            f"[UNIFIED] {asin}: Built unified product | "
            f"BSR={current_bsr} | ROI={roi_data.get('roi_percentage', 0):.1f}% | "
            f"Velocity={velocity_score:.1f} | Score={score_result['score']:.1f}"
        )

        return unified_product

    except Exception as e:
        logger.error(f"[UNIFIED_ERROR] {identifier}: {str(e)}")
        # Return error product structure
        return {
            "asin": identifier,
            "title": None,
            "score": 0.0,
            "rank": 0,
            "strategy_profile": None,
            "weights_applied": {},
            "components": {},
            "raw_metrics": {},
            "amazon_on_listing": False,
            "amazon_buybox": False,
            "market_sell_price": None,
            "market_buy_price": None,
            "current_roi_pct": None,
            "max_buy_price_35pct": None,
            "velocity_breakdown": None,
            "pricing": None,
            "current_bsr": None,
            "current_price": None,
            "current_fba_price": None,
            "current_used_price": None,
            "current_fbm_price": None,
            "weight": None,
            "error": str(e)
        }


# ============================================================================
# Batch Processing Helper
# ============================================================================

async def process_product_batch(
    identifiers: List[str],
    keepa_service: Any,
    config: Dict[str, Any],
    view_type: str = "mes_niches",
    strategy: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Process a batch of products through unified analysis.

    Args:
        identifiers: List of ASINs/ISBNs to process
        keepa_service: KeepaService instance
        config: Business configuration
        view_type: View type for scoring
        strategy: Optional strategy override

    Returns:
        List of unified product dicts, sorted by score descending
    """

    products = []

    for identifier in identifiers:
        try:
            # Fetch Keepa data
            raw_keepa = await keepa_service.get_product_data(identifier, force_refresh=False)

            if not raw_keepa:
                logger.warning(f"No Keepa data for {identifier}")
                products.append({
                    "asin": identifier,
                    "error": "No data available from Keepa",
                    # ... other fields with None/0 defaults
                })
                continue

            # Build unified product
            unified = await build_unified_product(
                raw_keepa=raw_keepa,
                keepa_service=keepa_service,
                config=config,
                view_type=view_type,
                strategy=strategy
            )

            products.append(unified)

        except Exception as e:
            logger.error(f"Failed to process {identifier}: {e}")
            products.append({
                "asin": identifier,
                "error": str(e),
                # ... other fields with None/0 defaults
            })

    # Sort by score and assign ranks
    products.sort(key=lambda x: x.get("score", 0), reverse=True)
    for idx, product in enumerate(products, start=1):
        product["rank"] = idx

    return products


# ============================================================================
# PHASE 3: UNIFIED PRODUCT BUILDER v2 - Used by ALL endpoints
# ============================================================================

async def build_unified_product_v2(
    raw_keepa: Dict[str, Any],
    keepa_service: Any,
    config: Dict[str, Any],
    view_type: str = "analyse_manuelle",
    strategy: Optional[str] = None,
    compute_score: bool = True,
    source_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    UNIFIED product builder v2 - Used by ALL endpoints (Analyse Manuelle, Mes Niches, AutoSourcing).

    Consolidates ALL pricing extraction and ROI calculation with SINGLE source of truth.

    Args:
        raw_keepa: Raw Keepa API response data
        keepa_service: KeepaService instance
        config: Business configuration with amazon_fee_pct, shipping_cost
        view_type: "analyse_manuelle" | "mes_niches" | "autosourcing"
        strategy: Optional strategy override (for AutoSourcing/Mes Niches)
        compute_score: Whether to compute scoring (False for Analyse Manuelle)
        source_price: Acquisition cost (used by Analyse Manuelle, optional for others)

    Returns:
        Complete unified product response with:
        - pricing.by_condition: ROI for each condition (new, very_good, good, acceptable)
        - pricing.recommended_condition: Best ROI condition
        - pricing.current_prices: Amazon/New/Used/FBA prices
        - velocity: BSR and velocity metrics
        - amazon_on_listing / amazon_buybox: Amazon presence
        - score/rank: For Mes Niches/AutoSourcing only
    """
    asin = raw_keepa.get('asin', 'UNKNOWN')

    try:
        # ====== STEP 1: Parse with unified parser (Phase 1) ======
        parsed = parse_keepa_product_unified(raw_keepa)
        title = parsed.get("title")
        current_bsr = parsed.get("current_bsr")

        # ====== STEP 2: Amazon presence check ======
        amazon_result = check_amazon_presence(raw_keepa)
        amazon_on_listing = amazon_result.get("amazon_on_listing", False)
        amazon_buybox = amazon_result.get("amazon_buybox", False)

        # ====== STEP 3: Calculate pricing metrics (Phase 2) ======
        # Use provided source_price or config default
        effective_source_price = source_price or config.get('default_source_price', 8.0)

        pricing_metrics = calculate_pricing_metrics_unified(
            parsed_data=parsed,
            source_price=effective_source_price,
            config=config
        )

        # ====== STEP 3.5: Calculate INTRINSIC VALUE pricing (Phase 4 - Textbook Pivot) ======
        # This uses historical median instead of snapshot prices for accurate ROI
        intrinsic_metrics = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed,
            source_price=effective_source_price,
            config=config,
            strategy=strategy or 'balanced'
        )

        # Extract intrinsic value fields for unified response
        intrinsic_value = intrinsic_metrics.get('intrinsic_value', {})
        intrinsic_sell_price = intrinsic_metrics.get('sell_price_used')
        intrinsic_roi_pct = intrinsic_metrics.get('roi_pct', 0.0)
        pricing_confidence = intrinsic_metrics.get('pricing_confidence', 'INSUFFICIENT_DATA')
        pricing_source = intrinsic_metrics.get('pricing_source', 'no_price_available')
        current_vs_intrinsic_pct = intrinsic_metrics.get('current_vs_intrinsic_pct')

        # ====== STEP 4: Extract current prices ======
        current_prices = {
            'amazon': parsed.get('current_amazon_price'),
            'new': parsed.get('current_new_price'),
            'used': parsed.get('current_used_price'),
            'fba': parsed.get('current_fba_price'),
            'list': parsed.get('current_list_price'),
        }

        # ====== STEP 5: Determine recommended condition ======
        recommended_condition = next(
            (k for k, v in pricing_metrics.items() if v.get('is_recommended')),
            'good'  # Fallback
        )

        # ====== STEP 6: Calculate velocity metrics ======
        velocity_metrics = calculate_velocity_score(parsed, config)

        # ====== STEP 6.5: Calculate ADVANCED SCORING (0-100 scale) ======
        # Extract history data for advanced scoring
        # Ensure we always have lists, not ints or None
        bsr_history_raw = parsed.get('bsr_history', [])
        price_history_raw = parsed.get('price_history', [])

        # Safety: Convert to empty list if not already a list
        bsr_history = bsr_history_raw if isinstance(bsr_history_raw, list) else []
        price_history = price_history_raw if isinstance(price_history_raw, list) else []
        data_age_days = 1  # Assume recent data (could be enhanced with actual age calculation)

        # Compute advanced scores
        velocity_raw, velocity_normalized, velocity_level, velocity_notes = compute_advanced_velocity_score(
            bsr_history, config
        )

        stability_raw, stability_normalized, stability_level, stability_notes = compute_advanced_stability_score(
            price_history, config
        )

        confidence_raw, confidence_normalized, confidence_level, confidence_notes = compute_advanced_confidence_score(
            price_history, bsr_history, data_age_days, config
        )

        # Calculate ROI percentage from best condition
        best_roi_condition = pricing_metrics.get(
            next((k for k, v in pricing_metrics.items() if v.get('is_recommended')), 'good'),
            {}
        )
        roi_percentage = best_roi_condition.get('roi_pct', 0.0) * 100  # Convert to percentage

        # Compute overall rating
        overall_rating = compute_overall_rating(
            roi_percentage, velocity_normalized, stability_normalized, confidence_normalized, config
        )

        # Build score breakdown
        score_breakdown = {
            "velocity": {
                "score": velocity_normalized,
                "raw": velocity_raw,
                "level": velocity_level,
                "notes": velocity_notes
            },
            "stability": {
                "score": stability_normalized,
                "raw": stability_raw,
                "level": stability_level,
                "notes": stability_notes
            },
            "confidence": {
                "score": confidence_normalized,
                "raw": confidence_raw,
                "level": confidence_level,
                "notes": confidence_notes
            }
        }

        # Generate readable summary
        scores_dict = {
            "velocity": velocity_normalized,
            "stability": stability_normalized,
            "confidence": confidence_normalized
        }
        readable_summary = generate_readable_summary(roi_percentage, overall_rating, scores_dict, config)

        # Determine recommendation based on overall rating
        recommendation_map = {
            "EXCELLENT": "STRONG BUY - Excellent opportunity",
            "GOOD": "BUY - Good opportunity",
            "FAIR": "CONSIDER - Marginal opportunity",
            "PASS": "PASS - Does not meet criteria",
            "ERROR": "ERROR - Analysis failed"
        }
        recommendation = recommendation_map.get(overall_rating, "PASS")

        # Build risk factors list
        risk_factors = []
        if velocity_normalized < 50:
            risk_factors.append("Low sales velocity")
        if stability_normalized < 50:
            risk_factors.append("Price volatility detected")
        if confidence_normalized < 50:
            risk_factors.append("Limited historical data")
        if amazon_on_listing:
            risk_factors.append("Amazon competing on listing")
        if roi_percentage < 20:
            risk_factors.append("Low ROI potential")
        if not risk_factors:
            risk_factors = ["No major risks identified"]

        # ====== STEP 6.6: Calculate BUYING GUIDANCE (Textbook UX Simplification) ======
        # This transforms intrinsic corridor data into user-friendly buying recommendations
        buying_guidance_service = BuyingGuidanceService()

        # Prepare velocity data for days-to-sell estimation
        velocity_for_guidance = {
            'monthly_sales': velocity_metrics.get('estimated_sales_30d', 0) if velocity_metrics else 0,
            'velocity_tier': velocity_metrics.get('velocity_tier', 'unknown') if velocity_metrics else 'unknown',
        }

        # Calculate comprehensive buying guidance
        guidance_result = buying_guidance_service.calculate_guidance(
            intrinsic_result=intrinsic_value,
            velocity_data=velocity_for_guidance,
            source_price=effective_source_price,
        )

        # Convert dataclass to dict for JSON serialization
        buying_guidance = {
            'max_buy_price': guidance_result.max_buy_price,
            'target_sell_price': guidance_result.target_sell_price,
            'estimated_profit': guidance_result.estimated_profit,
            'estimated_roi_pct': guidance_result.estimated_roi_pct,
            'price_range': guidance_result.price_range,
            'estimated_days_to_sell': guidance_result.estimated_days_to_sell,
            'recommendation': guidance_result.recommendation,
            'recommendation_reason': guidance_result.recommendation_reason,
            'confidence_label': guidance_result.confidence_label,
            'explanations': guidance_result.explanations,
        }

        # ====== STEP 7: Build core response ======
        response = {
            'asin': asin,
            'title': title,

            # Pricing breakdown by condition (UNIFIED!)
            'pricing': {
                'current_prices': current_prices,
                'by_condition': pricing_metrics,
                'recommended_condition': recommended_condition,
                'source_price': effective_source_price,  # Transparent pricing
            },

            # Velocity and market indicators
            'velocity': velocity_metrics,
            'current_bsr': current_bsr,

            # Amazon presence
            'amazon_on_listing': amazon_on_listing,
            'amazon_buybox': amazon_buybox,

            # Advanced scoring fields (0-100 scale) - NEW
            'velocity_score': velocity_normalized,
            'price_stability_score': stability_normalized,
            'confidence_score': confidence_normalized,
            'overall_rating': overall_rating,
            'score_breakdown': score_breakdown,
            'readable_summary': readable_summary,
            'recommendation': recommendation,
            'risk_factors': risk_factors,

            # Strategy profile
            'strategy_profile': strategy or 'balanced',

            # View-specific fields
            'view_type': view_type,
            'timestamp': datetime.now().isoformat(),

            # ====== INTRINSIC VALUE fields (Phase 4 - Textbook Pivot) ======
            # These provide accurate ROI based on historical median pricing
            'intrinsic_value': intrinsic_value,              # Full corridor dict (low, median, high, confidence, etc.)
            'intrinsic_roi_pct': intrinsic_roi_pct,          # ROI based on intrinsic median
            'intrinsic_sell_price': intrinsic_sell_price,    # The intrinsic median price used for calculation
            'pricing_confidence': pricing_confidence,         # HIGH/MEDIUM/LOW/INSUFFICIENT_DATA
            'pricing_source': pricing_source,                 # intrinsic_median or current_price_fallback
            'current_vs_intrinsic_pct': current_vs_intrinsic_pct,  # Gap percentage between current and intrinsic

            # ====== BUYING GUIDANCE (Textbook UX Simplification) ======
            # User-friendly buying recommendations with explanations
            'buying_guidance': buying_guidance,
        }

        # ====== STEP 8: Add scoring for Mes Niches/AutoSourcing ======
        best_roi_condition = pricing_metrics.get(recommended_condition, {})

        if compute_score and view_type in ['mes_niches', 'auto_sourcing', 'niche_discovery']:
            # Get weights from VIEW_WEIGHTS (single source of truth from scoring_v2)
            weights = VIEW_WEIGHTS.get(view_type, VIEW_WEIGHTS.get('dashboard', {}))
            roi_weight = weights.get('roi', 0.5)
            velocity_weight = weights.get('velocity', 0.5)
            stability_weight = weights.get('stability', 0.3)

            # Extract raw metrics (normalized to 0-100)
            roi_pct_raw = best_roi_condition.get('roi_pct', 0) * 100  # Convert decimal to percentage
            velocity_raw = velocity_metrics.get('velocity_score', 0)
            # Default stability to 50 (neutral) if missing - represents average market stability
            stability_raw = stability_normalized if stability_normalized else 50

            # Clamp metrics to 0-100 range
            roi_norm = max(0, min(100, roi_pct_raw))
            velocity_norm = max(0, min(100, velocity_raw))
            stability_norm = max(0, min(100, stability_raw))

            # Calculate weighted score (ROI + Velocity + Stability with view-specific weights)
            score_value = (
                roi_norm * roi_weight +
                velocity_norm * velocity_weight +
                stability_norm * stability_weight
            )
            # Normalize by total weights to get 0-100 scale
            total_weight = roi_weight + velocity_weight + stability_weight
            if total_weight > 0:
                score_value = score_value / total_weight
            score_value = max(0, min(100, score_value))

            weights_applied = {'roi': roi_weight, 'velocity': velocity_weight, 'stability': stability_weight}

            response.update({
                'score': round(score_value, 1),
                'strategy_profile': strategy or 'balanced',
                'weights_applied': weights_applied,
                'components': {
                    'roi': roi_norm * roi_weight / total_weight if total_weight > 0 else 0,
                    'velocity': velocity_norm * velocity_weight / total_weight if total_weight > 0 else 0,
                    'stability': stability_norm * stability_weight / total_weight if total_weight > 0 else 0,
                },
                'raw_metrics': {
                    'roi_pct': roi_pct_raw,
                    'velocity_score': velocity_raw,
                    'stability_score': stability_raw,
                },
            })

        logger.info(
            f"[UNIFIED_V2] {asin}: "
            f"view={view_type}, "
            f"best_roi={recommended_condition}({best_roi_condition.get('roi_pct', 0)*100:+.1f}%), "
            f"bsr={current_bsr}"
        )

        return response

    except Exception as e:
        logger.error(f"[UNIFIED_V2] Error building {asin}: {str(e)}", exc_info=True)
        return {
            "asin": asin,
            "title": None,
            "error": str(e),
            "view_type": view_type,
            "pricing": {},
            "velocity": {},
            "current_bsr": None,
            "amazon_on_listing": False,
            "amazon_buybox": False,

            # Score field required for sorting (defensive)
            "score": 0,

            # Required for ProductScore schema validation
            "weights_applied": {"roi": 0.0, "velocity": 0.0, "stability": 0.0},
            "components": {"roi": 0.0, "velocity": 0.0, "stability": 0.0},
            "raw_metrics": {"roi_pct": 0.0, "velocity_score": 0.0, "stability_score": 0.0},

            # Error state for advanced scoring
            "velocity_score": 0,
            "price_stability_score": 0,
            "confidence_score": 0,
            "overall_rating": "ERROR",
            "score_breakdown": {
                "velocity": {"score": 0, "raw": 0.0, "level": "error", "notes": f"Analysis failed: {str(e)}"},
                "stability": {"score": 0, "raw": 0.0, "level": "error", "notes": f"Analysis failed: {str(e)}"},
                "confidence": {"score": 0, "raw": 0.0, "level": "error", "notes": f"Analysis failed: {str(e)}"}
            },
            "readable_summary": f"[ERROR] Analysis failed: {str(e)}",
            "recommendation": "ERROR",
            "risk_factors": ["Analysis failed"],
            "strategy_profile": None,

            # Intrinsic value fields (Phase 4 - Textbook Pivot) - Error defaults
            "intrinsic_value": {},
            "intrinsic_roi_pct": 0.0,
            "intrinsic_sell_price": None,
            "pricing_confidence": "INSUFFICIENT_DATA",
            "pricing_source": "no_price_available",
            "current_vs_intrinsic_pct": None,

            # Buying guidance (Textbook UX Simplification) - Error defaults
            "buying_guidance": {
                "max_buy_price": 0.0,
                "target_sell_price": 0.0,
                "estimated_profit": 0.0,
                "estimated_roi_pct": 0.0,
                "price_range": "N/A",
                "estimated_days_to_sell": 90,
                "recommendation": "SKIP",
                "recommendation_reason": f"Erreur lors de l'analyse: {str(e)}",
                "confidence_label": "Donnees insuffisantes",
                "explanations": {},
            },
        }