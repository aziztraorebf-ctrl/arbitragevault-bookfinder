"""
Core calculation engine for ROI, velocity, and business metrics.

This module now acts as a facade, importing from specialized sub-modules
for better SRP compliance and maintainability.

Sub-modules:
- roi_calculations: ROI and profitability calculations
- velocity_calculations: Sales velocity and market activity
- advanced_scoring: v1.5.0 config-driven scoring system
"""

from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Import from specialized modules - maintain backward compatibility
from .roi_calculations import (
    calculate_purchase_cost_from_strategy,
    calculate_max_buy_price,
    calculate_roi_metrics,
)

from .velocity_calculations import (
    VelocityData,
    calculate_velocity_score,
)

from .advanced_scoring import (
    compute_advanced_velocity_score,
    compute_advanced_stability_score,
    compute_advanced_confidence_score,
    compute_overall_rating,
    generate_readable_summary,
)


def create_combined_analysis(
    current_price: Decimal,
    estimated_buy_cost: Decimal,
    velocity_data: VelocityData,
    product_weight_lbs: Decimal = Decimal("1.0"),
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create comprehensive analysis combining ROI and velocity metrics.

    This is the main function for full product analysis.
    """
    # Calculate ROI metrics
    roi_metrics = calculate_roi_metrics(
        current_price=current_price,
        estimated_buy_cost=estimated_buy_cost,
        product_weight_lbs=product_weight_lbs,
        category=velocity_data.category,
        config=config
    )

    # Calculate velocity metrics
    velocity_metrics = calculate_velocity_score(velocity_data, config=config)

    # Create combined analysis
    analysis = {
        "analysis_type": "combined_roi_velocity",
        "timestamp": datetime.now().isoformat(),

        # ROI Analysis
        "roi_analysis": roi_metrics,

        # Velocity Analysis
        "velocity_analysis": velocity_metrics,

        # Combined Scoring (with config)
        "combined_score": _calculate_combined_score(roi_metrics, velocity_metrics, config),
        "recommendation": _generate_recommendation(roi_metrics, velocity_metrics, config)
    }

    return analysis


def _calculate_combined_score(
    roi_metrics: Dict,
    velocity_metrics: Dict,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Calculate weighted combined score from ROI and velocity."""
    try:
        roi_score = min(max(float(roi_metrics.get("roi_percentage", 0)), 0), 100)
        velocity_score = float(velocity_metrics.get("velocity_score", 0))

        # Get weights from config or use defaults
        if config and "combined_score" in config:
            roi_weight = config["combined_score"].get("roi_weight", 0.6)
            velocity_weight = config["combined_score"].get("velocity_weight", 0.4)
        else:
            roi_weight = 0.6
            velocity_weight = 0.4

        # Weighted average with config weights
        combined_score = (roi_score * roi_weight) + (velocity_score * velocity_weight)

        return {
            "combined_score": round(combined_score, 2),
            "roi_weight": roi_weight,
            "velocity_weight": velocity_weight,
            "roi_contribution": round(roi_score * roi_weight, 2),
            "velocity_contribution": round(velocity_score * velocity_weight, 2)
        }
    except (ValueError, TypeError, KeyError) as e:
        return {"combined_score": 0, "error": f"Score calculation failed: {e}"}


def _generate_recommendation(
    roi_metrics: Dict,
    velocity_metrics: Dict,
    config: Optional[Dict[str, Any]] = None
) -> str:
    """Generate business recommendation based on combined analysis."""
    try:
        roi_pct = float(roi_metrics.get("roi_percentage", 0))
        velocity_score = float(velocity_metrics.get("velocity_score", 0))
        is_profitable = roi_metrics.get("is_profitable", False)

        if not is_profitable:
            return "PASS - Not profitable"

        # Use config recommendation rules if available
        if config and "recommendation_rules" in config:
            rules = config["recommendation_rules"]

            for rule in rules:
                min_roi = rule.get("min_roi", 0)
                min_velocity = rule.get("min_velocity", 0)

                if roi_pct >= min_roi and velocity_score >= min_velocity:
                    label = rule.get("label", "UNKNOWN")
                    description = rule.get("description", "")
                    return f"{label} - {description}" if description else label

            return "PASS - Below configured thresholds"
        else:
            # Default fallback rules
            if roi_pct >= 30 and velocity_score >= 70:
                return "STRONG BUY - High profit, fast moving"
            elif roi_pct >= 20 and velocity_score >= 50:
                return "BUY - Good opportunity"
            elif roi_pct >= 15 or velocity_score >= 60:
                return "CONSIDER - Monitor for better entry"
            else:
                return "PASS - Low profit/slow moving"

    except (ValueError, TypeError, KeyError) as e:
        return f"UNKNOWN - Analysis incomplete: {e}"


# Backward compatibility exports
__all__ = [
    # ROI calculations
    'calculate_purchase_cost_from_strategy',
    'calculate_max_buy_price',
    'calculate_roi_metrics',

    # Velocity calculations
    'VelocityData',
    'calculate_velocity_score',

    # Advanced scoring v1.5.0
    'compute_advanced_velocity_score',
    'compute_advanced_stability_score',
    'compute_advanced_confidence_score',
    'compute_overall_rating',
    'generate_readable_summary',

    # Combined analysis
    'create_combined_analysis',
]
