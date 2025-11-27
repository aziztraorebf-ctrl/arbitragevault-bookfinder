"""
Advanced Scoring Functions (v1.5.0)
===================================
Config-driven scoring system for velocity, stability, confidence, and overall ratings.

Separated from calculations.py for SRP compliance.
"""

import statistics
from datetime import datetime
from typing import Dict, List, Any, Tuple


def compute_advanced_velocity_score(
    bsr_history: List[Tuple[datetime, int]],
    config: Dict[str, Any]
) -> Tuple[float, int, str, str]:
    """
    Calculate simplified velocity score (0-100) based on BSR trend.

    Args:
        bsr_history: List of (datetime, bsr) pairs
        config: Configuration from business_rules.json

    Returns:
        Tuple of (raw_score, normalized_0_100, level, notes)
    """
    # Safety: Ensure bsr_history is a list
    if not isinstance(bsr_history, list):
        return (0.5, 50, "unknown", "Invalid data type for bsr_history")

    try:
        velocity_config = config.get("advanced_scoring", {}).get("velocity", {})
        min_points = velocity_config.get("min_data_points", 10)
        fallback_score = velocity_config.get("fallback_score", 50)

        # Filter valid BSR data
        valid_bsr = [(dt, bsr) for dt, bsr in bsr_history if bsr and bsr > 0]

        if len(valid_bsr) < min_points:
            return (0.5, fallback_score, "unknown", f"Insufficient data: {len(valid_bsr)} points")

        # CRITICAL FIX: Sort by timestamp to ensure chronological order
        # Parser extracts data in CSV order which may not be sorted
        # We need oldest -> newest for trend calculation
        sorted_bsr = sorted(valid_bsr, key=lambda x: x[0])

        # Simple BSR trend calculation
        bsr_values = [bsr for _, bsr in sorted_bsr]
        recent_avg = statistics.mean(bsr_values[-7:]) if len(bsr_values) >= 7 else statistics.mean(bsr_values)
        older_avg = statistics.mean(bsr_values[:7]) if len(bsr_values) >= 14 else statistics.mean(bsr_values)

        if older_avg > 0:
            # Improvement = lower BSR is better
            improvement = (older_avg - recent_avg) / older_avg
            velocity_raw = 0.5 + (improvement * 0.5)  # Scale to 0-1
            velocity_raw = max(0.0, min(1.0, velocity_raw))  # Clamp
        else:
            velocity_raw = 0.5

        # Convert to 0-100
        velocity_normalized = int(velocity_raw * 100)

        # Determine level
        level = _get_score_level(velocity_normalized, velocity_config)

        notes = f"{len(valid_bsr)} BSR data points, {improvement:.2%} trend" if 'improvement' in locals() else f"{len(valid_bsr)} BSR data points"

        return (velocity_raw, velocity_normalized, level, notes)

    except Exception as e:
        return (0.5, 50, "error", f"Calculation error: {str(e)}")


def compute_advanced_stability_score(
    price_history: List[Tuple[datetime, float]],
    config: Dict[str, Any]
) -> Tuple[float, int, str, str]:
    """
    Calculate price stability score (0-100) based on coefficient of variation.

    Args:
        price_history: List of (datetime, price) pairs
        config: Configuration from business_rules.json

    Returns:
        Tuple of (raw_score, normalized_0_100, level, notes)
    """
    # Safety: Ensure price_history is a list
    if not isinstance(price_history, list):
        return (0.5, 50, "unknown", "Invalid data type for price_history")

    try:
        stability_config = config.get("advanced_scoring", {}).get("stability", {})
        min_points = stability_config.get("min_price_points", 10)
        fallback_score = stability_config.get("fallback_score", 50)

        # Filter valid price data
        valid_prices = [price for _, price in price_history if price and price > 0]

        if len(valid_prices) < min_points:
            return (0.5, fallback_score, "unknown", f"Insufficient price data: {len(valid_prices)} points")

        if len(set(valid_prices)) == 1:
            # Constant price = perfect stability
            return (1.0, 100, "excellent", f"Constant price: ${valid_prices[0]:.2f}")

        # Simple coefficient of variation
        mean_price = statistics.mean(valid_prices)
        std_price = statistics.stdev(valid_prices)
        cv = std_price / mean_price if mean_price > 0 else 0

        # Stability = 1 - CV (clamped to 0-1)
        stability_raw = 1 - min(cv, 1.0)
        stability_raw = max(0.0, stability_raw)

        # Convert to 0-100
        stability_normalized = int(stability_raw * 100)

        # Determine level
        level = _get_score_level(stability_normalized, stability_config)

        notes = f"CV: {cv:.3f}, price range: ${min(valid_prices):.2f}-${max(valid_prices):.2f}"

        return (stability_raw, stability_normalized, level, notes)

    except Exception as e:
        return (0.5, 50, "error", f"Calculation error: {str(e)}")


