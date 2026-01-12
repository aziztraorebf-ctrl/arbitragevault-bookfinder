"""
Seasonal Pattern Detector Service - Textbook Pricing Optimization

This service detects seasonal patterns in textbook pricing to help identify
optimal buy/sell windows. It analyzes historical price data to classify
patterns into known seasonal cycles.

Pattern Types:
- COLLEGE_FALL: peaks in August-September (back-to-school)
- COLLEGE_SPRING: peaks in December-January (spring semester)
- HIGH_SCHOOL: peaks in May-June (end of school year)
- EVERGREEN: consistent demand year-round
- STABLE: low volatility, no clear pattern
- IRREGULAR: high volatility, no matching pattern
- INSUFFICIENT_DATA: not enough data for analysis

Author: Claude Opus 4.5
Date: January 2026
"""

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Keepa epoch: 21 Oct 2000 00:00 UTC
KEEPA_EPOCH = datetime(2000, 10, 21, 0, 0, 0)

# Known seasonal patterns with their peak months
KNOWN_PATTERNS = {
    "COLLEGE_FALL": {
        "peak_months": [8, 9],
        "trough_months": [3, 4, 5, 6],
        "description": "College fall semester textbooks",
    },
    "COLLEGE_SPRING": {
        "peak_months": [12, 1],
        "trough_months": [9, 10, 11],
        "description": "College spring semester textbooks",
    },
    "HIGH_SCHOOL": {
        "peak_months": [5, 6],
        "trough_months": [1, 2, 3, 4],
        "description": "High school textbooks",
    },
}

# Optimal buy windows for each pattern
BUY_WINDOWS = {
    "COLLEGE_FALL": {
        "start_month": 3,
        "end_month": 6,
        "months_before_peak": 4,
        "recommendation": "Buy March-June for August-September peak",
    },
    "COLLEGE_SPRING": {
        "start_month": 9,
        "end_month": 11,
        "months_before_peak": 2,
        "recommendation": "Buy September-November for December-January peak",
    },
    "HIGH_SCHOOL": {
        "start_month": 1,
        "end_month": 4,
        "months_before_peak": 3,
        "recommendation": "Buy January-April for May-June peak",
    },
}

# Volatility threshold for STABLE pattern
STABLE_VOLATILITY_THRESHOLD = 0.15

