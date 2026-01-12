"""
Unit tests for Unified Analysis Service Buying Guidance Integration.

TDD: These tests are written FIRST before implementation.
Tests the integration of buying guidance into unified analysis output.

Task 2 of Textbook UX Simplification plan.

The buying guidance provides user-friendly recommendations with:
- max_buy_price: Maximum price to pay for target ROI
- target_sell_price: Expected sell price (intrinsic median)
- estimated_profit: Net profit after fees
- recommendation: BUY/HOLD/SKIP with reason
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_keepa_service():
    """Mock KeepaService for async tests."""
    service = MagicMock()
    service.get_product_data = AsyncMock(return_value=None)
    return service


@pytest.fixture
def standard_config() -> Dict[str, Any]:
    """Standard business configuration."""
    return {
        'amazon_fee_pct': 0.15,
        'shipping_cost': 3.0,
        'default_source_price': 8.0,
        'roi': {
            'target_roi_percent': 30
        }
    }


@pytest.fixture
def raw_keepa_with_good_history() -> Dict[str, Any]:
    """
    Raw Keepa data with sufficient price history for intrinsic calculation.
    Prices centered around $30 with good velocity.
    """
    base_date = datetime.now()
    keepa_epoch = datetime(2000, 10, 21, 0, 0, 0)

    # Generate 60 days of price data
    price_history_raw = []
    for i in range(60):
        date = base_date - timedelta(days=i)
        timestamp_minutes = int((date - keepa_epoch).total_seconds() / 60)
        variation = (i % 10 - 5) * 40  # +/- 200 cents = +/- $2
        price_cents = 3000 + variation
        price_history_raw.extend([timestamp_minutes, price_cents])

    # Generate BSR history with sales drops (for velocity calculation)
    bsr_history_raw = []
    for i in range(60):
        date = base_date - timedelta(days=i)
        timestamp_minutes = int((date - keepa_epoch).total_seconds() / 60)
        # BSR drops from 50000 to 45000 occasionally (indicates sales)
        bsr = 50000 - (i % 5) * 1000  # Creates "drops" for velocity
        bsr_history_raw.extend([timestamp_minutes, bsr])

    return {
        'asin': 'B07GUIDANCE',
        'data': {
            'asin': 'B07GUIDANCE',
            'title': 'Engineering Textbook for Guidance Test',
            'stats': {
                'current': [
                    3500,   # 0: Amazon price (cents)
                    3800,   # 1: New price (cents)
                    2800,   # 2: Used price (cents)
                    45230,  # 3: Sales rank (BSR)
                    -1, -1, -1, -1, -1, -1,
                    3200,   # 10: Buy Box price (cents)
                    3300,   # 11: FBA price (cents)
                ]
            },
            'csv': [
                price_history_raw,  # 0: Amazon price history
                price_history_raw,  # 1: New price history
                price_history_raw,  # 2: Used price history
                bsr_history_raw,    # 3: BSR history
            ],
            'offers': [],
            'packageWeight': 200,
        },
        'price_history': [
            (int((base_date - timedelta(days=i)).timestamp() / 60), 30.0 + (i % 10 - 5) * 0.4)
            for i in range(60)
        ],
        'current_buybox_price': 35.00,
        'current_new_price': 38.00,
        'current_used_price': 28.00,
    }


@pytest.fixture
def raw_keepa_insufficient_history() -> Dict[str, Any]:
    """
    Raw Keepa data with insufficient price history.
    Should trigger SKIP recommendation.
    """
    base_date = datetime.now()
    keepa_epoch = datetime(2000, 10, 21, 0, 0, 0)

    # Only 5 data points - below threshold
    price_history_raw = []
    for i in range(5):
        date = base_date - timedelta(days=i)
        timestamp_minutes = int((date - keepa_epoch).total_seconds() / 60)
        price_cents = 4500 + i * 100
        price_history_raw.extend([timestamp_minutes, price_cents])

    return {
        'asin': 'B07SPARSE',
        'data': {
            'asin': 'B07SPARSE',
            'title': 'Rare Book With Little History',
            'stats': {
                'current': [
                    4500, 5000, 4000, 123456, -1, -1, -1, -1, -1, -1, 4500, 4600
                ]
            },
            'csv': [
                price_history_raw,
                price_history_raw,
                price_history_raw,
                [],
            ],
            'offers': [],
            'packageWeight': 150,
        },
        'price_history': [
            (int((base_date - timedelta(days=i)).timestamp() / 60), 45.0 + i)
            for i in range(5)
        ],
        'current_buybox_price': 45.00,
        'current_new_price': 50.00,
        'current_used_price': 40.00,
    }


@pytest.fixture
def raw_keepa_high_roi_opportunity() -> Dict[str, Any]:
    """
    Raw Keepa data for a high ROI opportunity.
    Intrinsic median ~$50, source price ~$10 = high ROI.
    """
    base_date = datetime.now()
    keepa_epoch = datetime(2000, 10, 21, 0, 0, 0)

    # 60 days of higher price data (~$50)
    price_history_raw = []
    for i in range(60):
        date = base_date - timedelta(days=i)
        timestamp_minutes = int((date - keepa_epoch).total_seconds() / 60)
        variation = (i % 8 - 4) * 50
        price_cents = 5000 + variation  # ~$50
        price_history_raw.extend([timestamp_minutes, price_cents])

    # Good velocity BSR history
    bsr_history_raw = []
    for i in range(60):
        date = base_date - timedelta(days=i)
        timestamp_minutes = int((date - keepa_epoch).total_seconds() / 60)
        bsr = 30000 - (i % 3) * 2000  # Frequent drops = good velocity
        bsr_history_raw.extend([timestamp_minutes, bsr])

    return {
        'asin': 'B07HIGHROI',
        'data': {
            'asin': 'B07HIGHROI',
            'title': 'High Value Textbook',
            'stats': {
                'current': [
                    5200, 5500, 4800, 30000, -1, -1, -1, -1, -1, -1, 5000, 5100
                ]
            },
            'csv': [
                price_history_raw,
                price_history_raw,
                price_history_raw,
                bsr_history_raw,
            ],
            'offers': [],
            'packageWeight': 250,
        },
        'price_history': [
            (int((base_date - timedelta(days=i)).timestamp() / 60), 50.0 + (i % 8 - 4) * 0.5)
            for i in range(60)
        ],
        'current_buybox_price': 52.00,
        'current_new_price': 55.00,
        'current_used_price': 48.00,
    }


# =============================================================================
# TEST 1: Response includes buying_guidance section
# =============================================================================

class TestBuyingGuidanceSectionPresent:
    """Verify buying_guidance section is present in unified response."""

    @pytest.mark.asyncio
    async def test_response_includes_buying_guidance(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        The unified product response MUST include a buying_guidance section.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        # Must have buying_guidance field
        assert 'buying_guidance' in result, "Missing buying_guidance section in response"

    @pytest.mark.asyncio
    async def test_buying_guidance_is_dict(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        buying_guidance should be a dictionary.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        assert isinstance(result.get('buying_guidance'), dict), \
            "buying_guidance should be a dict"

    @pytest.mark.asyncio
    async def test_buying_guidance_has_required_fields(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        buying_guidance must have all required fields.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        guidance = result.get('buying_guidance', {})

        required_fields = [
            'max_buy_price',
            'target_sell_price',
            'estimated_profit',
            'estimated_roi_pct',
            'price_range',
            'estimated_days_to_sell',
            'recommendation',
            'recommendation_reason',
            'confidence_label',
            'explanations',
        ]

        for field in required_fields:
            assert field in guidance, f"Missing required field in buying_guidance: {field}"


# =============================================================================
# TEST 2: Guidance uses intrinsic median for target_sell_price
# =============================================================================

class TestGuidanceUsesIntrinsicMedian:
    """Verify guidance uses intrinsic median for target sell price."""

    @pytest.mark.asyncio
    async def test_target_sell_price_uses_intrinsic_median(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        target_sell_price in buying_guidance should use intrinsic median,
        NOT the current snapshot price.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        guidance = result.get('buying_guidance', {})
        intrinsic_value = result.get('intrinsic_value', {})

        # If we have intrinsic data, target_sell_price should match median
        if intrinsic_value.get('median') is not None:
            expected_median = intrinsic_value['median']
            actual_target = guidance.get('target_sell_price')

            assert actual_target == expected_median, \
                f"target_sell_price ({actual_target}) should match intrinsic median ({expected_median})"

    @pytest.mark.asyncio
    async def test_max_buy_price_calculated_from_intrinsic(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        max_buy_price should be calculated from intrinsic median, not current price.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        guidance = result.get('buying_guidance', {})
        intrinsic_value = result.get('intrinsic_value', {})

        max_buy = guidance.get('max_buy_price')

        # max_buy_price should be positive when we have intrinsic data
        if intrinsic_value.get('median') is not None and intrinsic_value['median'] > 0:
            assert max_buy is not None, "max_buy_price should not be None with valid intrinsic data"
            assert max_buy >= 0, "max_buy_price should be non-negative"


# =============================================================================
# TEST 3: Guidance with source_price calculates real ROI
# =============================================================================

class TestGuidanceWithSourcePrice:
    """Verify guidance calculates accurate ROI with provided source price."""

    @pytest.mark.asyncio
    async def test_estimated_roi_uses_source_price(
        self,
        raw_keepa_high_roi_opportunity,
        mock_keepa_service,
        standard_config
    ):
        """
        estimated_roi_pct should be calculated using the provided source_price.
        """
        from app.services.unified_analysis import build_unified_product_v2

        source_price = 10.0  # Low source price for high ROI

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_high_roi_opportunity,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=source_price
        )

        guidance = result.get('buying_guidance', {})

        # With $50 sell price and $10 source, ROI should be high
        estimated_roi = guidance.get('estimated_roi_pct', 0)

        # After 22% fees on $50 = $39 net, minus $10 source = $29 profit
        # ROI = $29 / $10 = 290%
        # Allow tolerance but should be > 100%
        if result.get('pricing_confidence') != 'INSUFFICIENT_DATA':
            assert estimated_roi > 50, \
                f"Expected high ROI with low source price, got {estimated_roi}%"

    @pytest.mark.asyncio
    async def test_estimated_profit_is_accurate(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        estimated_profit should = (sell_price * (1 - fee_pct)) - source_price
        """
        from app.services.unified_analysis import build_unified_product_v2

        source_price = 10.0

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=source_price
        )

        guidance = result.get('buying_guidance', {})
        target_sell = guidance.get('target_sell_price', 0)
        estimated_profit = guidance.get('estimated_profit', 0)

        # Calculate expected profit
        # Default fee is 22% (from buying_guidance_service)
        fee_pct = 0.22
        expected_profit = (target_sell * (1 - fee_pct)) - source_price

        if target_sell > 0:
            # Allow $0.50 tolerance for rounding
            assert abs(estimated_profit - expected_profit) < 0.5, \
                f"Profit mismatch: got {estimated_profit}, expected {expected_profit}"


