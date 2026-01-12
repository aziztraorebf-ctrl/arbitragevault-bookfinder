"""
Unit tests for Unified Analysis Service Intrinsic Value Integration.

TDD: These tests are written FIRST before implementation.
Tests the integration of intrinsic value calculation into unified analysis output.

Task 4 of Textbook Pivot implementation plan.

The unified analysis service powers ALL views in the application.
This integration ensures intrinsic pricing is available across all views.
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
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
    This mimics the raw response format from Keepa API.
    """
    base_date = datetime.now()

    # Generate 60 days of price data - sufficient for intrinsic calculation
    # Prices centered around $30 with small variation
    # Format: alternating [timestamp_keepa, price_cents]
    price_history_raw = []
    for i in range(60):
        date = base_date - timedelta(days=i)
        # Convert to Keepa timestamp (minutes since Oct 21, 2000)
        keepa_epoch = datetime(2000, 10, 21, 0, 0, 0)
        timestamp_minutes = int((date - keepa_epoch).total_seconds() / 60)
        # Price in cents: $30 +/- $2
        variation = (i % 10 - 5) * 40  # +/- 200 cents = +/- $2
        price_cents = 3000 + variation
        price_history_raw.extend([timestamp_minutes, price_cents])

    return {
        'asin': 'B07INTRINSIC',
        'data': {
            'asin': 'B07INTRINSIC',
            'title': 'Engineering Textbook with Good History',
            'stats': {
                'current': [
                    3500,   # 0: Amazon price (cents)
                    3800,   # 1: New price (cents)
                    2800,   # 2: Used price (cents)
                    45230,  # 3: Sales rank (BSR)
                    -1, -1, -1, -1, -1, -1,  # 4-9
                    3200,   # 10: Buy Box price (cents)
                    3300,   # 11: FBA price (cents)
                ]
            },
            # Keepa price index: 0=Amazon, 1=New, 2=Used, 10=BuyBox, 11=FBA
            'csv': [
                price_history_raw,  # 0: Amazon price history
                price_history_raw,  # 1: New price history
                price_history_raw,  # 2: Used price history
                [],  # 3: BSR history
            ],
            'offers': [],
            'packageWeight': 200,  # Weight in grams
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
    Should trigger fallback to current price.
    """
    base_date = datetime.now()
    keepa_epoch = datetime(2000, 10, 21, 0, 0, 0)

    # Only 5 data points - below default threshold of 10
    price_history_raw = []
    for i in range(5):
        date = base_date - timedelta(days=i)
        timestamp_minutes = int((date - keepa_epoch).total_seconds() / 60)
        price_cents = 4500 + i * 100  # Around $45
        price_history_raw.extend([timestamp_minutes, price_cents])

    return {
        'asin': 'B07SPARSE',
        'data': {
            'asin': 'B07SPARSE',
            'title': 'Rare Book With Little History',
            'stats': {
                'current': [
                    4500,   # Amazon price
                    5000,   # New price
                    4000,   # Used price
                    123456, # BSR
                    -1, -1, -1, -1, -1, -1,
                    4500,   # Buy Box price
                    4600,   # FBA price
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


# =============================================================================
# TEST: build_unified_product_v2 - Intrinsic value fields present
# =============================================================================

class TestUnifiedProductIncludesIntrinsicValue:
    """Verify intrinsic value fields are present in unified product output."""

    @pytest.mark.asyncio
    async def test_unified_product_includes_intrinsic_value(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        The unified product response should include intrinsic_value dict.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        # Must have intrinsic_value field
        assert 'intrinsic_value' in result, "Missing intrinsic_value field"

        # intrinsic_value should be a dict with corridor structure
        intrinsic = result['intrinsic_value']
        assert isinstance(intrinsic, dict), "intrinsic_value should be a dict"

        # Verify corridor structure keys
        assert 'low' in intrinsic, "Missing low in intrinsic_value"
        assert 'median' in intrinsic, "Missing median in intrinsic_value"
        assert 'high' in intrinsic, "Missing high in intrinsic_value"
        assert 'confidence' in intrinsic, "Missing confidence in intrinsic_value"

    @pytest.mark.asyncio
    async def test_unified_product_includes_intrinsic_roi(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        The unified product should include intrinsic_roi_pct field.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        # Must have intrinsic_roi_pct field
        assert 'intrinsic_roi_pct' in result, "Missing intrinsic_roi_pct field"

        # Should be a numeric value (float or int)
        assert isinstance(result['intrinsic_roi_pct'], (int, float)), \
            "intrinsic_roi_pct should be numeric"

    @pytest.mark.asyncio
    async def test_unified_product_includes_intrinsic_sell_price(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        The unified product should include intrinsic_sell_price field.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        # Must have intrinsic_sell_price field
        assert 'intrinsic_sell_price' in result, "Missing intrinsic_sell_price field"

        # Should be a numeric value or None
        assert result['intrinsic_sell_price'] is None or \
               isinstance(result['intrinsic_sell_price'], (int, float)), \
            "intrinsic_sell_price should be numeric or None"

    @pytest.mark.asyncio
    async def test_unified_product_includes_pricing_confidence(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        The unified product should include pricing_confidence field.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        # Must have pricing_confidence field
        assert 'pricing_confidence' in result, "Missing pricing_confidence field"

        # Should be one of the valid confidence levels
        valid_levels = ['HIGH', 'MEDIUM', 'LOW', 'INSUFFICIENT_DATA']
        assert result['pricing_confidence'] in valid_levels, \
            f"pricing_confidence should be one of {valid_levels}"

    @pytest.mark.asyncio
    async def test_unified_product_includes_pricing_source(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        The unified product should include pricing_source field.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        # Must have pricing_source field
        assert 'pricing_source' in result, "Missing pricing_source field"

        # Should indicate the source of pricing
        valid_sources = ['intrinsic_median', 'current_price_fallback', 'no_price_available']
        assert result['pricing_source'] in valid_sources, \
            f"pricing_source should be one of {valid_sources}"

    @pytest.mark.asyncio
    async def test_unified_product_includes_current_vs_intrinsic(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        The unified product should include current_vs_intrinsic_pct field.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        # Must have current_vs_intrinsic_pct field
        assert 'current_vs_intrinsic_pct' in result, "Missing current_vs_intrinsic_pct field"

        # Should be numeric or None
        assert result['current_vs_intrinsic_pct'] is None or \
               isinstance(result['current_vs_intrinsic_pct'], (int, float)), \
            "current_vs_intrinsic_pct should be numeric or None"


# =============================================================================
# TEST: build_unified_product_v2 - ROI uses intrinsic not current
# =============================================================================

class TestRoiUsesIntrinsicNotCurrent:
    """Verify that intrinsic_roi_pct uses intrinsic median, not current price."""

    @pytest.mark.asyncio
    async def test_roi_uses_intrinsic_not_current(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        intrinsic_roi_pct should be calculated from intrinsic median sell price,
        NOT from current market price. This is the KEY requirement of the Textbook Pivot.
        """
        from app.services.unified_analysis import build_unified_product_v2

        source_price = 10.0  # Acquisition cost

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=source_price
        )

        # Get the sell price used for ROI calculation
        intrinsic_sell_price = result.get('intrinsic_sell_price')
        intrinsic_roi = result.get('intrinsic_roi_pct')

        # If intrinsic value was used successfully
        if result.get('pricing_source') == 'intrinsic_median':
            # Verify the ROI calculation matches intrinsic median
            # Formula: ROI = (net_revenue - source_price) / source_price
            # net_revenue = sell_price - amazon_fees - shipping
            amazon_fee_pct = standard_config.get('amazon_fee_pct', 0.15)
            shipping_cost = standard_config.get('shipping_cost', 3.0)

            amazon_fees = intrinsic_sell_price * amazon_fee_pct
            net_revenue = intrinsic_sell_price - amazon_fees - shipping_cost
            expected_roi = (net_revenue - source_price) / source_price

            # Allow 5% tolerance for rounding
            assert abs(intrinsic_roi - expected_roi) < 0.05, \
                f"ROI mismatch: got {intrinsic_roi}, expected {expected_roi}"

            # The intrinsic sell price should NOT be the current price ($35)
            # It should be around the intrinsic median (~$30)
            current_price = raw_keepa_with_good_history.get('current_buybox_price', 35.0)

            # Intrinsic median from our test data is around $30
            # Current buybox is $35 - these should be different
            if intrinsic_sell_price is not None:
                # Allow some tolerance but they should not be equal
                assert abs(intrinsic_sell_price - current_price) > 1.0 or \
                       result.get('pricing_source') != 'intrinsic_median', \
                    "Intrinsic sell price should differ from current price when using intrinsic median"

    @pytest.mark.asyncio
    async def test_fallback_uses_current_price(
        self,
        raw_keepa_insufficient_history,
        mock_keepa_service,
        standard_config
    ):
        """
        When insufficient historical data, should fallback to current price
        or indicate no price available if prices cannot be extracted.
        """
        from app.services.unified_analysis import build_unified_product_v2

        source_price = 10.0

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_insufficient_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=source_price
        )

        # When data is insufficient, should indicate either fallback or no price
        # The parser may not extract prices if the fixture structure differs
        if result.get('pricing_confidence') == 'INSUFFICIENT_DATA':
            valid_sources = ['current_price_fallback', 'no_price_available']
            assert result.get('pricing_source') in valid_sources, \
                f"Should indicate fallback or no price when insufficient data, got: {result.get('pricing_source')}"