# Minimum confidence for pattern matching
MIN_PATTERN_CONFIDENCE = 0.5


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SeasonalPattern:
    """
    Represents a detected seasonal pricing pattern.

    Attributes:
        pattern_type: Type of pattern (COLLEGE_FALL, COLLEGE_SPRING, etc.)
        peak_months: List of months (1-12) where prices peak
        trough_months: List of months (1-12) where prices are lowest
        confidence: Confidence score for pattern detection (0.0-1.0)
        avg_peak_price: Average price during peak months (optional)
        avg_trough_price: Average price during trough months (optional)
        price_swing_pct: Percentage price swing from trough to peak (optional)
    """
    pattern_type: str
    peak_months: List[int]
    trough_months: List[int]
    confidence: float
    avg_peak_price: Optional[float] = None
    avg_trough_price: Optional[float] = None
    price_swing_pct: Optional[float] = None


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def detect_seasonal_pattern(
    price_history: Optional[List[Tuple[Union[datetime, int, float], float]]],
    min_data_months: int = 6
) -> SeasonalPattern:
    """
    Detect seasonal pattern in price history.

    Analyzes price history to identify seasonal patterns by:
    1. Grouping prices by month
    2. Calculating monthly averages
    3. Identifying peaks (> avg + 0.5 std) and troughs (< avg - 0.5 std)
    4. Matching against known patterns

    Args:
        price_history: List of (datetime/timestamp, price) tuples.
                      Timestamps can be datetime objects or Keepa-style
                      integer minutes since epoch.
        min_data_months: Minimum months of data required for analysis.

    Returns:
        SeasonalPattern with detected pattern type and metrics.
    """
    # Handle None or empty input
    if not price_history:
        logger.debug("[SEASONAL] Empty or None price history provided")
        return SeasonalPattern(
            pattern_type="INSUFFICIENT_DATA",
            peak_months=[],
            trough_months=[],
            confidence=0.0
        )

    # Parse and group prices by month
    monthly_prices = _group_prices_by_month(price_history)

    # Check minimum data requirement
    months_with_data = len([m for m in monthly_prices.values() if m])
    if months_with_data < min_data_months:
        logger.info(
            f"[SEASONAL] Insufficient months: {months_with_data} < {min_data_months} required"
        )
        return SeasonalPattern(
            pattern_type="INSUFFICIENT_DATA",
            peak_months=[],
            trough_months=[],
            confidence=max(0.0, months_with_data / min_data_months * 0.5)
        )

    # Calculate monthly averages
    monthly_averages = _calculate_monthly_averages(monthly_prices)

    if not monthly_averages:
        return SeasonalPattern(
            pattern_type="INSUFFICIENT_DATA",
            peak_months=[],
            trough_months=[],
            confidence=0.0
        )

    # Calculate overall statistics
    all_prices = [p for prices in monthly_prices.values() for p in prices if p > 0]

    if len(all_prices) < 10:
        return SeasonalPattern(
            pattern_type="INSUFFICIENT_DATA",
            peak_months=[],
            trough_months=[],
            confidence=0.3
        )

    mean_price = statistics.mean(all_prices)
    try:
        std_price = statistics.stdev(all_prices)
    except statistics.StatisticsError:
        std_price = 0.0

    # Calculate volatility
    volatility = std_price / mean_price if mean_price > 0 else 0.0

    # Check for STABLE pattern (low volatility)
    if volatility < STABLE_VOLATILITY_THRESHOLD:
        # Confidence depends on how much data we have
        # Full year (12 months) = 0.9, fewer months = lower confidence
        stable_confidence = min(0.9, 0.3 + (months_with_data / 12) * 0.6)

        logger.info(
            f"[SEASONAL] Stable pattern detected: volatility={volatility:.2%}, "
            f"months={months_with_data}, confidence={stable_confidence:.2f}"
        )
        return SeasonalPattern(
            pattern_type="STABLE",
            peak_months=[],
            trough_months=[],
            confidence=stable_confidence,
            price_swing_pct=volatility * 100
        )

    # Identify peaks and troughs
    peak_threshold = mean_price + (0.5 * std_price)
    trough_threshold = mean_price - (0.5 * std_price)

    peak_months = []
    trough_months = []

    for month, avg in monthly_averages.items():
        if avg > peak_threshold:
            peak_months.append(month)
        elif avg < trough_threshold:
            trough_months.append(month)

    logger.debug(
        f"[SEASONAL] Detected peaks: {peak_months}, troughs: {trough_months}"
    )

    # Match against known patterns
    best_match = _match_known_pattern(peak_months, trough_months)

    if best_match:
        pattern_type, confidence = best_match

        # Calculate price metrics
        avg_peak_price = _calculate_average_for_months(monthly_averages, peak_months)
        avg_trough_price = _calculate_average_for_months(monthly_averages, trough_months)
        price_swing_pct = None

        if avg_peak_price and avg_trough_price and avg_trough_price > 0:
            price_swing_pct = ((avg_peak_price - avg_trough_price) / avg_trough_price) * 100

        logger.info(
            f"[SEASONAL] Pattern detected: {pattern_type}, confidence={confidence:.2f}"
        )

        return SeasonalPattern(
            pattern_type=pattern_type,
            peak_months=peak_months,
            trough_months=trough_months,
            confidence=confidence,
            avg_peak_price=avg_peak_price,
            avg_trough_price=avg_trough_price,
            price_swing_pct=price_swing_pct
        )

    # No pattern matched - return IRREGULAR
    logger.info("[SEASONAL] No pattern matched - returning IRREGULAR")

    avg_peak_price = _calculate_average_for_months(monthly_averages, peak_months) if peak_months else None
    avg_trough_price = _calculate_average_for_months(monthly_averages, trough_months) if trough_months else None

    return SeasonalPattern(
        pattern_type="IRREGULAR",
        peak_months=peak_months,
        trough_months=trough_months,
        confidence=0.4,
        avg_peak_price=avg_peak_price,
        avg_trough_price=avg_trough_price
    )


def get_days_until_peak(
    pattern: SeasonalPattern,
    reference_date: Optional[datetime] = None
) -> Optional[int]:
    """
    Calculate days from reference date to next peak month.

    Args:
        pattern: Detected seasonal pattern.
        reference_date: Date to calculate from (defaults to now).

    Returns:
        Number of days until middle of next peak month, or None if no peaks.
    """
    if not pattern.peak_months:
        return None

    if reference_date is None:
        reference_date = datetime.now()

    # Find the next peak month
    current_month = reference_date.month
    current_year = reference_date.year
    current_day = reference_date.day

    # Sort peak months
    sorted_peaks = sorted(pattern.peak_months)

    # Find the next peak month after current date
    next_peak_month = None
    next_peak_year = current_year

    for peak_month in sorted_peaks:
        if peak_month > current_month:
            next_peak_month = peak_month
            break
        elif peak_month == current_month and current_day < 15:
            # Still in peak month but before mid-month
            next_peak_month = peak_month
            break

    # If no peak found this year (including if we're past mid-month in a peak),
    # take the first peak next year
    if next_peak_month is None:
        next_peak_month = sorted_peaks[0]
        next_peak_year = current_year + 1

    # Calculate days to middle of peak month (15th)
    try:
        peak_date = datetime(next_peak_year, next_peak_month, 15)
        delta = peak_date - reference_date
        return delta.days
    except ValueError:
        # Handle edge cases (e.g., invalid date)
        return None