def compute_advanced_confidence_score(
    price_history: List[Tuple[datetime, float]],
    bsr_data: List[Tuple[datetime, int]],
    data_age_days: int,
    config: Dict[str, Any]
) -> Tuple[float, int, str, str]:
    """
    Calculate data confidence score (0-100) based on freshness, completeness, and BSR availability.

    Args:
        price_history: List of (datetime, price) pairs
        bsr_data: List of (datetime, bsr) pairs
        data_age_days: Age of most recent data in days
        config: Configuration from business_rules.json

    Returns:
        Tuple of (raw_score, normalized_0_100, level, notes)
    """
    # Safety: Ensure price_history and bsr_data are lists
    if not isinstance(price_history, list):
        return (0.5, 50, "unknown", "Invalid data type for price_history")
    if not isinstance(bsr_data, list):
        return (0.5, 50, "unknown", "Invalid data type for bsr_data")

    try:
        confidence_config = config.get("advanced_scoring", {}).get("confidence", {})
        freshness_threshold = confidence_config.get("data_freshness_days", 7)
        weights = confidence_config.get("weights", {"freshness": 0.3, "completeness": 0.4, "bsr_availability": 0.3})

        # Component 1: Data Freshness
        if data_age_days <= freshness_threshold:
            freshness_score = 1.0
        else:
            # Linear decay after threshold
            freshness_score = max(0, 1 - (data_age_days - freshness_threshold) / 30)

        # Component 2: Price Data Completeness
        # Assume 90-day window for completeness calculation
        window_days = 90
        expected_points = window_days
        actual_points = len([p for _, p in price_history if p and p > 0])
        completeness_score = min(actual_points / expected_points, 1.0) if expected_points > 0 else 0

        # Component 3: BSR Availability
        has_recent_bsr = bool(bsr_data and any(bsr for _, bsr in bsr_data if bsr and bsr > 0))
        bsr_availability_score = 1.0 if has_recent_bsr else 0.3  # Partial credit if missing

        # Weighted average
        confidence_raw = (
            freshness_score * weights.get("freshness", 0.3) +
            completeness_score * weights.get("completeness", 0.4) +
            bsr_availability_score * weights.get("bsr_availability", 0.3)
        )

        # Convert to 0-100
        confidence_normalized = int(confidence_raw * 100)

        # Determine level
        level = _get_confidence_level(confidence_normalized, confidence_config)

        notes = f"Fresh: {freshness_score:.2f}, Complete: {completeness_score:.2f}, BSR: {bsr_availability_score:.2f}"

        return (confidence_raw, confidence_normalized, level, notes)

    except Exception as e:
        return (0.5, 50, "error", f"Calculation error: {str(e)}")


def compute_overall_rating(
    roi: float,
    velocity: int,
    stability: int,
    confidence: int,
    config: Dict[str, Any]
) -> str:
    """
    Determine overall rating using gating rules from config.

    Args:
        roi: ROI percentage
        velocity: Velocity score (0-100)
        stability: Stability score (0-100)
        confidence: Confidence score (0-100)
        config: Configuration from business_rules.json

    Returns:
        Overall rating string (EXCELLENT/GOOD/FAIR/PASS)
    """
    try:
        gating_rules = config.get("overall_rating", {}).get("gating_rules", {})

        # Check each rating level from highest to lowest
        for rating in ["EXCELLENT", "GOOD", "FAIR"]:
            rules = gating_rules.get(rating, {})

            roi_min = rules.get("roi_min", 0)
            velocity_min = rules.get("velocity_min", 0)
            stability_min = rules.get("stability_min", 0)
            confidence_min = rules.get("confidence_min", 0)

            if (roi >= roi_min and velocity >= velocity_min and
                stability >= stability_min and confidence >= confidence_min):
                return rating

        return "PASS"  # Falls below all thresholds

    except Exception as e:
        return "ERROR"


