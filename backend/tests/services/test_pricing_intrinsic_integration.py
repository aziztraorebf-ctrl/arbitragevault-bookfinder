"""
Unit tests for Pricing Service Intrinsic Value Integration.

TDD: These tests are written FIRST before implementation.
Tests the integration of intrinsic value calculation into pricing metrics.

Task 3 of Textbook Pivot implementation plan.
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def parsed_data_with_good_history() -> Dict[str, Any]:
    """
    Parsed Keepa data with sufficient price history for intrinsic calculation.
    60 data points with stable prices around $30.
    """
    base_date = datetime.now()

    # Generate 60 days of price data - sufficient for intrinsic calculation
    price_history = []
    for i in range(60):
        date = base_date - timedelta(days=i)
        # Price varies between $28 and $32, centered around $30
        variation = (i % 10 - 5) * 0.4  # +/- $2
        price = 30.0 + variation
        timestamp_minutes = int(date.timestamp() / 60)
        price_history.append((timestamp_minutes, price))

    return {
        'asin': 'B07INTRINSIC',
        'title': 'Book With Good Price History',
        'current_buybox_price': 35.00,  # Higher than intrinsic median
        'current_new_price': 38.00,
        'current_used_price': 28.00,
        'price_history': price_history,
        'bsr_history': [],
        'offers_by_condition': {
            'new': {'minimum_price': 38.00, 'seller_count': 5},
            'good': {'minimum_price': 28.00, 'seller_count': 8},
        }
    }


@pytest.fixture
def parsed_data_insufficient_history() -> Dict[str, Any]:
    """
    Parsed Keepa data with insufficient price history.
    Only 5 data points - triggers fallback to current price.
    """
    base_date = datetime.now()

    # Only 5 points - below default threshold of 10
    price_history = [
        (int((base_date - timedelta(days=i)).timestamp() / 60), 25.0 + i)
        for i in range(5)
    ]

    return {
        'asin': 'B07SPARSE',
        'title': 'Rare Book With Little History',
        'current_buybox_price': 45.00,
        'current_new_price': 50.00,
        'current_used_price': 40.00,
        'price_history': price_history,
        'bsr_history': [],
        'offers_by_condition': {}
    }


@pytest.fixture
def standard_config() -> Dict[str, Any]:
    """Standard pricing configuration."""
    return {
        'amazon_fee_pct': 0.15,
        'shipping_cost': 3.0,
    }


# =============================================================================
# TEST: calculate_pricing_metrics_with_intrinsic - Intrinsic value usage
# =============================================================================

class TestUsesIntrinsicValueWhenAvailable:
    """Verify intrinsic median is used instead of current price when available."""

    def test_uses_intrinsic_value_when_available(
        self,
        parsed_data_with_good_history,
        standard_config
    ):
        """
        When sufficient price history exists, should use intrinsic median
        as the sell price, NOT the current price.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        source_price = 10.0  # Acquisition cost

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data_with_good_history,
            source_price=source_price,
            config=standard_config,
            strategy="balanced"
        )

        # Key assertion: sell_price_used should be the intrinsic median (~$30)
        # NOT the current_buybox_price ($35)
        assert result['sell_price_used'] is not None

        # Intrinsic median should be around $30 (our test data center)
        assert 28.0 <= result['sell_price_used'] <= 32.0

        # Should NOT be the current buybox price
        assert result['sell_price_used'] != 35.0

        # Source should indicate intrinsic value was used
        assert result['pricing_source'] == 'intrinsic_median'

        # No warning when intrinsic value is available
        assert result.get('pricing_warning') is None

    def test_roi_calculated_from_intrinsic_not_current(
        self,
        parsed_data_with_good_history,
        standard_config
    ):
        """
        ROI should be calculated using the intrinsic median,
        giving a more conservative (accurate) estimate.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        source_price = 10.0

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data_with_good_history,
            source_price=source_price,
            config=standard_config,
            strategy="balanced"
        )

        # Verify ROI calculation components
        sell_price = result['sell_price_used']  # Should be ~$30
        amazon_fees = sell_price * 0.15  # 15% = ~$4.50
        shipping = 3.0
        expected_net = sell_price - amazon_fees - shipping  # ~$22.50
        expected_roi = (expected_net - source_price) / source_price  # ~1.25 = 125%

        # Verify our calculations match the result
        assert abs(result['amazon_fees'] - amazon_fees) < 0.01
        assert abs(result['net_revenue'] - expected_net) < 0.01
        assert abs(result['roi_pct'] - expected_roi) < 0.05  # Allow 5% tolerance

    def test_current_price_included_for_comparison(
        self,
        parsed_data_with_good_history,
        standard_config
    ):
        """
        Even when using intrinsic value, current price should be included
        for comparison purposes.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        source_price = 10.0

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data_with_good_history,
            source_price=source_price,
            config=standard_config,
            strategy="balanced"
        )

        # Current price should be available for comparison
        assert 'current_price' in result
        assert result['current_price'] == 35.0  # The buybox price

        # Gap between current and intrinsic should be calculated
        assert 'current_vs_intrinsic_pct' in result
        # Current ($35) is ~17% higher than intrinsic (~$30)
        assert result['current_vs_intrinsic_pct'] > 0  # Positive = current higher


