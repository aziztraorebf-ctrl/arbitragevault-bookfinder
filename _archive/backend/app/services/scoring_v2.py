"""
Scoring V2 - View-Specific Adaptive Scoring System

Implements adaptive product scoring based on frontend view context.
Each view has distinct weight priorities for ROI, velocity, and stability metrics.

Phase 2 of Strategy Refactor (strategy_refactor_v2_phase2_views)
"""

from typing import Dict, Any, Optional, List
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# VIEW_WEIGHTS Matrix
# ============================================================================
# Defines scoring priorities per frontend view
# Each weight represents the importance coefficient for that metric in [0-1] range

VIEW_WEIGHTS = {
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
    },
    "analyse_strategique": {
        "roi": 0.4,
        "velocity": 0.6,
        "stability": 0.2,
        "description": "Strategic analysis - Velocity priority for fast movers"
    },
    "auto_sourcing": {
        "roi": 0.3,
        "velocity": 0.7,
        "stability": 0.1,
        "description": "Automated sourcing - Maximum velocity for automation"
    },
    "stock_estimates": {
        "roi": 0.45,
        "velocity": 0.45,
        "stability": 0.6,
        "description": "Stock forecasting - Stability priority for predictions"
    },
    "niche_discovery": {
        "roi": 0.5,
        "velocity": 0.5,
        "stability": 0.4,
        "description": "Discovery mode - Balanced exploration with stability"
    }
}

# Strategy boost multipliers (optional enhancement)
STRATEGY_BOOSTS = {
    "textbook": {"roi": 1.2, "velocity": 1.0, "stability": 1.1},
    "velocity": {"roi": 1.0, "velocity": 1.2, "stability": 0.9},
    "balanced": {"roi": 1.0, "velocity": 1.0, "stability": 1.0}
}


# ============================================================================
# Core Scoring Function
# ============================================================================

