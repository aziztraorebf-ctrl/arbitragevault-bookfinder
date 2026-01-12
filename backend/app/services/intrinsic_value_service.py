"""
Intrinsic Value Service - Core Calculation for Textbook Pivot

This service calculates the intrinsic value corridor for book pricing
based on historical price data. It replaces snapshot pricing with
historical median-based pricing for more accurate ROI calculations.

Author: Claude Opus 4.5
Date: January 2026
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Confidence level thresholds
CONFIDENCE_HIGH_MIN_POINTS = 30
CONFIDENCE_MEDIUM_MIN_POINTS = 15
CONFIDENCE_HIGH_MAX_VOLATILITY = 0.20
CONFIDENCE_MEDIUM_MAX_VOLATILITY = 0.35

# Strategy window configurations (days)
STRATEGY_WINDOWS = {
    "textbook": 365,  # Long-term for stable textbook pricing
    "velocity": 90,   # Short-term for fast-moving items
    "balanced": 90,   # Default 90-day window
}

# Keepa epoch: 21 Oct 2000 00:00 UTC
KEEPA_EPOCH = datetime(2000, 10, 21, 0, 0, 0)


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def calculate_intrinsic_value_corridor(
    price_history: Optional[List[Tuple[datetime, float]]],
    window_days: int = 90,
    min_data_points: int = 10
) -> Dict[str, Any]:
    """
    Calculate intrinsic value corridor from historical prices.

    Computes [P25, Median, P75] from historical price data with outlier
    filtering using P5-P95 range.

    Args:
        price_history: List of (datetime, float) tuples representing price history.
                      Can also accept (timestamp_minutes, float) from Keepa format.
        window_days: Number of days to consider for calculation (default 90).
        min_data_points: Minimum data points required for valid calculation (default 10).

    Returns:
        Dict with:
            - low: P25 percentile (or None if insufficient data)
            - median: P50 percentile (or None if insufficient data)
            - high: P75 percentile (or None if insufficient data)
            - confidence: 'HIGH', 'MEDIUM', 'LOW', or 'INSUFFICIENT_DATA'
            - volatility: Coefficient of variation (stdev/mean)
            - data_points: Number of valid data points used
            - window_days: Window used for calculation
            - reason: Human-readable explanation
    """
    # Handle None or empty input
    if not price_history:
        logger.debug("[INTRINSIC] Empty or None price history provided")
        return _build_result(
            low=None,
            median=None,
            high=None,
            confidence="INSUFFICIENT_DATA",
            volatility=0.0,
            data_points=0,
            window_days=window_days,
            reason="No price history data available"
        )

    # Convert and filter prices within window
    now = datetime.now()
    window_start = now - timedelta(days=window_days)

    valid_prices = []
    for entry in price_history:
        try:
            timestamp, price = entry

            # Convert timestamp to datetime if needed
            if isinstance(timestamp, (int, float)):
                # Assume Keepa timestamp (minutes since epoch)
                dt = KEEPA_EPOCH + timedelta(minutes=timestamp)
            elif isinstance(timestamp, datetime):
                dt = timestamp
            else:
                continue

            # Filter by window and validate price
            if dt >= window_start and price is not None and price > 0:
                valid_prices.append(price)

        except (ValueError, TypeError) as e:
            logger.debug(f"[INTRINSIC] Skipping invalid entry: {entry}, error: {e}")
            continue

    logger.debug(
        f"[INTRINSIC] Extracted {len(valid_prices)} valid prices "
        f"from {len(price_history)} entries (window={window_days} days)"
    )

    # Check minimum data points
    if len(valid_prices) < min_data_points:
        logger.info(
            f"[INTRINSIC] Insufficient data: {len(valid_prices)} < {min_data_points} required"
        )
        return _build_result(
            low=None,
            median=None,
            high=None,
            confidence="INSUFFICIENT_DATA",
            volatility=0.0,
            data_points=len(valid_prices),
            window_days=window_days,
            reason=f"Insufficient data points: {len(valid_prices)} < {min_data_points} required"
        )

    # Filter outliers using P5-P95 range
    filtered_prices = _filter_outliers(valid_prices)
    logger.debug(
        f"[INTRINSIC] After outlier filtering: {len(filtered_prices)} prices "
        f"(removed {len(valid_prices) - len(filtered_prices)} outliers)"
    )

    # Check again after filtering
    if len(filtered_prices) < min_data_points:
        logger.info(
            f"[INTRINSIC] Insufficient data after filtering: {len(filtered_prices)} < {min_data_points}"
        )
        return _build_result(
            low=None,
            median=None,
            high=None,
            confidence="INSUFFICIENT_DATA",
            volatility=0.0,
            data_points=len(filtered_prices),
            window_days=window_days,
            reason=f"Insufficient data after outlier filtering: {len(filtered_prices)} < {min_data_points}"
        )

    # Calculate percentiles
    sorted_prices = sorted(filtered_prices)
    p25 = _percentile(sorted_prices, 25)
    median = _percentile(sorted_prices, 50)
    p75 = _percentile(sorted_prices, 75)

    # Calculate volatility (coefficient of variation)
    volatility = _calculate_volatility(filtered_prices)

    # Determine confidence level
    confidence = _determine_confidence(len(filtered_prices), volatility)

    reason = _build_confidence_reason(len(filtered_prices), volatility, confidence)

    logger.info(
        f"[INTRINSIC] Corridor calculated: "
        f"low=${p25:.2f}, median=${median:.2f}, high=${p75:.2f}, "
        f"confidence={confidence}, volatility={volatility:.2%}, "
        f"data_points={len(filtered_prices)}"
    )

    return _build_result(
        low=p25,
        median=median,
        high=p75,
        confidence=confidence,
        volatility=volatility,
        data_points=len(filtered_prices),
        window_days=window_days,
        reason=reason
    )


def get_sell_price_for_strategy(
    parsed_data: Dict[str, Any],
    strategy: str = "balanced",
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get sell price based on strategy using intrinsic value calculation.

    Uses historical median as the sell price for more accurate ROI calculation.
    Falls back to current price when insufficient historical data.

    Args:
        parsed_data: Output from parse_keepa_product_unified().
                    Must contain 'price_history' key with [(timestamp, price), ...].
        strategy: Pricing strategy - 'textbook', 'velocity', or 'balanced'.
        config: Optional configuration overrides:
                - min_data_points: Override minimum data points threshold.

    Returns:
        Dict with:
            - sell_price: Recommended sell price (intrinsic median or fallback)
            - source: 'intrinsic_median', 'current_price_fallback', or 'no_price_available'
            - corridor: Full corridor calculation result
            - warning: Warning message if fallback was used (or None)
    """
    config = config or {}

    # Determine window based on strategy
    window_days = STRATEGY_WINDOWS.get(strategy, 90)

    # Get configuration
    min_data_points = config.get('min_data_points', 10)

    # Extract price history from parsed data
    price_history = parsed_data.get('price_history', [])

    # Calculate intrinsic corridor
    corridor = calculate_intrinsic_value_corridor(
        price_history=price_history,
        window_days=window_days,
        min_data_points=min_data_points
    )

    # Determine sell price based on corridor confidence
    if corridor['confidence'] != 'INSUFFICIENT_DATA' and corridor['median'] is not None:
        # Use intrinsic median as sell price
        return {
            'sell_price': corridor['median'],
            'source': 'intrinsic_median',
            'corridor': corridor,
            'warning': None
        }

    # Fallback to current price
    fallback_price = _get_fallback_price(parsed_data)

    if fallback_price is not None:
        logger.warning(
            f"[INTRINSIC] Falling back to current price: ${fallback_price:.2f} "
            f"(reason: {corridor['reason']})"
        )
        return {
            'sell_price': fallback_price,
            'source': 'current_price_fallback',
            'corridor': corridor,
            'warning': f"Insufficient historical data for intrinsic value calculation. "
                      f"Using current price as fallback. Reason: {corridor['reason']}"
        }

    # No price available at all
    logger.warning("[INTRINSIC] No price available - neither intrinsic nor fallback")
    return {
        'sell_price': None,
        'source': 'no_price_available',
        'corridor': corridor,
        'warning': "No price data available. Cannot calculate sell price."
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _filter_outliers(prices: List[float]) -> List[float]:
    """
    Filter outliers using P5-P95 range.

    Only applies filtering when there are enough data points to
    reliably detect outliers without accidentally removing valid data.

    Args:
        prices: List of price values.

    Returns:
        List of prices with outliers removed.
    """
    # Need at least 20 data points to reliably filter outliers
    # With fewer points, P5/P95 interpolation can remove valid data
    if len(prices) < 20:
        return prices

    sorted_prices = sorted(prices)
    p5 = _percentile(sorted_prices, 5)
    p95 = _percentile(sorted_prices, 95)

    filtered = [p for p in prices if p5 <= p <= p95]

    return filtered if filtered else prices  # Return original if all filtered


def _percentile(sorted_data: List[float], p: int) -> float:
    """
    Calculate percentile from sorted data.

    Args:
        sorted_data: Pre-sorted list of values.
        p: Percentile to calculate (0-100).

    Returns:
        Percentile value.
    """
    if not sorted_data:
        return 0.0

    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]

    # Linear interpolation method
    k = (n - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < n else f

    if f == c:
        return sorted_data[f]

    # Interpolate between f and c
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def _calculate_volatility(prices: List[float]) -> float:
    """
    Calculate volatility as coefficient of variation (stdev / mean).

    Args:
        prices: List of price values.

    Returns:
        Coefficient of variation (0.0 if all values identical or mean is 0).
    """
    if len(prices) < 2:
        return 0.0

    try:
        mean = statistics.mean(prices)
        if mean == 0:
            return 0.0

        stdev = statistics.stdev(prices)
        return stdev / mean

    except statistics.StatisticsError:
        return 0.0


def _determine_confidence(data_points: int, volatility: float) -> str:
    """
    Determine confidence level based on data points and volatility.

    Confidence levels:
        - HIGH: 30+ data points AND volatility < 0.20
        - MEDIUM: 15+ data points AND volatility < 0.35
        - LOW: 10+ data points (min threshold met)
        - INSUFFICIENT_DATA: Below min threshold (handled by caller)

    Args:
        data_points: Number of valid data points.
        volatility: Coefficient of variation.

    Returns:
        Confidence level string.
    """
    if data_points >= CONFIDENCE_HIGH_MIN_POINTS and volatility < CONFIDENCE_HIGH_MAX_VOLATILITY:
        return "HIGH"
    elif data_points >= CONFIDENCE_MEDIUM_MIN_POINTS and volatility < CONFIDENCE_MEDIUM_MAX_VOLATILITY:
        return "MEDIUM"
    else:
        return "LOW"


def _build_confidence_reason(data_points: int, volatility: float, confidence: str) -> str:
    """
    Build human-readable reason for confidence level.

    Args:
        data_points: Number of valid data points.
        volatility: Coefficient of variation.
        confidence: Determined confidence level.

    Returns:
        Human-readable explanation.
    """
    if confidence == "HIGH":
        return f"High confidence: {data_points} data points with {volatility:.1%} volatility"
    elif confidence == "MEDIUM":
        reasons = []
        if data_points < CONFIDENCE_HIGH_MIN_POINTS:
            reasons.append(f"data points ({data_points}) < {CONFIDENCE_HIGH_MIN_POINTS}")
        if volatility >= CONFIDENCE_HIGH_MAX_VOLATILITY:
            reasons.append(f"volatility ({volatility:.1%}) >= {CONFIDENCE_HIGH_MAX_VOLATILITY:.0%}")
        return f"Medium confidence: {', '.join(reasons)}"
    else:
        reasons = []
        if data_points < CONFIDENCE_MEDIUM_MIN_POINTS:
            reasons.append(f"data points ({data_points}) < {CONFIDENCE_MEDIUM_MIN_POINTS}")
        if volatility >= CONFIDENCE_MEDIUM_MAX_VOLATILITY:
            reasons.append(f"volatility ({volatility:.1%}) >= {CONFIDENCE_MEDIUM_MAX_VOLATILITY:.0%}")
        return f"Low confidence: {', '.join(reasons) or 'marginal thresholds'}"


def _get_fallback_price(parsed_data: Dict[str, Any]) -> Optional[float]:
    """
    Get fallback price from current prices in parsed data.

    Priority: buybox > new > used

    Args:
        parsed_data: Parsed Keepa product data.

    Returns:
        Fallback price or None if no price available.
    """
    price_fields = [
        'current_buybox_price',
        'current_new_price',
        'current_used_price'
    ]

    for field in price_fields:
        price = parsed_data.get(field)
        if price is not None and price > 0:
            return float(price)

    return None


def _build_result(
    low: Optional[float],
    median: Optional[float],
    high: Optional[float],
    confidence: str,
    volatility: float,
    data_points: int,
    window_days: int,
    reason: str
) -> Dict[str, Any]:
    """
    Build standardized result dictionary.

    Args:
        All corridor calculation values.

    Returns:
        Standardized result dict.
    """
    return {
        'low': low,
        'median': median,
        'high': high,
        'confidence': confidence,
        'volatility': round(volatility, 4),
        'data_points': data_points,
        'window_days': window_days,
        'reason': reason
    }


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    'calculate_intrinsic_value_corridor',
    'get_sell_price_for_strategy',
]