# =============================================================================
# TEST: calculate_pricing_metrics_with_intrinsic - Fallback behavior
# =============================================================================

class TestFallbackToCurrentPrice:
    """Verify fallback to current price when insufficient historical data."""

    def test_fallback_to_current_price(
        self,
        parsed_data_insufficient_history,
        standard_config
    ):
        """
        When insufficient price history, should fallback to current price
        and include a warning.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        source_price = 10.0

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data_insufficient_history,
            source_price=source_price,
            config=standard_config,
            strategy="balanced"
        )

        # Should fallback to current buybox price
        assert result['sell_price_used'] == 45.0

        # Source should indicate fallback
        assert result['pricing_source'] == 'current_price_fallback'

        # Warning should be present explaining why fallback was used
        assert result['pricing_warning'] is not None
        assert 'insufficient' in result['pricing_warning'].lower()

    def test_roi_calculated_from_fallback_price(
        self,
        parsed_data_insufficient_history,
        standard_config
    ):
        """
        When using fallback, ROI should be calculated from current price.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        source_price = 10.0

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data_insufficient_history,
            source_price=source_price,
            config=standard_config,
            strategy="balanced"
        )

        # Verify ROI uses fallback price ($45)
        sell_price = 45.0
        amazon_fees = sell_price * 0.15  # $6.75
        shipping = 3.0
        expected_net = sell_price - amazon_fees - shipping  # $35.25
        expected_roi = (expected_net - source_price) / source_price  # 2.525 = 252.5%

        assert abs(result['roi_pct'] - expected_roi) < 0.05


# =============================================================================
# TEST: calculate_pricing_metrics_with_intrinsic - Confidence in output
# =============================================================================

class TestIncludesConfidenceInOutput:
    """Verify confidence information is included in output."""

    def test_includes_confidence_in_output(
        self,
        parsed_data_with_good_history,
        standard_config
    ):
        """
        Output should include pricing confidence from intrinsic calculation.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        source_price = 10.0

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data_with_good_history,
            source_price=source_price,
            config=standard_config,
            strategy="balanced"
        )

        # Confidence should be present
        assert 'pricing_confidence' in result
        assert result['pricing_confidence'] in ('HIGH', 'MEDIUM', 'LOW', 'INSUFFICIENT_DATA')

        # With 60 data points and stable prices, should be HIGH or MEDIUM
        assert result['pricing_confidence'] in ('HIGH', 'MEDIUM')

    def test_includes_intrinsic_value_corridor(
        self,
        parsed_data_with_good_history,
        standard_config
    ):
        """
        Output should include the full intrinsic value corridor for transparency.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        source_price = 10.0

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data_with_good_history,
            source_price=source_price,
            config=standard_config,
            strategy="balanced"
        )

        # Full corridor should be included
        assert 'intrinsic_value' in result
        corridor = result['intrinsic_value']

        # Verify corridor structure
        assert 'low' in corridor
        assert 'median' in corridor
        assert 'high' in corridor
        assert 'confidence' in corridor
        assert 'volatility' in corridor
        assert 'data_points' in corridor