def generate_readable_summary(
    roi: float,
    rating: str,
    scores: Dict[str, int],
    config: Dict[str, Any]
) -> str:
    """
    Generate readable summary using templates from config.

    Args:
        roi: ROI percentage
        rating: Overall rating (EXCELLENT/GOOD/FAIR/PASS)
        scores: Dict with velocity, stability, confidence scores
        config: Configuration from business_rules.json

    Returns:
        Formatted summary string
    """
    try:
        templates = config.get("summary_templates", {})
        level_flags = config.get("level_flags", {})

        if rating not in templates:
            return f"Rating: {rating}, ROI: {roi}%"  # Fallback

        template = templates[rating]

        # Get levels for each score
        velocity_level = _get_level_from_flags(scores.get("velocity", 0), level_flags.get("velocity", {}))
        stability_level = _get_level_from_flags(scores.get("stability", 0), level_flags.get("stability", {}))
        confidence_level = _get_level_from_flags(scores.get("confidence", 0), level_flags.get("confidence", {}))

        # Handle PASS case with primary_issue
        if rating == "PASS":
            primary_issue = _determine_primary_issue(roi, scores, config)
            return template.format(roi=roi, primary_issue=primary_issue)

        # Standard template formatting
        return template.format(
            roi=roi,
            velocity_level=velocity_level,
            stability_level=stability_level,
            confidence_level=confidence_level
        )

    except Exception as e:
        return f"Summary generation failed: {roi}% ROI"


def _get_score_level(score: int, score_config: Dict[str, Any]) -> str:
    """Get level name for score using thresholds."""
    excellent = score_config.get("excellent_threshold", 80)
    good = score_config.get("good_threshold", 60)
    fair = score_config.get("fair_threshold", 40)

    if score >= excellent:
        return "excellent"
    elif score >= good:
        return "good"
    elif score >= fair:
        return "fair"
    else:
        return "poor"


def _get_confidence_level(score: int, confidence_config: Dict[str, Any]) -> str:
    """Get confidence level name for score."""
    high = confidence_config.get("high_threshold", 85)
    good = confidence_config.get("good_threshold", 70)
    fair = confidence_config.get("fair_threshold", 50)

    if score >= high:
        return "high"
    elif score >= good:
        return "good"
    elif score >= fair:
        return "fair"
    else:
        return "low"


def _get_level_from_flags(score: int, flags: Dict[str, int]) -> str:
    """Get level name from score using level_flags config."""
    # Sort levels by threshold descending
    sorted_levels = sorted(flags.items(), key=lambda x: x[1], reverse=True)

    for level, threshold in sorted_levels:
        if score >= threshold:
            return level

    return "unknown"


def _determine_primary_issue(roi: float, scores: Dict[str, int], config: Dict[str, Any]) -> str:
    """Determine primary issue for PASS rating."""
    try:
        gating_rules = config.get("overall_rating", {}).get("gating_rules", {})
        fair_rules = gating_rules.get("FAIR", {})

        roi_min = fair_rules.get("roi_min", 15.0)
        velocity_min = fair_rules.get("velocity_min", 30)
        stability_min = fair_rules.get("stability_min", 30)
        confidence_min = fair_rules.get("confidence_min", 40)

        # Calculate gaps
        gaps = {}
        if roi < roi_min:
            gaps["low_roi"] = roi_min - roi
        if scores.get("velocity", 0) < velocity_min:
            gaps["slow_velocity"] = velocity_min - scores.get("velocity", 0)
        if scores.get("stability", 0) < stability_min:
            gaps["volatile_pricing"] = stability_min - scores.get("stability", 0)
        if scores.get("confidence", 0) < confidence_min:
            gaps["low_confidence"] = confidence_min - scores.get("confidence", 0)

        # Return biggest gap
        if gaps:
            primary_issue = max(gaps.items(), key=lambda x: x[1])[0]
            return primary_issue.replace("_", " ")

        return "multiple factors"

    except Exception:
        return "insufficient metrics"


__all__ = [
    'compute_advanced_velocity_score',
    'compute_advanced_stability_score',
    'compute_advanced_confidence_score',
    'compute_overall_rating',
    'generate_readable_summary',
]