def compute_view_score(
    parsed_data: Dict[str, Any],
    view_type: str,
    strategy_profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate adaptive score based on view context and strategy profile.

    Args:
        parsed_data: Keepa parsed product data from keepa_parser_v2.py
            Expected keys:
            - roi: dict with "roi_percentage" key
            - velocity_score: float (0-100)
            - stability_score: float (0-100) - optional, defaults to 50
        view_type: Frontend view identifier (dashboard, mes_niches, etc.)
        strategy_profile: textbook | velocity | balanced (optional boost)

    Returns:
        {
            "score": float (0-100),
            "view_type": str,
            "strategy_profile": str or None,
            "weights_applied": dict,
            "components": {
                "roi_contribution": float,
                "velocity_contribution": float,
                "stability_contribution": float
            },
            "raw_metrics": {
                "roi_pct": float,
                "velocity_score": float,
                "stability_score": float
            }
        }

    Business Rules:
        - Invalid view_type → fallback to "dashboard" weights
        - Missing metrics → default to 0 (roi/velocity) or 50 (stability)
        - Metrics normalized to [0-100] range
        - Strategy boosts applied after base calculation (optional)
    """
    # 1. Get weights for view (fallback to dashboard if invalid)
    weights = VIEW_WEIGHTS.get(view_type, VIEW_WEIGHTS["dashboard"])
    if view_type not in VIEW_WEIGHTS:
        logger.warning(
            f"Invalid view_type '{view_type}', falling back to 'dashboard' weights"
        )
        view_type = "dashboard"

    # 2. Extract raw metrics from parsed_data
    roi_pct = _extract_roi_percentage(parsed_data)
    velocity_score = _extract_velocity_score(parsed_data)
    stability_score = _extract_stability_score(parsed_data)

    # 3. Normalize metrics to [0-100] range
    roi_norm = _normalize_metric(roi_pct, 0, 100)
    velocity_norm = _normalize_metric(velocity_score, 0, 100)
    stability_norm = _normalize_metric(stability_score, 0, 100)

    # 4. Calculate weighted base score
    base_score = (
        roi_norm * weights["roi"] +
        velocity_norm * weights["velocity"] +
        stability_norm * weights["stability"]
    )

    # 5. Apply strategy boost (if provided)
    final_score = base_score
    boost_applied = None
    if strategy_profile and strategy_profile in STRATEGY_BOOSTS:
        boosts = STRATEGY_BOOSTS[strategy_profile]
        boosted_score = (
            roi_norm * weights["roi"] * boosts["roi"] +
            velocity_norm * weights["velocity"] * boosts["velocity"] +
            stability_norm * weights["stability"] * boosts["stability"]
        )
        final_score = boosted_score
        boost_applied = strategy_profile
        logger.debug(
            f"Applied '{strategy_profile}' boost: {base_score:.2f} -> {final_score:.2f}"
        )

    # 5b. Clamp final score to [0, 100] range
    final_score = max(0.0, min(100.0, final_score))

    # 6. Calculate individual contributions (for transparency)
    roi_contribution = roi_norm * weights["roi"]
    velocity_contribution = velocity_norm * weights["velocity"]
    stability_contribution = stability_norm * weights["stability"]

    return {
        "score": round(final_score, 2),
        "view_type": view_type,
        "strategy_profile": boost_applied,
        "weights_applied": {
            "roi": weights["roi"],
            "velocity": weights["velocity"],
            "stability": weights["stability"]
        },
        "components": {
            "roi_contribution": round(roi_contribution, 2),
            "velocity_contribution": round(velocity_contribution, 2),
            "stability_contribution": round(stability_contribution, 2)
        },
        "raw_metrics": {
            "roi_pct": round(roi_norm, 2),
            "velocity_score": round(velocity_norm, 2),
            "stability_score": round(stability_norm, 2)
        }
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _extract_roi_percentage(parsed_data: Dict[str, Any]) -> float:
    """
    Extract ROI percentage from parsed Keepa data.

    Args:
        parsed_data: Product data dictionary

    Returns:
        ROI percentage as float (can be negative, > 100, etc.)
        Defaults to 0.0 if missing
    """
    try:
        roi_dict = parsed_data.get("roi", {})
        if isinstance(roi_dict, dict):
            return float(roi_dict.get("roi_percentage", 0.0))
        return 0.0
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"Failed to extract ROI percentage: {e}")
        return 0.0


def _extract_velocity_score(parsed_data: Dict[str, Any]) -> float:
    """
    Extract velocity score from parsed Keepa data.

    Args:
        parsed_data: Product data dictionary

    Returns:
        Velocity score as float [0-100]
        Defaults to 0.0 if missing
    """
    try:
        return float(parsed_data.get("velocity_score", 0.0))
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to extract velocity_score: {e}")
        return 0.0


def _extract_stability_score(parsed_data: Dict[str, Any]) -> float:
    """
    Extract stability score from parsed Keepa data.

    Args:
        parsed_data: Product data dictionary

    Returns:
        Stability score as float [0-100]
        Defaults to 50.0 (neutral) if missing
    """
    try:
        # Default to 50 (neutral) instead of 0 for missing stability
        return float(parsed_data.get("stability_score", 50.0))
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to extract stability_score: {e}")
        return 50.0


def _normalize_metric(value: float, min_val: float, max_val: float) -> float:
    """
    Normalize metric to [0-100] range with boundary clamping.

    Args:
        value: Raw metric value
        min_val: Minimum expected value
        max_val: Maximum expected value

    Returns:
        Normalized value clamped to [0-100]

    Examples:
        _normalize_metric(150, 0, 100) → 100.0  (clamp upper)
        _normalize_metric(-50, 0, 100) → 0.0    (clamp lower)
        _normalize_metric(75, 0, 100) → 75.0    (within range)
    """
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_view_type(view_type: str) -> bool:
    """
    Check if view_type is valid.

    Args:
        view_type: View identifier to validate

    Returns:
        True if valid, False otherwise
    """
    return view_type in VIEW_WEIGHTS


def get_available_views() -> List[str]:
    """
    Get list of all available view types.

    Returns:
        List of valid view identifiers
    """
    return list(VIEW_WEIGHTS.keys())


def get_view_description(view_type: str) -> Optional[str]:
    """
    Get human-readable description for a view type.

    Args:
        view_type: View identifier

    Returns:
        Description string or None if invalid view_type
    """
    weights = VIEW_WEIGHTS.get(view_type)
    if weights:
        return weights.get("description")
    return None