# =============================================================================
# TEST: calculate_pricing_metrics_with_intrinsic - Output structure
# =============================================================================

class TestOutputStructure:
    """Verify the complete output structure is correct."""

    def test_complete_output_structure(
        self,
        parsed_data_with_good_history,
        standard_config
    ):
        """
        Verify all required fields are present in the output.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        source_price = 10.0

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data_with_good_history,
            source_price=source_price,
            config=standard_config,
            strategy="balanced"
        )

        # All required fields as per spec
        required_fields = [
            'sell_price_used',
            'source_price',
            'amazon_fees',
            'shipping_cost',
            'net_revenue',
            'roi_value',
            'roi_pct',
            'profit_margin',
            'intrinsic_value',
            'pricing_source',
            'pricing_confidence',
            'current_price',
            'current_vs_intrinsic_pct',
            'strategy',
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_strategy_is_included_in_output(
        self,
        parsed_data_with_good_history,
        standard_config
    ):
        """
        The strategy parameter should be reflected in output.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        source_price = 10.0

        for strategy in ['balanced', 'textbook', 'velocity']:
            result = calculate_pricing_metrics_with_intrinsic(
                parsed_data=parsed_data_with_good_history,
                source_price=source_price,
                config=standard_config,
                strategy=strategy
            )

            assert result['strategy'] == strategy


# =============================================================================
# TEST: calculate_pricing_metrics_with_intrinsic - Edge cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_source_price_handled(
        self,
        parsed_data_with_good_history,
        standard_config
    ):
        """
        Zero source price should be handled gracefully.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        source_price = 0.0

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data_with_good_history,
            source_price=source_price,
            config=standard_config,
            strategy="balanced"
        )

        # Should not crash, ROI should be 0 or handled appropriately
        assert result['sell_price_used'] is not None
        assert result['roi_pct'] == 0 or result['roi_value'] == result['net_revenue']

    def test_negative_source_price_handled(
        self,
        parsed_data_with_good_history,
        standard_config
    ):
        """
        Negative source price should be handled gracefully.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        source_price = -5.0

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data_with_good_history,
            source_price=source_price,
            config=standard_config,
            strategy="balanced"
        )

        # Should not crash
        assert result is not None

    def test_empty_config_uses_defaults(
        self,
        parsed_data_with_good_history
    ):
        """
        Empty config should use default values.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        source_price = 10.0

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data_with_good_history,
            source_price=source_price,
            config={},  # Empty config
            strategy="balanced"
        )

        # Should use default shipping_cost of 3.0
        assert result['shipping_cost'] == 3.0

        # Default amazon fee is 15%
        sell_price = result['sell_price_used']
        expected_fees = sell_price * 0.15
        assert abs(result['amazon_fees'] - expected_fees) < 0.01

    def test_no_price_available_scenario(self, standard_config):
        """
        Handle case where no price is available at all.
        """
        from app.services.pricing_service import calculate_pricing_metrics_with_intrinsic

        parsed_data = {
            'asin': 'B07NOPRICE',
            'current_buybox_price': None,
            'current_new_price': None,
            'current_used_price': None,
            'price_history': [],
        }

        source_price = 10.0

        result = calculate_pricing_metrics_with_intrinsic(
            parsed_data=parsed_data,
            source_price=source_price,
            config=standard_config,
            strategy="balanced"
        )

        # Should handle gracefully with None or warning
        assert result['sell_price_used'] is None or result['pricing_warning'] is not None
