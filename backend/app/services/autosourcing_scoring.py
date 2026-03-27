"""
AutoSourcing Scoring Helpers - Extracted from autosourcing_service.py for SRP.

Contains:
- ROI calculation (was duplicated in _analyze_product_from_batch and _analyze_single_product)
- Condition signal evaluation (same duplication)
- Velocity/stability/confidence scoring from Keepa data
- Overall rating computation
- Criteria matching and tier classification
"""
import math
import logging
from typing import Any, Dict, Optional, Tuple

from app.models.autosourcing import AutoSourcingPick

logger = logging.getLogger(__name__)


def calculate_product_roi(
    current_price: float,
    source_price_factor: float,
    fba_fee_percentage: float,
) -> Tuple[float, float, float]:
    """
    Calculate ROI metrics for a product.

    Returns:
        (estimated_cost, profit_net, roi_percentage)
    """
    estimated_cost = current_price * source_price_factor
    amazon_fees = current_price * fba_fee_percentage
    profit_net = current_price - estimated_cost - amazon_fees
    roi_percentage = (profit_net / estimated_cost) * 100 if estimated_cost > 0 else 0
    return estimated_cost, profit_net, roi_percentage


def evaluate_condition_signal(
    product_data: Dict[str, Any],
    estimated_cost: float,
    fba_fee_percentage: float,
    cs_config: Dict[str, Any],
) -> Tuple[Optional[float], str]:
    """
    Evaluate condition signal from used price data.

    Returns:
        (used_roi_percentage, condition_signal)
    """
    used_price = product_data.get("used_price")
    used_offer_count = product_data.get("used_offer_count", 0)
    used_roi_percentage = None
    condition_signal = "UNKNOWN"

    if used_price is not None and used_price > 0:
        used_fees = used_price * fba_fee_percentage
        used_profit = used_price - estimated_cost - used_fees
        used_roi_percentage = (used_profit / estimated_cost) * 100 if estimated_cost > 0 else 0.0

        strong_roi_min = cs_config.get("strong_roi_min", 25.0)
        moderate_roi_min = cs_config.get("moderate_roi_min", 10.0)
        max_offers_strong = cs_config.get("max_used_offers_strong", 10)
        max_offers_moderate = cs_config.get("max_used_offers_moderate", 25)

        if used_roi_percentage >= strong_roi_min and (used_offer_count or 0) <= max_offers_strong:
            condition_signal = "STRONG"
        elif used_roi_percentage >= moderate_roi_min and (used_offer_count or 0) <= max_offers_moderate:
            condition_signal = "MODERATE"
        else:
            condition_signal = "WEAK"

    return used_roi_percentage, condition_signal


def calculate_velocity_from_keepa(raw_keepa: Dict[str, Any], bsr: int) -> float:
    """Calculate velocity score from real Keepa data."""
    if bsr <= 0:
        return 50.0

    velocity = max(10, min(100, 130 - (math.log10(bsr) * 20)))

    stats = raw_keepa.get("stats", {})
    current_stats = stats.get("current", [])

    if current_stats and len(current_stats) > 18 and current_stats[18]:
        velocity = min(100, velocity + 10)

    return velocity


def calculate_stability_from_keepa(raw_keepa: Dict[str, Any]) -> float:
    """Calculate price stability score from real Keepa data."""
    stats = raw_keepa.get("stats", {})
    current_stats = stats.get("current", [])
    avg30_stats = stats.get("avg30", [])

    if not current_stats or not avg30_stats:
        return 70.0

    if len(current_stats) > 1 and len(avg30_stats) > 1:
        current_price = current_stats[1]
        avg30_price = avg30_stats[1]

        if current_price and avg30_price and avg30_price > 0:
            variance = abs(current_price - avg30_price) / avg30_price
            stability = max(30, min(100, 100 - (variance * 100)))
            return stability

    return 70.0


def calculate_confidence_from_keepa(
    raw_keepa: Dict[str, Any],
    condition_signal: Optional[str] = None,
    business_config: Optional[Dict[str, Any]] = None,
) -> float:
    """Calculate confidence score from real Keepa data completeness."""
    confidence = 50.0

    if raw_keepa.get("title"):
        confidence += 10

    stats = raw_keepa.get("stats", {})
    if stats.get("current"):
        confidence += 15
    if stats.get("avg30"):
        confidence += 10

    if raw_keepa.get("salesRanks"):
        confidence += 10

    last_update = raw_keepa.get("lastUpdate", 0)
    if last_update > 0:
        confidence += 5

    if condition_signal:
        config = business_config or {}
        if condition_signal == "STRONG":
            confidence += config.get("confidence_boost_strong", 10)
        elif condition_signal == "MODERATE":
            confidence += config.get("confidence_boost_moderate", 5)

    return min(100, confidence)