def get_optimal_buy_window(pattern: SeasonalPattern) -> Dict[str, Any]:
    """
    Get optimal buy window recommendation for a pattern.

    Args:
        pattern: Detected seasonal pattern.

    Returns:
        Dict with:
            - start_month: First month of buy window (or None)
            - end_month: Last month of buy window (or None)
            - months_before_peak: How many months before peak
            - recommendation: Human-readable recommendation
    """
    pattern_type = pattern.pattern_type

    # Check for known pattern with predefined buy window
    if pattern_type in BUY_WINDOWS:
        window = BUY_WINDOWS[pattern_type].copy()
        return window

    # Handle STABLE pattern
    if pattern_type == "STABLE":
        return {
            "start_month": None,
            "end_month": None,
            "months_before_peak": 0,
            "recommendation": "Stable prices - buy any time"
        }

    # Handle INSUFFICIENT_DATA
    if pattern_type == "INSUFFICIENT_DATA":
        return {
            "start_month": None,
            "end_month": None,
            "months_before_peak": 0,
            "recommendation": "Insufficient data - use caution"
        }

    # Handle IRREGULAR pattern
    if pattern_type == "IRREGULAR":
        return {
            "start_month": None,
            "end_month": None,
            "months_before_peak": 0,
            "recommendation": "Unpredictable pattern - use caution, monitor prices closely"
        }

    # Handle EVERGREEN or unknown patterns
    return {
        "start_month": None,
        "end_month": None,
        "months_before_peak": 0,
        "recommendation": "No clear seasonal pattern - buy any time"
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _group_prices_by_month(
    price_history: List[Tuple[Union[datetime, int, float], float]]
) -> Dict[int, List[float]]:
    """
    Group prices by month (1-12).

    Args:
        price_history: List of (datetime/timestamp, price) tuples.

    Returns:
        Dict mapping month number (1-12) to list of prices.
    """
    monthly_prices: Dict[int, List[float]] = {m: [] for m in range(1, 13)}

    for entry in price_history:
        try:
            timestamp, price = entry

            # Skip invalid prices
            if price is None or price <= 0:
                continue

            # Convert timestamp to datetime if needed
            if isinstance(timestamp, (int, float)):
                # Assume Keepa timestamp (minutes since epoch)
                dt = KEEPA_EPOCH + timedelta(minutes=timestamp)
            elif isinstance(timestamp, datetime):
                dt = timestamp
            else:
                continue

            month = dt.month
            monthly_prices[month].append(float(price))

        except (ValueError, TypeError, IndexError) as e:
            logger.debug(f"[SEASONAL] Skipping invalid entry: {entry}, error: {e}")
            continue

    return monthly_prices


def _calculate_monthly_averages(
    monthly_prices: Dict[int, List[float]]
) -> Dict[int, float]:
    """
    Calculate average price for each month.

    Args:
        monthly_prices: Dict mapping month to list of prices.

    Returns:
        Dict mapping month to average price (only months with data).
    """
    averages = {}

    for month, prices in monthly_prices.items():
        if prices:
            averages[month] = statistics.mean(prices)

    return averages


def _match_known_pattern(
    peak_months: List[int],
    trough_months: List[int]
) -> Optional[Tuple[str, float]]:
    """
    Match detected peaks/troughs against known patterns.

    Args:
        peak_months: List of detected peak months.
        trough_months: List of detected trough months.

    Returns:
        Tuple of (pattern_type, confidence) or None if no match.
    """
    if not peak_months:
        return None

    best_match = None
    best_confidence = 0.0

    for pattern_name, pattern_def in KNOWN_PATTERNS.items():
        expected_peaks = set(pattern_def["peak_months"])
        expected_troughs = set(pattern_def["trough_months"])

        # Calculate peak overlap
        peak_overlap = len(set(peak_months) & expected_peaks)
        peak_score = peak_overlap / len(expected_peaks) if expected_peaks else 0

        # Calculate trough overlap (if we have troughs)
        trough_score = 0
        if trough_months and expected_troughs:
            trough_overlap = len(set(trough_months) & expected_troughs)
            trough_score = trough_overlap / len(expected_troughs)

        # Combined confidence (weighted toward peaks)
        confidence = (peak_score * 0.7) + (trough_score * 0.3)

        if confidence > best_confidence and confidence >= MIN_PATTERN_CONFIDENCE:
            best_confidence = confidence
            best_match = (pattern_name, confidence)

    return best_match


def _calculate_average_for_months(
    monthly_averages: Dict[int, float],
    months: List[int]
) -> Optional[float]:
    """
    Calculate average price for a set of months.

    Args:
        monthly_averages: Dict mapping month to average price.
        months: List of months to average.

    Returns:
        Average price or None if no data.
    """
    if not months:
        return None

    prices = [monthly_averages[m] for m in months if m in monthly_averages]

    if not prices:
        return None

    return statistics.mean(prices)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "SeasonalPattern",
    "detect_seasonal_pattern",
    "get_days_until_peak",
    "get_optimal_buy_window",
]