# =============================================================================
# TEST 4: Guidance without source_price uses max_buy_price reference
# =============================================================================

class TestGuidanceWithoutSourcePrice:
    """Verify guidance behavior when source_price is not provided."""

    @pytest.mark.asyncio
    async def test_uses_default_source_price(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        When source_price not provided, should use config default.
        """
        from app.services.unified_analysis import build_unified_product_v2

        # Source price not provided - should use config default (8.0)
        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=None
        )

        guidance = result.get('buying_guidance', {})

        # Should still have valid guidance
        assert guidance.get('max_buy_price') is not None, \
            "max_buy_price should be calculated even without explicit source_price"
        assert guidance.get('estimated_roi_pct') is not None, \
            "estimated_roi_pct should be calculated with default source_price"

    @pytest.mark.asyncio
    async def test_max_buy_price_is_usable_reference(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        max_buy_price should be a usable reference for sourcing decisions.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=None
        )

        guidance = result.get('buying_guidance', {})
        intrinsic = result.get('intrinsic_value', {})

        max_buy = guidance.get('max_buy_price', 0)
        target_sell = guidance.get('target_sell_price', 0)

        # max_buy_price should be less than target_sell_price (to make profit)
        if target_sell > 0 and intrinsic.get('confidence') != 'INSUFFICIENT_DATA':
            assert max_buy < target_sell, \
                f"max_buy_price ({max_buy}) should be < target_sell_price ({target_sell})"


# =============================================================================
# TEST 5: Insufficient data returns SKIP recommendation
# =============================================================================

class TestInsufficientDataSkipRecommendation:
    """Verify SKIP recommendation for insufficient data cases."""

    @pytest.mark.asyncio
    async def test_insufficient_data_returns_skip(
        self,
        raw_keepa_insufficient_history,
        mock_keepa_service,
        standard_config
    ):
        """
        When price history is insufficient, recommendation should be SKIP.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_insufficient_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        guidance = result.get('buying_guidance', {})
        pricing_confidence = result.get('pricing_confidence')

        # If insufficient data detected, should recommend SKIP
        if pricing_confidence == 'INSUFFICIENT_DATA':
            assert guidance.get('recommendation') == 'SKIP', \
                "Should recommend SKIP when data is insufficient"

    @pytest.mark.asyncio
    async def test_insufficient_data_has_explanation(
        self,
        raw_keepa_insufficient_history,
        mock_keepa_service,
        standard_config
    ):
        """
        SKIP recommendation should have a clear reason.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_insufficient_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        guidance = result.get('buying_guidance', {})
        pricing_confidence = result.get('pricing_confidence')

        if pricing_confidence == 'INSUFFICIENT_DATA':
            reason = guidance.get('recommendation_reason', '')
            assert len(reason) > 10, "SKIP recommendation should have explanation"

    @pytest.mark.asyncio
    async def test_insufficient_data_confidence_label_french(
        self,
        raw_keepa_insufficient_history,
        mock_keepa_service,
        standard_config
    ):
        """
        Confidence label should be in French.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_insufficient_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        guidance = result.get('buying_guidance', {})
        pricing_confidence = result.get('pricing_confidence')

        if pricing_confidence == 'INSUFFICIENT_DATA':
            label = guidance.get('confidence_label', '')
            # French label for insufficient data
            assert label == 'Donnees insuffisantes', \
                f"Expected French label 'Donnees insuffisantes', got '{label}'"


# =============================================================================
# TEST 6: Explanations dictionary for tooltips
# =============================================================================

class TestExplanationsDictionary:
    """Verify explanations dict is present for frontend tooltips."""

    @pytest.mark.asyncio
    async def test_explanations_is_dict(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        explanations should be a dictionary with tooltip content.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        guidance = result.get('buying_guidance', {})
        explanations = guidance.get('explanations', {})

        assert isinstance(explanations, dict), "explanations should be a dict"

    @pytest.mark.asyncio
    async def test_explanations_has_key_fields(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        explanations should have entries for key guidance fields.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        guidance = result.get('buying_guidance', {})
        explanations = guidance.get('explanations', {})

        expected_keys = [
            'max_buy_price',
            'target_sell_price',
            'estimated_profit',
            'estimated_roi_pct',
        ]

        for key in expected_keys:
            assert key in explanations, f"Missing explanation for: {key}"
            assert len(explanations[key]) > 5, f"Explanation for {key} seems too short"


# =============================================================================
# TEST 7: Error handling - no crash on edge cases
# =============================================================================

class TestErrorHandling:
    """Verify graceful handling of edge cases."""

    @pytest.mark.asyncio
    async def test_minimal_data_no_crash(
        self,
        mock_keepa_service,
        standard_config
    ):
        """
        Minimal/missing data should not crash, should return safe defaults.
        """
        from app.services.unified_analysis import build_unified_product_v2

        minimal_keepa = {
            'asin': 'B07MINIMAL',
            'data': {},
        }

        result = await build_unified_product_v2(
            raw_keepa=minimal_keepa,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        # Should not crash and should have buying_guidance
        assert 'buying_guidance' in result, "buying_guidance should be present even with minimal data"

        guidance = result.get('buying_guidance', {})
        assert guidance.get('recommendation') is not None, "Should have some recommendation"

    @pytest.mark.asyncio
    async def test_zero_source_price_handled(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        Zero source price should be handled gracefully (no division by zero).
        """
        from app.services.unified_analysis import build_unified_product_v2

        # This should not crash
        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=0.0  # Edge case: zero source price
        )

        # Should not crash
        assert 'buying_guidance' in result
        guidance = result.get('buying_guidance', {})

        # ROI calculation with zero source should not raise exception
        assert guidance.get('estimated_roi_pct') is not None