def compute_rating(
    roi: float, velocity: float, stability: float,
    confidence: float, config: Dict[str, Any],
) -> str:
    """Compute overall rating based on thresholds."""
    roi_min = config.get("roi_min", 30)
    velocity_min = config.get("velocity_min", 70)
    stability_min = config.get("stability_min", 70)
    confidence_min = config.get("confidence_min", 70)

    if (roi >= roi_min and velocity >= velocity_min and
            stability >= stability_min and confidence >= confidence_min):
        return "EXCELLENT"
    elif (roi >= roi_min * 0.8 and velocity >= velocity_min * 0.85 and
          stability >= stability_min * 0.85 and confidence >= confidence_min * 0.85):
        return "GOOD"
    elif roi >= roi_min * 0.7:
        return "FAIR"
    else:
        return "PASS"


def meets_criteria(pick: AutoSourcingPick, scoring_config: Dict[str, Any]) -> bool:
    """Check if pick meets minimum criteria including velocity threshold."""
    rating_required = scoring_config.get("rating_required", "FAIR")
    roi_min = scoring_config.get("roi_min", 20)
    velocity_min = scoring_config.get("velocity_min", 0)

    rating_hierarchy = {"PASS": 0, "FAIR": 1, "GOOD": 2, "EXCELLENT": 3}

    pick_rating_level = rating_hierarchy.get(pick.overall_rating, 0)
    required_rating_level = rating_hierarchy.get(rating_required, 1)

    if velocity_min > 0 and pick.velocity_score < velocity_min:
        return False

    condition_signals_config = scoring_config.get("condition_signals", {})
    if condition_signals_config.get("reject_weak", False):
        if pick.condition_signal and pick.condition_signal == "WEAK":
            return False

    return (pick_rating_level >= required_rating_level and
            pick.roi_percentage >= roi_min)


def should_reject_by_competition(
    fba_seller_count: int | None,
    max_fba_sellers: int | None,
) -> bool:
    """Return True if product should be rejected due to too many FBA sellers.

    If either value is None, do not reject (incomplete data or no max configured).
    """
    if fba_seller_count is None or max_fba_sellers is None:
        return False
    return fba_seller_count > max_fba_sellers


def should_reject_by_profit_floor(
    profit_net: float | None,
    min_profit_dollars: float | None,
) -> bool:
    """Return True if net profit is below the configured minimum.

    If either value is None, do not reject.
    """
    if profit_net is None or min_profit_dollars is None:
        return False
    return profit_net < min_profit_dollars


def classify_product_tier(product_data: Dict[str, Any]) -> Tuple[str, str]:
    """Classify product tier for AutoScheduler (HOT/TOP/WATCH/OTHER)."""
    roi = product_data.get("roi_percentage", 0)
    profit = product_data.get("profit_net", 0)
    velocity = product_data.get("velocity_score", 0)
    confidence = product_data.get("confidence_score", 0)
    rating = product_data.get("overall_rating", "PASS")

    if (roi >= 50 and profit >= 15 and velocity >= 80 and
            confidence >= 85 and rating in ["EXCELLENT"]):
        return "HOT", f"[HOT] {roi:.0f}% ROI, ${profit:.0f} profit, {velocity:.0f} velocity - Action immediate!"

    elif (roi >= 35 and profit >= 10 and velocity >= 70 and
          confidence >= 75 and rating in ["EXCELLENT", "GOOD"]):
        return "TOP", f"[TOP] {roi:.0f}% ROI, ${profit:.0f} profit - Opportunite solide"

    elif (roi >= 25 and profit >= 5 and velocity >= 60 and
          confidence >= 65 and rating in ["EXCELLENT", "GOOD", "FAIR"]):
        return "WATCH", f"[WATCH] {roi:.0f}% ROI, potentiel a surveiller"

    else:
        return "OTHER", f"[INFO] {roi:.0f}% ROI - Analyse detaillee recommandee"
