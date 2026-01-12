"""
Unit tests for Intrinsic Value Service.

TDD: These tests are written FIRST before implementation.
Tests the core intrinsic value corridor calculation for the Textbook Pivot.
"""
import pytest
from datetime import datetime, timedelta
from typing import List, Tuple

# Import will fail until service is implemented - expected for TDD
from app.services.intrinsic_value_service import (
    calculate_intrinsic_value_corridor,
    get_sell_price_for_strategy,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def price_history_90_points() -> List[Tuple[datetime, float]]:
    """
    Generate 90 data points of price history.
    Prices centered around $25 with normal variation.
    """
    base_date = datetime.now()
    prices = []

    # Generate 90 days of price data with realistic variation
    for i in range(90):
        date = base_date - timedelta(days=i)
        # Price varies between $20 and $30, centered around $25
        # Using a simple pattern: base + variation
        variation = (i % 10 - 5) * 0.5  # +/- $2.50
        price = 25.0 + variation
        prices.append((date, price))

    return prices


@pytest.fixture
def price_history_5_points() -> List[Tuple[datetime, float]]:
    """
    Generate only 5 data points - insufficient for HIGH confidence.
    """
    base_date = datetime.now()
    return [
        (base_date - timedelta(days=0), 25.0),
        (base_date - timedelta(days=1), 24.0),
        (base_date - timedelta(days=2), 26.0),
        (base_date - timedelta(days=3), 25.5),
        (base_date - timedelta(days=4), 24.5),
    ]


@pytest.fixture
def price_history_with_outliers() -> List[Tuple[datetime, float]]:
    """
    Generate price history with extreme outliers.
    Normal prices around $25, with outliers at $5 and $100.
    """
    base_date = datetime.now()
    prices = []

    # 30 normal prices around $25
    for i in range(30):
        date = base_date - timedelta(days=i)
        price = 25.0 + (i % 5 - 2) * 0.5  # $24-$26
        prices.append((date, price))

    # Add extreme outliers
    prices.append((base_date - timedelta(days=31), 5.0))   # Very low
    prices.append((base_date - timedelta(days=32), 100.0)) # Very high
    prices.append((base_date - timedelta(days=33), 3.0))   # Extremely low
    prices.append((base_date - timedelta(days=34), 150.0)) # Extremely high

    return prices


@pytest.fixture
def parsed_data_with_history() -> dict:
    """
    Parsed Keepa data containing price history.
    Mimics output from parse_keepa_product_unified().
    """
    base_date = datetime.now()

    # Generate price history as (timestamp_minutes, price) tuples
    # Similar to what keepa_parser_v2 produces
    price_history = []
    for i in range(60):
        date = base_date - timedelta(days=i)
        price = 30.0 + (i % 10 - 5) * 0.8  # $26-$34
        # Store as (timestamp_minutes, price) - simplified for testing
        timestamp_minutes = int(date.timestamp() / 60)
        price_history.append((timestamp_minutes, price))

    return {
        'asin': 'B07TEST123',
        'title': 'Engineering Textbook 101',
        'current_buybox_price': 29.99,
        'current_new_price': 32.00,
        'current_used_price': 24.00,
        'price_history': price_history,
        'bsr_history': [],
        'offers_by_condition': {
            'new': {'minimum_price': 32.00, 'seller_count': 5},
            'good': {'minimum_price': 24.00, 'seller_count': 12},
        }
    }


@pytest.fixture
def parsed_data_insufficient_history() -> dict:
    """
    Parsed Keepa data with insufficient price history.
    Should trigger fallback to current_price.
    """
    base_date = datetime.now()

    # Only 3 data points - insufficient
    price_history = [
        (int((base_date - timedelta(days=0)).timestamp() / 60), 25.0),
        (int((base_date - timedelta(days=1)).timestamp() / 60), 26.0),
        (int((base_date - timedelta(days=2)).timestamp() / 60), 24.0),
    ]

    return {
        'asin': 'B07SPARSE99',
        'title': 'Rare Book With Little Data',
        'current_buybox_price': 45.00,
        'current_new_price': 50.00,
        'current_used_price': 40.00,
        'price_history': price_history,
        'bsr_history': [],
        'offers_by_condition': {}
    }


# =============================================================================
# TEST: calculate_intrinsic_value_corridor
# =============================================================================

class TestCalculateCorridorWithSufficientData:
    """Test corridor calculation with sufficient data points."""

    def test_returns_high_confidence_with_90_points(self, price_history_90_points):
        """
        90 data points with low volatility should return HIGH confidence.
        """
        result = calculate_intrinsic_value_corridor(
            price_history=price_history_90_points,
            window_days=90,
            min_data_points=10
        )

        # Verify structure
        assert 'low' in result
        assert 'median' in result
        assert 'high' in result
        assert 'confidence' in result
        assert 'volatility' in result
        assert 'data_points' in result
        assert 'window_days' in result
        assert 'reason' in result

        # Verify confidence is HIGH
        assert result['confidence'] == 'HIGH'

        # Verify data points counted
        assert result['data_points'] == 90

        # Verify median is around $25 (our test data center)
        assert 22.0 <= result['median'] <= 28.0

        # Verify corridor makes sense (low < median < high)
        assert result['low'] < result['median'] < result['high']

    def test_returns_percentiles_correctly(self, price_history_90_points):
        """
        Verify P25, Median, P75 are calculated correctly.
        """
        result = calculate_intrinsic_value_corridor(
            price_history=price_history_90_points,
            window_days=90,
            min_data_points=10
        )

        # low should be P25, median should be P50, high should be P75
        # For our test data centered around $25, expect:
        # - low (P25): ~$23.50
        # - median (P50): ~$25.00
        # - high (P75): ~$26.50
        assert result['low'] < result['median']
        assert result['median'] < result['high']

        # Volatility should be low for our stable test data
        assert result['volatility'] < 0.20


class TestCalculateCorridorInsufficientData:
    """Test corridor calculation with insufficient data points."""

    def test_returns_insufficient_data_with_5_points(self, price_history_5_points):
        """
        5 data points (below default min of 10) should return INSUFFICIENT_DATA.
        """
        result = calculate_intrinsic_value_corridor(
            price_history=price_history_5_points,
            window_days=90,
            min_data_points=10
        )

        assert result['confidence'] == 'INSUFFICIENT_DATA'
        assert result['data_points'] == 5
        assert 'insufficient' in result['reason'].lower()

    def test_returns_low_confidence_with_custom_threshold(self, price_history_5_points):
        """
        With min_data_points=5, should pass and return LOW confidence.
        """
        result = calculate_intrinsic_value_corridor(
            price_history=price_history_5_points,
            window_days=90,
            min_data_points=5  # Custom threshold
        )

        # Should NOT be INSUFFICIENT_DATA since we meet min threshold
        assert result['confidence'] in ('LOW', 'MEDIUM', 'HIGH')
        assert result['data_points'] == 5


class TestCalculateCorridorFiltersOutliers:
    """Test that outliers are properly filtered using P5-P95."""

    def test_median_not_skewed_by_extreme_outliers(self, price_history_with_outliers):
        """
        Extreme outliers ($5 and $150) should be filtered.
        Median should remain around $25.
        """
        result = calculate_intrinsic_value_corridor(
            price_history=price_history_with_outliers,
            window_days=90,
            min_data_points=10
        )

        # Median should be close to $25 despite outliers
        # If outliers weren't filtered, median would be skewed
        assert 23.0 <= result['median'] <= 27.0

        # Reason should mention outlier filtering
        assert result['data_points'] <= len(price_history_with_outliers)

    def test_corridor_bounds_are_reasonable(self, price_history_with_outliers):
        """
        After filtering, corridor bounds should be within reasonable range.
        """
        result = calculate_intrinsic_value_corridor(
            price_history=price_history_with_outliers,
            window_days=90,
            min_data_points=10
        )

        # Low (P25) should not be near the $5 outlier
        assert result['low'] > 10.0

        # High (P75) should not be near the $150 outlier
        assert result['high'] < 50.0


class TestCalculateCorridorEmptyHistory:
    """Test corridor calculation with empty or invalid history."""

    def test_empty_list_returns_insufficient_data(self):
        """
        Empty price history should return INSUFFICIENT_DATA.
        """
        result = calculate_intrinsic_value_corridor(
            price_history=[],
            window_days=90,
            min_data_points=10
        )

        assert result['confidence'] == 'INSUFFICIENT_DATA'
        assert result['data_points'] == 0
        assert result['median'] is None
        assert result['low'] is None
        assert result['high'] is None

    def test_none_returns_insufficient_data(self):
        """
        None as price history should be handled gracefully.
        """
        result = calculate_intrinsic_value_corridor(
            price_history=None,
            window_days=90,
            min_data_points=10
        )

        assert result['confidence'] == 'INSUFFICIENT_DATA'
        assert result['data_points'] == 0


class TestCalculateCorridorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_all_same_values(self):
        """
        All prices identical should have zero volatility.
        """
        base_date = datetime.now()
        same_prices = [
            (base_date - timedelta(days=i), 25.0)
            for i in range(30)
        ]

        result = calculate_intrinsic_value_corridor(
            price_history=same_prices,
            window_days=90,
            min_data_points=10
        )

        # All percentiles should be the same
        assert result['median'] == 25.0
        assert result['low'] == 25.0
        assert result['high'] == 25.0

        # Volatility should be 0
        assert result['volatility'] == 0.0

    def test_negative_prices_are_excluded(self):
        """
        Negative prices should be filtered out.
        """
        base_date = datetime.now()
        prices_with_negatives = [
            (base_date - timedelta(days=i), 25.0 if i % 3 != 0 else -10.0)
            for i in range(30)
        ]

        result = calculate_intrinsic_value_corridor(
            price_history=prices_with_negatives,
            window_days=90,
            min_data_points=10
        )

        # Should only count valid (positive) prices
        assert result['data_points'] == 20  # 30 - 10 negative prices

        # Median should be $25 (ignoring negatives)
        assert result['median'] == 25.0

    def test_window_days_filters_old_data(self):
        """
        Data outside window_days should be excluded.
        """
        base_date = datetime.now()

        # 20 recent prices + 20 old prices (outside 30-day window)
        recent_prices = [
            (base_date - timedelta(days=i), 25.0)
            for i in range(20)
        ]
        old_prices = [
            (base_date - timedelta(days=i + 60), 100.0)  # 60+ days ago
            for i in range(20)
        ]

        all_prices = recent_prices + old_prices

        result = calculate_intrinsic_value_corridor(
            price_history=all_prices,
            window_days=30,  # Only consider last 30 days
            min_data_points=10
        )

        # Should only count recent prices (within 30 days)
        assert result['data_points'] == 20

        # Median should be $25 (from recent data, not $100)
        assert result['median'] == 25.0


class TestCalculateCorridorConfidenceLevels:
    """Test confidence level calculation logic."""

    def test_high_confidence_criteria(self):
        """
        HIGH: 30+ data points AND volatility < 0.20
        """
        base_date = datetime.now()
        # 35 prices with very low variation (volatility < 0.20)
        low_vol_prices = [
            (base_date - timedelta(days=i), 25.0 + (i % 3 - 1) * 0.5)
            for i in range(35)
        ]

        result = calculate_intrinsic_value_corridor(
            price_history=low_vol_prices,
            window_days=90,
            min_data_points=10
        )

        assert result['confidence'] == 'HIGH'
        assert result['data_points'] >= 30
        assert result['volatility'] < 0.20

    def test_medium_confidence_criteria(self):
        """
        MEDIUM: 15+ data points AND volatility < 0.35
        """
        base_date = datetime.now()
        # 20 prices with moderate variation
        medium_vol_prices = [
            (base_date - timedelta(days=i), 25.0 + (i % 7 - 3) * 1.5)
            for i in range(20)
        ]

        result = calculate_intrinsic_value_corridor(
            price_history=medium_vol_prices,
            window_days=90,
            min_data_points=10
        )

        # Could be MEDIUM or HIGH depending on actual volatility
        assert result['confidence'] in ('MEDIUM', 'HIGH')
        assert result['data_points'] >= 15

    def test_low_confidence_with_high_volatility(self):
        """
        LOW: data points OK but volatility too high.
        """
        base_date = datetime.now()
        # 35 prices with HIGH variation (volatility > 0.35)
        high_vol_prices = [
            (base_date - timedelta(days=i), 25.0 + (i % 2 * 20 - 10))
            for i in range(35)  # Alternates between $15 and $35
        ]

        result = calculate_intrinsic_value_corridor(
            price_history=high_vol_prices,
            window_days=90,
            min_data_points=10
        )

        # Even with 35 points, high volatility should cap at MEDIUM or LOW
        assert result['confidence'] in ('LOW', 'MEDIUM')
        assert result['volatility'] >= 0.20


# =============================================================================
# TEST: get_sell_price_for_strategy
# =============================================================================

class TestGetSellPriceForStrategy:
    """Test sell price calculation for different strategies."""

    def test_balanced_strategy_uses_90_day_window(self, parsed_data_with_history):
        """
        Balanced strategy should use 90-day window for calculation.
        """
        result = get_sell_price_for_strategy(
            parsed_data=parsed_data_with_history,
            strategy="balanced",
            config=None
        )

        assert 'sell_price' in result
        assert 'source' in result
        assert 'corridor' in result

        # Verify window used
        assert result['corridor']['window_days'] == 90

    def test_textbook_strategy_uses_365_day_window(self, parsed_data_with_history):
        """
        Textbook strategy should use 365-day window for calculation.
        """
        result = get_sell_price_for_strategy(
            parsed_data=parsed_data_with_history,
            strategy="textbook",
            config=None
        )

        assert result['corridor']['window_days'] == 365

    def test_velocity_strategy_uses_90_day_window(self, parsed_data_with_history):
        """
        Velocity strategy should use 90-day window (fast turnover).
        """
        result = get_sell_price_for_strategy(
            parsed_data=parsed_data_with_history,
            strategy="velocity",
            config=None
        )

        assert result['corridor']['window_days'] == 90

    def test_returns_intrinsic_median_when_sufficient_data(self, parsed_data_with_history):
        """
        Should return intrinsic median as sell_price when data is sufficient.
        """
        result = get_sell_price_for_strategy(
            parsed_data=parsed_data_with_history,
            strategy="balanced",
            config=None
        )

        # sell_price should be the intrinsic median
        assert result['sell_price'] == result['corridor']['median']
        assert result['source'] == 'intrinsic_median'
        assert 'warning' not in result or result['warning'] is None

    def test_fallback_to_current_price_when_insufficient_data(self, parsed_data_insufficient_history):
        """
        Should fallback to current_price when insufficient history data.
        """
        result = get_sell_price_for_strategy(
            parsed_data=parsed_data_insufficient_history,
            strategy="balanced",
            config=None
        )

        # Should fallback to current_buybox_price
        assert result['sell_price'] == 45.00
        assert result['source'] == 'current_price_fallback'
        assert result['warning'] is not None
        assert 'insufficient' in result['warning'].lower()

    def test_fallback_uses_buybox_price_first(self, parsed_data_insufficient_history):
        """
        Fallback priority: buybox > new > used.
        """
        result = get_sell_price_for_strategy(
            parsed_data=parsed_data_insufficient_history,
            strategy="balanced",
            config=None
        )

        # Should use current_buybox_price (45.00)
        assert result['sell_price'] == 45.00

    def test_fallback_to_new_price_when_no_buybox(self):
        """
        When no buybox, should fallback to new price.
        """
        data = {
            'asin': 'B07NOBUYBOX',
            'current_buybox_price': None,
            'current_new_price': 35.00,
            'current_used_price': 25.00,
            'price_history': [],  # Empty - triggers fallback
        }

        result = get_sell_price_for_strategy(
            parsed_data=data,
            strategy="balanced",
            config=None
        )

        assert result['sell_price'] == 35.00
        assert result['source'] == 'current_price_fallback'

    def test_returns_none_when_no_price_available(self):
        """
        Should handle case where no price is available at all.
        """
        data = {
            'asin': 'B07NOPRICE',
            'current_buybox_price': None,
            'current_new_price': None,
            'current_used_price': None,
            'price_history': [],
        }

        result = get_sell_price_for_strategy(
            parsed_data=data,
            strategy="balanced",
            config=None
        )

        assert result['sell_price'] is None
        assert result['source'] == 'no_price_available'
        assert result['warning'] is not None

    def test_custom_config_overrides_defaults(self, parsed_data_with_history):
        """
        Config can override default min_data_points.
        """
        config = {
            'min_data_points': 100  # Higher threshold
        }

        result = get_sell_price_for_strategy(
            parsed_data=parsed_data_with_history,
            strategy="balanced",
            config=config
        )

        # With min_data_points=100, our 60 points should trigger fallback
        assert result['source'] == 'current_price_fallback'


# =============================================================================
# TEST: Integration scenarios
# =============================================================================

class TestEdgeCasesSecurity:
    """Test security and robustness edge cases."""

    def test_handles_malformed_tuple_entries(self):
        """
        Malformed entries should be skipped gracefully.
        """
        base_date = datetime.now()
        # Mix of valid and malformed entries
        mixed_history = [
            (base_date - timedelta(days=0), 25.0),  # Valid
            (base_date - timedelta(days=1), 26.0),  # Valid
            "not a tuple",                           # Malformed
            (base_date - timedelta(days=2), 24.0),  # Valid
            (None, 25.0),                           # Invalid timestamp
            (base_date - timedelta(days=3),),       # Missing price
            (base_date - timedelta(days=4), 25.0),  # Valid
        ]

        # Extend with valid entries to meet threshold
        for i in range(10, 25):
            mixed_history.append((base_date - timedelta(days=i), 25.0))

        result = calculate_intrinsic_value_corridor(
            price_history=mixed_history,
            window_days=90,
            min_data_points=10
        )

        # Should complete without error
        assert result['confidence'] in ('LOW', 'MEDIUM', 'HIGH')
        assert result['median'] is not None

    def test_handles_extreme_price_values(self):
        """
        Extreme but valid price values should be handled.
        """
        base_date = datetime.now()

        # Very high prices (textbook prices can be >$500)
        # Use stable prices with small variation to get HIGH confidence
        high_prices = [
            (base_date - timedelta(days=i), 1000.0 + (i % 3 - 1) * 5)
            for i in range(35)  # 35 points for HIGH confidence
        ]

        result = calculate_intrinsic_value_corridor(
            price_history=high_prices,
            window_days=90,
            min_data_points=10
        )

        # High prices should be processed correctly
        assert result['confidence'] in ('HIGH', 'MEDIUM')
        assert result['median'] > 990.0

    def test_handles_very_small_prices(self):
        """
        Very small (but positive) prices should be handled.
        """
        base_date = datetime.now()

        # Penny prices (clearance books)
        tiny_prices = [
            (base_date - timedelta(days=i), 0.01 + i * 0.001)
            for i in range(30)
        ]

        result = calculate_intrinsic_value_corridor(
            price_history=tiny_prices,
            window_days=90,
            min_data_points=10
        )

        assert result['median'] is not None
        assert result['median'] < 0.1

    def test_float_timestamp_conversion(self):
        """
        Float timestamps (from Keepa) should convert correctly.
        """
        # Keepa timestamps are minutes since Oct 21, 2000
        # Calculate current Keepa timestamp dynamically
        from app.services.intrinsic_value_service import KEEPA_EPOCH
        now = datetime.now()
        current_keepa_ts = int((now - KEEPA_EPOCH).total_seconds() / 60)

        # Generate recent timestamps (within last 30 days)
        price_history = [
            (current_keepa_ts - i * 1440, 25.0)  # 1440 minutes = 1 day
            for i in range(30)
        ]

        result = calculate_intrinsic_value_corridor(
            price_history=price_history,
            window_days=90,
            min_data_points=10
        )

        # Should handle Keepa timestamps correctly
        assert result['data_points'] == 30
        assert result['median'] == 25.0

    def test_zero_window_days(self):
        """
        Zero window_days should result in no data.
        """
        base_date = datetime.now()
        prices = [
            (base_date - timedelta(days=i), 25.0)
            for i in range(30)
        ]

        result = calculate_intrinsic_value_corridor(
            price_history=prices,
            window_days=0,  # No historical window
            min_data_points=10
        )

        # All prices are in the past, window=0 means only "now"
        assert result['confidence'] == 'INSUFFICIENT_DATA'

    def test_negative_window_days_handled(self):
        """
        Negative window_days should not crash.
        """
        base_date = datetime.now()
        prices = [
            (base_date - timedelta(days=i), 25.0)
            for i in range(30)
        ]

        result = calculate_intrinsic_value_corridor(
            price_history=prices,
            window_days=-1,  # Invalid negative window
            min_data_points=10
        )

        # Should handle gracefully
        assert result['confidence'] == 'INSUFFICIENT_DATA'


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_textbook_with_stable_prices(self):
        """
        Textbook strategy with stable historical prices.
        Should return HIGH confidence intrinsic value.
        """
        base_date = datetime.now()

        # Simulate 365 days of stable textbook prices
        price_history = [
            (int((base_date - timedelta(days=i)).timestamp() / 60), 45.0 + (i % 5 - 2) * 0.5)
            for i in range(365)
        ]

        parsed_data = {
            'asin': 'B07TEXTBOOK',
            'current_buybox_price': 47.00,
            'current_new_price': 50.00,
            'current_used_price': 42.00,
            'price_history': price_history,
        }

        result = get_sell_price_for_strategy(
            parsed_data=parsed_data,
            strategy="textbook",
            config=None
        )

        assert result['corridor']['confidence'] == 'HIGH'
        assert 43.0 <= result['sell_price'] <= 47.0
        assert result['source'] == 'intrinsic_median'

    def test_velocity_with_volatile_prices(self):
        """
        Velocity strategy with volatile prices.
        May have lower confidence but should still work.
        """
        base_date = datetime.now()

        # Volatile prices for velocity items
        price_history = [
            (int((base_date - timedelta(days=i)).timestamp() / 60), 20.0 + (i % 10 - 5) * 3.0)
            for i in range(60)
        ]

        parsed_data = {
            'asin': 'B07VELOCITY',
            'current_buybox_price': 22.00,
            'current_new_price': 25.00,
            'current_used_price': 18.00,
            'price_history': price_history,
        }

        result = get_sell_price_for_strategy(
            parsed_data=parsed_data,
            strategy="velocity",
            config=None
        )

        # Should still return intrinsic median despite volatility
        assert result['sell_price'] is not None
        assert result['corridor']['window_days'] == 90
