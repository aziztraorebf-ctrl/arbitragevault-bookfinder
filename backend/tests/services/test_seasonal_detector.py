"""
Unit tests for Seasonal Pattern Detector Service.

TDD: These tests are written FIRST before implementation.
Tests the seasonal pattern detection for textbook pricing optimization.

Pattern Types:
- COLLEGE_FALL: peaks in August-September (back-to-school)
- COLLEGE_SPRING: peaks in December-January (spring semester)
- HIGH_SCHOOL: peaks in May-June (end of school year)
- EVERGREEN: consistent demand year-round
- STABLE: low volatility, no clear pattern
- IRREGULAR: high volatility, no matching pattern
"""
import pytest
from datetime import datetime, timedelta
from typing import List, Tuple

# Import will fail until service is implemented - expected for TDD
from app.services.seasonal_detector_service import (
    SeasonalPattern,
    detect_seasonal_pattern,
    get_days_until_peak,
    get_optimal_buy_window,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def college_fall_price_history() -> List[Tuple[datetime, float]]:
    """
    Generate price history with peaks in August-September.
    Simulates college textbook demand for fall semester.
    """
    prices = []
    base_date = datetime(2025, 1, 1)

    for month in range(1, 13):
        for day in range(1, 29):  # Avoid Feb 29 issues
            date = base_date.replace(month=month, day=day)

            # Base price around $50
            base_price = 50.0

            # Peak in August (8) and September (9)
            if month in [8, 9]:
                price = base_price + 15.0 + (day % 5) * 0.5  # $62-$67
            # Trough in March-June
            elif month in [3, 4, 5, 6]:
                price = base_price - 10.0 + (day % 5) * 0.5  # $38-$43
            else:
                price = base_price + (day % 10 - 5) * 0.5  # $47-$52

            prices.append((date, price))

    return prices


@pytest.fixture
def college_spring_price_history() -> List[Tuple[datetime, float]]:
    """
    Generate price history with peaks in December-January.
    Simulates textbook demand for spring semester registration.
    """
    prices = []
    base_date = datetime(2025, 1, 1)

    for month in range(1, 13):
        for day in range(1, 29):
            date = base_date.replace(month=month, day=day)

            base_price = 45.0

            # Peak in December (12) and January (1)
            if month in [12, 1]:
                price = base_price + 18.0 + (day % 5) * 0.5  # $60-$65
            # Trough in September-November
            elif month in [9, 10, 11]:
                price = base_price - 12.0 + (day % 5) * 0.5  # $30-$35
            else:
                price = base_price + (day % 10 - 5) * 0.5  # $42-$47

            prices.append((date, price))

    return prices


@pytest.fixture
def high_school_price_history() -> List[Tuple[datetime, float]]:
    """
    Generate price history with peaks in May-June.
    Simulates high school textbook demand at end of year.
    """
    prices = []
    base_date = datetime(2025, 1, 1)

    for month in range(1, 13):
        for day in range(1, 29):
            date = base_date.replace(month=month, day=day)

            base_price = 40.0

            # Peak in May (5) and June (6)
            if month in [5, 6]:
                price = base_price + 12.0 + (day % 5) * 0.5  # $50-$55
            # Trough in January-April
            elif month in [1, 2, 3, 4]:
                price = base_price - 8.0 + (day % 5) * 0.5  # $30-$35
            else:
                price = base_price + (day % 10 - 5) * 0.5  # $37-$42

            prices.append((date, price))

    return prices


@pytest.fixture
def stable_price_history() -> List[Tuple[datetime, float]]:
    """
    Generate price history with very low volatility.
    Should be detected as STABLE pattern.
    """
    prices = []
    base_date = datetime(2025, 1, 1)

    for month in range(1, 13):
        for day in range(1, 29):
            date = base_date.replace(month=month, day=day)
            # Very consistent price around $25 with minimal variation
            price = 25.0 + (day % 3 - 1) * 0.2  # $24.8-$25.2
            prices.append((date, price))

    return prices


@pytest.fixture
def irregular_price_history() -> List[Tuple[datetime, float]]:
    """
    Generate price history with high volatility and no clear pattern.
    Should be detected as IRREGULAR pattern.
    """
    prices = []
    base_date = datetime(2025, 1, 1)

    import random
    random.seed(42)  # For reproducibility

    for month in range(1, 13):
        for day in range(1, 29):
            date = base_date.replace(month=month, day=day)
            # Random high volatility with no pattern
            price = 50.0 + random.uniform(-25, 25)  # $25-$75
            prices.append((date, price))

    return prices


@pytest.fixture
def insufficient_price_history() -> List[Tuple[datetime, float]]:
    """
    Generate price history with insufficient months of data.
    """
    prices = []
    base_date = datetime(2025, 1, 1)

    # Only 3 months of data
    for month in range(1, 4):
        for day in range(1, 29):
            date = base_date.replace(month=month, day=day)
            price = 30.0 + (day % 5) * 0.5
            prices.append((date, price))

    return prices


# =============================================================================
# TEST: SeasonalPattern dataclass
# =============================================================================

class TestSeasonalPatternDataclass:
    """Test SeasonalPattern dataclass structure."""

    def test_seasonal_pattern_has_required_fields(self):
        """
        SeasonalPattern should have all required fields.
        """
        pattern = SeasonalPattern(
            pattern_type="COLLEGE_FALL",
            peak_months=[8, 9],
            trough_months=[3, 4, 5, 6],
            confidence=0.85
        )

        assert pattern.pattern_type == "COLLEGE_FALL"
        assert pattern.peak_months == [8, 9]
        assert pattern.trough_months == [3, 4, 5, 6]
        assert pattern.confidence == 0.85

    def test_seasonal_pattern_has_optional_price_fields(self):
        """
        SeasonalPattern should have optional price analysis fields.
        """
        pattern = SeasonalPattern(
            pattern_type="COLLEGE_FALL",
            peak_months=[8, 9],
            trough_months=[3, 4, 5, 6],
            confidence=0.85,
            avg_peak_price=65.0,
            avg_trough_price=40.0,
            price_swing_pct=62.5  # (65-40)/40 * 100
        )

        assert pattern.avg_peak_price == 65.0
        assert pattern.avg_trough_price == 40.0
        assert pattern.price_swing_pct == 62.5

    def test_seasonal_pattern_optional_fields_default_none(self):
        """
        Optional fields should default to None.
        """
        pattern = SeasonalPattern(
            pattern_type="STABLE",
            peak_months=[],
            trough_months=[],
            confidence=0.90
        )

        assert pattern.avg_peak_price is None
        assert pattern.avg_trough_price is None
        assert pattern.price_swing_pct is None


# =============================================================================
# TEST: detect_seasonal_pattern
# =============================================================================

class TestDetectCollegeFallPattern:
    """Test detection of COLLEGE_FALL pattern (peaks in Aug-Sept)."""

    def test_detect_college_fall_pattern(self, college_fall_price_history):
        """
        Price history with peaks in August-September should be
        detected as COLLEGE_FALL pattern.
        """
        result = detect_seasonal_pattern(college_fall_price_history)

        assert result.pattern_type == "COLLEGE_FALL"
        assert 8 in result.peak_months
        assert 9 in result.peak_months
        assert result.confidence >= 0.7

    def test_college_fall_pattern_identifies_troughs(self, college_fall_price_history):
        """
        COLLEGE_FALL pattern should identify trough months.
        """
        result = detect_seasonal_pattern(college_fall_price_history)

        # Trough should be in spring/early summer (March-June)
        trough_intersect = set(result.trough_months) & {3, 4, 5, 6}
        assert len(trough_intersect) >= 1

    def test_college_fall_calculates_price_swing(self, college_fall_price_history):
        """
        Should calculate price swing percentage for COLLEGE_FALL.
        """
        result = detect_seasonal_pattern(college_fall_price_history)

        # Peak prices ~$62-$67, trough ~$38-$43
        # Price swing should be significant (> 30%)
        assert result.price_swing_pct is not None
        assert result.price_swing_pct > 30.0


class TestDetectCollegeSpringPattern:
    """Test detection of COLLEGE_SPRING pattern (peaks in Dec-Jan)."""

    def test_detect_college_spring_pattern(self, college_spring_price_history):
        """
        Price history with peaks in December-January should be
        detected as COLLEGE_SPRING pattern.
        """
        result = detect_seasonal_pattern(college_spring_price_history)

        assert result.pattern_type == "COLLEGE_SPRING"
        # Either December or January (or both) should be peak
        assert 12 in result.peak_months or 1 in result.peak_months
        assert result.confidence >= 0.7

    def test_college_spring_identifies_troughs(self, college_spring_price_history):
        """
        COLLEGE_SPRING pattern should identify fall trough months.
        """
        result = detect_seasonal_pattern(college_spring_price_history)

        # Trough should be in fall (September-November)
        trough_intersect = set(result.trough_months) & {9, 10, 11}
        assert len(trough_intersect) >= 1


class TestDetectHighSchoolPattern:
    """Test detection of HIGH_SCHOOL pattern (peaks in May-June)."""

    def test_detect_high_school_pattern(self, high_school_price_history):
        """
        Price history with peaks in May-June should be
        detected as HIGH_SCHOOL pattern.
        """
        result = detect_seasonal_pattern(high_school_price_history)

        assert result.pattern_type == "HIGH_SCHOOL"
        assert 5 in result.peak_months or 6 in result.peak_months
        assert result.confidence >= 0.7


class TestDetectStablePattern:
    """Test detection of STABLE pattern (low volatility)."""

    def test_no_pattern_detected_for_stable_prices(self, stable_price_history):
        """
        Stable prices with volatility < 0.15 should return STABLE pattern.
        """
        result = detect_seasonal_pattern(stable_price_history)

        assert result.pattern_type == "STABLE"
        # Stable pattern may have empty or minimal peak/trough months
        assert result.confidence >= 0.8

    def test_stable_pattern_has_low_price_swing(self, stable_price_history):
        """
        STABLE pattern should have very low or no price swing.
        """
        result = detect_seasonal_pattern(stable_price_history)

        # Price swing should be minimal (< 5%) or None
        if result.price_swing_pct is not None:
            assert result.price_swing_pct < 5.0


class TestDetectIrregularPattern:
    """Test detection of IRREGULAR pattern (high volatility, no match)."""

    def test_irregular_pattern_detected_for_random_prices(self, irregular_price_history):
        """
        Random high-volatility prices should return IRREGULAR pattern.
        """
        result = detect_seasonal_pattern(irregular_price_history)

        # Should be IRREGULAR (no clear pattern despite volatility)
        assert result.pattern_type in ("IRREGULAR", "STABLE")

    def test_irregular_pattern_has_lower_confidence(self, irregular_price_history):
        """
        IRREGULAR pattern should have lower confidence.
        """
        result = detect_seasonal_pattern(irregular_price_history)

        # Irregular patterns have uncertainty
        assert result.confidence <= 0.8


class TestDetectPatternEdgeCases:
    """Test edge cases for pattern detection."""

    def test_insufficient_data_returns_stable(self, insufficient_price_history):
        """
        Insufficient months of data should return STABLE or INSUFFICIENT.
        """
        result = detect_seasonal_pattern(
            insufficient_price_history,
            min_data_months=6
        )

        # With only 3 months, can't reliably detect seasonal pattern
        assert result.pattern_type in ("STABLE", "INSUFFICIENT_DATA")
        assert result.confidence < 0.7

    def test_empty_price_history(self):
        """
        Empty price history should be handled gracefully.
        """
        result = detect_seasonal_pattern([])

        assert result.pattern_type in ("STABLE", "INSUFFICIENT_DATA")
        assert result.confidence == 0.0 or result.peak_months == []

    def test_none_price_history(self):
        """
        None as price history should be handled gracefully.
        """
        result = detect_seasonal_pattern(None)

        assert result.pattern_type in ("STABLE", "INSUFFICIENT_DATA")


# =============================================================================
# TEST: get_days_until_peak
# =============================================================================

class TestGetDaysUntilPeak:
    """Test calculation of days until next peak month."""

    def test_get_days_until_peak_college_fall(self):
        """
        Calculate days until August peak from various reference dates.
        """
        pattern = SeasonalPattern(
            pattern_type="COLLEGE_FALL",
            peak_months=[8, 9],
            trough_months=[3, 4, 5, 6],
            confidence=0.85
        )

        # From March 15, 2025 - should be ~138 days to mid-August
        reference_date = datetime(2025, 3, 15)
        days = get_days_until_peak(pattern, reference_date)

        assert days is not None
        # Mid-August (Aug 15) is about 153 days from March 15
        # Allow some tolerance for mid-month calculation
        assert 130 <= days <= 160

    def test_get_days_until_peak_when_in_peak_month(self):
        """
        When reference date is in a peak month but past mid-month,
        return days to the next peak month (could be same year or next year).
        """
        pattern = SeasonalPattern(
            pattern_type="COLLEGE_FALL",
            peak_months=[8, 9],
            trough_months=[3, 4, 5, 6],
            confidence=0.85
        )

        # From August 20, 2025 - September is still a peak month this year
        # So should return days to mid-September (about 26 days)
        reference_date = datetime(2025, 8, 20)
        days = get_days_until_peak(pattern, reference_date)

        assert days is not None
        # Next peak (Sept 15) is about 26 days away
        assert 20 <= days <= 35

    def test_get_days_until_peak_wraps_to_next_year(self):
        """
        When past all peak months in current year, wrap to next year.
        """
        pattern = SeasonalPattern(
            pattern_type="COLLEGE_FALL",
            peak_months=[8, 9],
            trough_months=[3, 4, 5, 6],
            confidence=0.85
        )

        # From October 15, 2025 - should return days to Aug 2026
        reference_date = datetime(2025, 10, 15)
        days = get_days_until_peak(pattern, reference_date)

        assert days is not None
        # Next peak is ~305 days away (to Aug 15, 2026)
        assert 290 <= days <= 320

    def test_get_days_until_peak_uses_current_date_if_none(self):
        """
        If reference_date is None, use current date.
        """
        pattern = SeasonalPattern(
            pattern_type="COLLEGE_FALL",
            peak_months=[8, 9],
            trough_months=[3, 4, 5, 6],
            confidence=0.85
        )

        days = get_days_until_peak(pattern, reference_date=None)

        assert days is not None
        # Should return some value (exact depends on current date)
        assert 0 <= days <= 365

    def test_get_days_until_peak_returns_none_for_no_peaks(self):
        """
        Return None if pattern has no peak months.
        """
        pattern = SeasonalPattern(
            pattern_type="STABLE",
            peak_months=[],
            trough_months=[],
            confidence=0.90
        )

        days = get_days_until_peak(pattern, datetime(2025, 6, 1))

        assert days is None

    def test_get_days_until_peak_college_spring(self):
        """
        Calculate days until December/January peak.
        """
        pattern = SeasonalPattern(
            pattern_type="COLLEGE_SPRING",
            peak_months=[12, 1],
            trough_months=[9, 10, 11],
            confidence=0.85
        )

        # From October 1 - should be ~75 days to mid-December
        reference_date = datetime(2025, 10, 1)
        days = get_days_until_peak(pattern, reference_date)

        assert days is not None
        # Mid-December (Dec 15) is about 75 days from Oct 1
        assert 60 <= days <= 90


# =============================================================================
# TEST: get_optimal_buy_window
# =============================================================================

class TestGetOptimalBuyWindow:
    """Test optimal buy window recommendations."""

    def test_optimal_buy_window_college_fall(self):
        """
        COLLEGE_FALL: Buy in March-June for August-September peak.
        """
        pattern = SeasonalPattern(
            pattern_type="COLLEGE_FALL",
            peak_months=[8, 9],
            trough_months=[3, 4, 5, 6],
            confidence=0.85
        )

        window = get_optimal_buy_window(pattern)

        assert window is not None
        assert window['start_month'] == 3  # March
        assert window['end_month'] == 6     # June
        assert window['months_before_peak'] >= 2
        assert 'March' in window['recommendation'] or 'June' in window['recommendation']
        assert 'August' in window['recommendation'] or 'September' in window['recommendation']

    def test_optimal_buy_window_college_spring(self):
        """
        COLLEGE_SPRING: Buy in September-November for December-January peak.
        """
        pattern = SeasonalPattern(
            pattern_type="COLLEGE_SPRING",
            peak_months=[12, 1],
            trough_months=[9, 10, 11],
            confidence=0.85
        )

        window = get_optimal_buy_window(pattern)

        assert window is not None
        assert window['start_month'] == 9   # September
        assert window['end_month'] == 11    # November
        assert window['months_before_peak'] >= 1
        assert 'September' in window['recommendation'] or 'November' in window['recommendation']
        assert 'December' in window['recommendation'] or 'January' in window['recommendation']

    def test_optimal_buy_window_high_school(self):
        """
        HIGH_SCHOOL: Buy in January-April for May-June peak.
        """
        pattern = SeasonalPattern(
            pattern_type="HIGH_SCHOOL",
            peak_months=[5, 6],
            trough_months=[1, 2, 3, 4],
            confidence=0.80
        )

        window = get_optimal_buy_window(pattern)

        assert window is not None
        assert window['start_month'] == 1   # January
        assert window['end_month'] == 4     # April
        assert 'January' in window['recommendation'] or 'April' in window['recommendation']
        assert 'May' in window['recommendation'] or 'June' in window['recommendation']

    def test_optimal_buy_window_stable_no_recommendation(self):
        """
        STABLE pattern should return no specific buy window.
        """
        pattern = SeasonalPattern(
            pattern_type="STABLE",
            peak_months=[],
            trough_months=[],
            confidence=0.90
        )

        window = get_optimal_buy_window(pattern)

        # For stable, no specific window - buy anytime
        assert window is not None
        assert window['start_month'] is None or window['start_month'] == 1
        assert 'any time' in window['recommendation'].lower() or 'anytime' in window['recommendation'].lower()

    def test_optimal_buy_window_irregular_cautious(self):
        """
        IRREGULAR pattern should return cautious recommendation.
        """
        pattern = SeasonalPattern(
            pattern_type="IRREGULAR",
            peak_months=[2, 7, 11],  # Random peaks
            trough_months=[4, 9],
            confidence=0.40
        )

        window = get_optimal_buy_window(pattern)

        assert window is not None
        assert 'caution' in window['recommendation'].lower() or 'unpredictable' in window['recommendation'].lower()


# =============================================================================
# TEST: Integration scenarios
# =============================================================================

class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_full_workflow_college_textbook(self, college_fall_price_history):
        """
        Complete workflow for college textbook analysis.
        """
        # 1. Detect pattern
        pattern = detect_seasonal_pattern(college_fall_price_history)
        assert pattern.pattern_type == "COLLEGE_FALL"

        # 2. Get days until peak
        reference = datetime(2025, 4, 1)  # April
        days = get_days_until_peak(pattern, reference)
        assert days is not None
        assert days > 100  # ~4.5 months to August

        # 3. Get buy window
        window = get_optimal_buy_window(pattern)
        assert window['start_month'] == 3

    def test_pattern_detection_with_timestamp_integers(self):
        """
        Handle Keepa-style timestamp integers (minutes since epoch).
        """
        from app.services.intrinsic_value_service import KEEPA_EPOCH

        prices = []
        for month in range(1, 13):
            for day in range(1, 29):
                date = datetime(2025, month, day)
                keepa_ts = int((date - KEEPA_EPOCH).total_seconds() / 60)

                # Peak in August
                if month in [8, 9]:
                    price = 60.0
                else:
                    price = 40.0

                prices.append((keepa_ts, price))

        result = detect_seasonal_pattern(prices)

        # Should still detect pattern from integer timestamps
        assert result.pattern_type in ("COLLEGE_FALL", "STABLE")


# =============================================================================
# TEST: Edge cases and robustness
# =============================================================================

class TestRobustness:
    """Test robustness and edge case handling."""

    def test_handles_negative_prices_gracefully(self):
        """
        Negative prices should be filtered out.
        """
        prices = [
            (datetime(2025, 1, i), 30.0 if i % 3 != 0 else -10.0)
            for i in range(1, 29)
        ]
        # Add more months
        for month in range(2, 8):
            for day in range(1, 29):
                prices.append((datetime(2025, month, day), 30.0))

        result = detect_seasonal_pattern(prices)

        # Should complete without error
        assert result is not None
        assert result.pattern_type in ("STABLE", "IRREGULAR", "INSUFFICIENT_DATA")

    def test_handles_malformed_entries(self):
        """
        Malformed entries should be skipped.
        """
        prices = [
            (datetime(2025, 1, 1), 30.0),
            "not a tuple",
            (datetime(2025, 1, 2), 30.0),
            (None, 30.0),
            (datetime(2025, 1, 3), 30.0),
        ]

        # Add valid data for remaining months
        for month in range(2, 8):
            for day in range(1, 29):
                prices.append((datetime(2025, month, day), 30.0))

        result = detect_seasonal_pattern(prices)

        # Should complete without error
        assert result is not None

    def test_single_month_data(self):
        """
        Single month of data should return low confidence.
        """
        prices = [
            (datetime(2025, 5, day), 40.0)
            for day in range(1, 29)
        ]

        result = detect_seasonal_pattern(prices, min_data_months=1)

        # With only 1 month, can't detect seasonal pattern
        assert result.pattern_type in ("STABLE", "INSUFFICIENT_DATA")
        assert result.confidence <= 0.5
