"""
Keepa Router - Utility Functions
================================
Helper functions for Keepa API endpoints.

Separated from keepa.py for SRP compliance.
"""

import uuid
import logging
from typing import Dict, Any, Optional, List

from app.services.keepa_service import KeepaService
from app.services.unified_analysis import build_unified_product_v2
from .keepa_schemas import AnalysisResult, PricingDetail, ScoreBreakdown

logger = logging.getLogger(__name__)


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
    source_price: Optional[float] = None,
    condition_filter: Optional[List[str]] = None
) -> AnalysisResult:
    """
    Analyze a single product with given config.
    Uses build_unified_product_v2() for unified pricing extraction.

    Args:
        asin: Product ASIN
        keepa_data: Raw Keepa API response
        config: Business configuration
        keepa_service: Keepa service instance
        source_price: Optional source/acquisition price override
        condition_filter: Filter offers by condition (e.g., ['new', 'very_good', 'good'])
                         If None, all conditions are included (backward compatible)
    """
    try:
        # Use build_unified_product_v2() for unified pricing
        unified_product = await build_unified_product_v2(
            raw_keepa=keepa_data,
            keepa_service=keepa_service,
            config=config,
            view_type='analyse_manuelle',
            compute_score=False,
            source_price=source_price,
            condition_filter=condition_filter
        )

        # Convert pricing structure to match AnalysisResult schema
        pricing_unified = unified_product.get('pricing', {})
        pricing_by_condition = pricing_unified.get('by_condition', {})

        # Map to PricingDetail format expected by AnalysisResult
        pricing_breakdown = {}
        for condition, details in pricing_by_condition.items():
            pricing_breakdown[condition] = PricingDetail(
                current_price=details.get('buy_price'),
                target_buy_price=details.get('max_buy_price', 0),
                roi_percentage=details.get('roi_pct', 0) * 100 if details.get('roi_pct') else None,
                net_profit=details.get('profit'),
                available=details.get('buy_price') is not None,
                recommended=details.get('is_recommended', False)
            )

        # Convert score_breakdown dict to ScoreBreakdown objects
        score_breakdown_raw = unified_product.get('score_breakdown', {})
        score_breakdown_typed = {}
        for key, breakdown in score_breakdown_raw.items():
            score_breakdown_typed[key] = ScoreBreakdown(
                score=breakdown.get('score', 0),
                raw=breakdown.get('raw', 0.0),
                level=breakdown.get('level', 'unknown'),
                notes=breakdown.get('notes', '')
            )

        # Extract current price from unified pricing
        current_price_raw = pricing_unified.get('current_prices', {}).get('amazon')
        if not current_price_raw:
            current_price_raw = pricing_unified.get('current_prices', {}).get('used')

        return AnalysisResult(
            asin=asin,
            title=unified_product.get('title'),
            current_price=current_price_raw,
            current_bsr=unified_product.get('current_bsr'),

            # Pricing breakdown
            pricing=pricing_breakdown,

            # ROI and velocity (legacy format for compatibility)
            roi=unified_product.get('velocity', {}),
            velocity=unified_product.get('velocity', {}),

            # Advanced scoring (0-100 scale)
            velocity_score=unified_product.get('velocity_score', 0),
            price_stability_score=unified_product.get('price_stability_score', 0),
            confidence_score=unified_product.get('confidence_score', 0),
            overall_rating=unified_product.get('overall_rating', 'PASS'),
            score_breakdown=score_breakdown_typed,
            readable_summary=unified_product.get('readable_summary', ''),

            # Strategy profile
            strategy_profile=unified_product.get('strategy_profile'),
            calculation_method=None,

            # Recommendation and risk factors
            recommendation=unified_product.get('recommendation', 'PASS'),
            risk_factors=unified_product.get('risk_factors', [])
        )

    except Exception as e:
        # Error handling with complete AnalysisResult structure
        logger.error(f"Error analyzing {asin}: {str(e)}", exc_info=True)
        return AnalysisResult(
            asin=asin,
            title=None,
            current_price=None,
            current_bsr=None,

            # Empty pricing
            pricing={},

            roi={"error": str(e)},
            velocity={"error": str(e)},

            # Error state for advanced scoring
            velocity_score=0,
            price_stability_score=0,
            confidence_score=0,
            overall_rating="ERROR",
            score_breakdown={
                "velocity": ScoreBreakdown(score=0, raw=0.0, level="error", notes=f"Analysis failed: {str(e)}"),
                "stability": ScoreBreakdown(score=0, raw=0.0, level="error", notes=f"Analysis failed: {str(e)}"),
                "confidence": ScoreBreakdown(score=0, raw=0.0, level="error", notes=f"Analysis failed: {str(e)}")
            },
            readable_summary=f"Analysis failed: {str(e)}",

            # Strategy and recommendation
            strategy_profile=None,
            calculation_method=None,
            recommendation="ERROR",
            risk_factors=["Analysis failed"]
        )


__all__ = [
    'generate_trace_id',
    'normalize_identifier',
    'analyze_product',
]