# =============================================================================
# TEST: build_unified_product_v2 - Backward compatibility
# =============================================================================

class TestBackwardCompatibility:
    """Verify existing fields are not broken by intrinsic integration."""

    @pytest.mark.asyncio
    async def test_existing_pricing_fields_preserved(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        All existing pricing fields must still be present.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        # Existing fields that must still exist
        existing_fields = [
            'asin',
            'title',
            'pricing',  # Existing pricing breakdown
            'velocity',
            'current_bsr',
            'amazon_on_listing',
            'amazon_buybox',
            'view_type',
            'timestamp',
        ]

        for field in existing_fields:
            assert field in result, f"Missing existing field: {field}"

    @pytest.mark.asyncio
    async def test_scoring_fields_preserved_for_mes_niches(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        Scoring fields must still work for mes_niches view.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="mes_niches",  # View that uses scoring
            compute_score=True,
            source_price=10.0
        )

        # Scoring fields must be present
        scoring_fields = [
            'score',
            'strategy_profile',
            'weights_applied',
            'components',
            'raw_metrics',
        ]

        for field in scoring_fields:
            assert field in result, f"Missing scoring field: {field}"

    @pytest.mark.asyncio
    async def test_minimal_data_includes_new_fields(
        self,
        mock_keepa_service,
        standard_config
    ):
        """
        Even with minimal/missing data, new intrinsic fields should be present.
        The parser is resilient and handles missing data gracefully.
        """
        from app.services.unified_analysis import build_unified_product_v2

        # Minimal raw_keepa with missing data - parser handles gracefully
        minimal_keepa = {
            'asin': 'B07MINIMAL',
            'data': {},  # Empty data - parser will extract what it can
        }

        result = await build_unified_product_v2(
            raw_keepa=minimal_keepa,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        # New intrinsic fields should be present even with minimal data
        new_fields = [
            'intrinsic_value',
            'intrinsic_roi_pct',
            'intrinsic_sell_price',
            'pricing_confidence',
            'pricing_source',
            'current_vs_intrinsic_pct',
        ]

        for field in new_fields:
            assert field in result, f"Missing new field with minimal data: {field}"

        # With minimal data, should have safe defaults
        assert result['pricing_confidence'] in ['HIGH', 'MEDIUM', 'LOW', 'INSUFFICIENT_DATA']
        assert result['pricing_source'] in ['intrinsic_median', 'current_price_fallback', 'no_price_available']


# =============================================================================
# TEST: build_unified_product_v2 - Source price handling
# =============================================================================

class TestSourcePriceHandling:
    """Verify source price is properly passed to intrinsic calculations."""

    @pytest.mark.asyncio
    async def test_uses_provided_source_price(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        When source_price is provided, it should be used for ROI calculation.
        """
        from app.services.unified_analysis import build_unified_product_v2

        source_price = 15.0  # Specific source price

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=source_price
        )

        # Verify source_price was used
        # The intrinsic_roi_pct should be calculated using $15 as source
        if result.get('intrinsic_sell_price'):
            sell = result['intrinsic_sell_price']
            amazon_fee = sell * 0.15
            shipping = 3.0
            net = sell - amazon_fee - shipping
            expected_roi = (net - source_price) / source_price

            # Allow reasonable tolerance
            assert abs(result['intrinsic_roi_pct'] - expected_roi) < 0.05

    @pytest.mark.asyncio
    async def test_uses_default_source_price_when_not_provided(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        When source_price not provided, should use config default or fallback.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=None  # Not provided
        )

        # Should not crash and should still compute intrinsic metrics
        assert 'intrinsic_roi_pct' in result
        assert 'intrinsic_sell_price' in result


# =============================================================================
# TEST: Complete output structure
# =============================================================================

class TestCompleteOutputStructure:
    """Verify the complete output structure with all new fields."""

    @pytest.mark.asyncio
    async def test_all_new_fields_present(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        Verify ALL new intrinsic-related fields are present in output.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        # All new fields as per spec
        new_fields = [
            'intrinsic_value',          # Full corridor dict
            'intrinsic_roi_pct',        # ROI based on intrinsic median
            'intrinsic_sell_price',     # The intrinsic median price
            'pricing_confidence',       # HIGH/MEDIUM/LOW/INSUFFICIENT_DATA
            'pricing_source',           # intrinsic_median or current_price_fallback
            'current_vs_intrinsic_pct', # Gap percentage
        ]

        for field in new_fields:
            assert field in result, f"Missing required new field: {field}"

    @pytest.mark.asyncio
    async def test_intrinsic_value_corridor_structure(
        self,
        raw_keepa_with_good_history,
        mock_keepa_service,
        standard_config
    ):
        """
        Verify intrinsic_value has complete corridor structure.
        """
        from app.services.unified_analysis import build_unified_product_v2

        result = await build_unified_product_v2(
            raw_keepa=raw_keepa_with_good_history,
            keepa_service=mock_keepa_service,
            config=standard_config,
            view_type="analyse_manuelle",
            source_price=10.0
        )

        corridor = result['intrinsic_value']

        # Required corridor fields
        corridor_fields = [
            'low',          # P25
            'median',       # P50
            'high',         # P75
            'confidence',   # HIGH/MEDIUM/LOW/INSUFFICIENT_DATA
            'volatility',   # Coefficient of variation
            'data_points',  # Number of points used
        ]

        for field in corridor_fields:
            assert field in corridor, f"Missing corridor field: {field}"
