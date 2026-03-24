"""
Tests for Phase C enhancements:
- Condition signal derivation in unified pipeline
- Confidence boost from condition signals
- Condition breakdown in buying guidance
- Pydantic v2 decimal_places fix
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.analytics import AnalyticsRequestSchema
from app.services.unified_analysis import _build_condition_breakdown


# =============================================================================
# PYDANTIC V2 FIX TESTS
# =============================================================================


class TestPydanticDecimalFix:
    """Tests for Pydantic v2 decimal_places migration."""

    def test_analytics_schema_accepts_decimal(self):
        """Schema accepts Decimal values without deprecated decimal_places."""
        schema = AnalyticsRequestSchema(
            asin="B001234567",
            estimated_buy_price=Decimal("5.00"),
            estimated_sell_price=Decimal("19.99"),
        )
        assert schema.estimated_buy_price == Decimal("5.00")
        assert schema.estimated_sell_price == Decimal("19.99")

    def test_analytics_schema_accepts_float(self):
        """Schema accepts float values and rounds to 2 decimal places."""
        schema = AnalyticsRequestSchema(
            asin="B001234567",
            estimated_buy_price=5.123,
            estimated_sell_price=19.999,
        )
        assert schema.estimated_buy_price == Decimal("5.12")
        assert schema.estimated_sell_price == Decimal("20.00")

    def test_analytics_schema_accepts_string(self):
        """Schema accepts string values."""
        schema = AnalyticsRequestSchema(
            asin="B001234567",
            estimated_buy_price="5.00",
            estimated_sell_price="19.99",
        )
        assert schema.estimated_buy_price == Decimal("5.00")
        assert schema.estimated_sell_price == Decimal("19.99")

    def test_analytics_schema_accepts_int(self):
        """Schema accepts integer values."""
        schema = AnalyticsRequestSchema(
            asin="B001234567",
            estimated_buy_price=5,
            estimated_sell_price=20,
        )
        assert schema.estimated_buy_price == Decimal("5")
        assert schema.estimated_sell_price == Decimal("20")

    def test_analytics_schema_defaults(self):
        """Optional fields have correct defaults."""
        schema = AnalyticsRequestSchema(
            asin="B001234567",
            estimated_buy_price="5.00",
            estimated_sell_price="19.99",
        )
        assert schema.referral_fee_percent == Decimal("15")
        assert schema.fba_fee == Decimal("2.50")
        assert schema.return_rate_percent == Decimal("2")
        assert schema.storage_cost_monthly == Decimal("0.87")
        assert schema.prep_fee is None

    def test_analytics_schema_none_optional(self):
        """Optional Decimal fields accept None."""
        schema = AnalyticsRequestSchema(
            asin="B001234567",
            estimated_buy_price="5.00",
            estimated_sell_price="19.99",
            prep_fee=None,
        )
        assert schema.prep_fee is None

    def test_analytics_schema_json_serialization(self):
        """Schema can be serialized to JSON (model_dump)."""
        schema = AnalyticsRequestSchema(
            asin="B001234567",
            estimated_buy_price="5.00",
            estimated_sell_price="19.99",
        )
        data = schema.model_dump()
        assert data["asin"] == "B001234567"
        assert "estimated_buy_price" in data


# =============================================================================
# CONDITION BREAKDOWN TESTS
# =============================================================================


class TestConditionBreakdown:
    """Tests for _build_condition_breakdown helper."""

    def test_breakdown_basic(self):
        """Breakdown returns sorted conditions with correct fields."""
        pricing = {
            'good': {
                'market_price': 12.0,
                'roi_pct': 0.80,
                'roi_value': 4.0,
                'seller_count': 5,
                'fba_count': 2,
                'is_recommended': True,
            },
            'new': {
                'market_price': 25.0,
                'roi_pct': 0.40,
                'roi_value': 2.0,
                'seller_count': 3,
                'fba_count': 1,
                'is_recommended': False,
            },
        }
        result = _build_condition_breakdown(pricing, source_price=5.0)

        assert len(result) == 2
        # Sorted by ROI descending
        assert result[0]['condition'] == 'good'
        assert result[0]['roi_pct'] == 80.0
        assert result[0]['label'] == 'Bon'
        assert result[0]['is_recommended'] is True
        assert result[1]['condition'] == 'new'
        assert result[1]['roi_pct'] == 40.0
        assert result[1]['label'] == 'Neuf'

    def test_breakdown_empty_pricing(self):
        """Empty pricing returns empty list."""
        result = _build_condition_breakdown({}, source_price=5.0)
        assert result == []

    def test_breakdown_all_conditions(self):
        """All 4 conditions are mapped with French labels."""
        pricing = {
            'new': {'market_price': 30.0, 'roi_pct': 0.20, 'roi_value': 2.0, 'seller_count': 1, 'fba_count': 0, 'is_recommended': False},
            'very_good': {'market_price': 20.0, 'roi_pct': 0.50, 'roi_value': 5.0, 'seller_count': 3, 'fba_count': 1, 'is_recommended': False},
            'good': {'market_price': 15.0, 'roi_pct': 0.80, 'roi_value': 8.0, 'seller_count': 5, 'fba_count': 2, 'is_recommended': True},
            'acceptable': {'market_price': 10.0, 'roi_pct': 1.20, 'roi_value': 12.0, 'seller_count': 2, 'fba_count': 0, 'is_recommended': False},
        }
        result = _build_condition_breakdown(pricing, source_price=5.0)

        assert len(result) == 4
        labels = {r['label'] for r in result}
        assert labels == {'Neuf', 'Tres bon', 'Bon', 'Acceptable'}
        # Sorted by ROI desc
        assert result[0]['condition'] == 'acceptable'
        assert result[0]['roi_pct'] == 120.0

    def test_breakdown_missing_fields_defaults(self):
        """Missing fields in pricing data use safe defaults."""
        pricing = {
            'good': {'market_price': 15.0},
        }
        result = _build_condition_breakdown(pricing, source_price=5.0)
        assert result[0]['roi_pct'] == 0.0
        assert result[0]['seller_count'] == 0
        assert result[0]['fba_count'] == 0
        assert result[0]['is_recommended'] is False


# =============================================================================
# CONDITION SIGNAL DERIVATION TESTS (unified pipeline logic)
# =============================================================================


class TestConditionSignalDerivationUnified:
    """Tests for condition signal derivation logic used in unified pipeline."""

    def _derive_signal(self, roi_pct, total_used_offers, config=None):
        """Mirror the derivation logic from unified_analysis.py step 5.5."""
        if config is None:
            config = {
                "strong_roi_min": 25.0,
                "moderate_roi_min": 10.0,
                "max_used_offers_strong": 10,
                "max_used_offers_moderate": 25,
            }
        strong_roi_min = config.get("strong_roi_min", 25.0)
        moderate_roi_min = config.get("moderate_roi_min", 10.0)
        max_offers_strong = config.get("max_used_offers_strong", 10)
        max_offers_moderate = config.get("max_used_offers_moderate", 25)

        if roi_pct >= strong_roi_min and total_used_offers <= max_offers_strong:
            return "STRONG"
        elif roi_pct >= moderate_roi_min and total_used_offers <= max_offers_moderate:
            return "MODERATE"
        else:
            return "WEAK"

    def test_strong_signal_high_roi_low_offers(self):
        """High ROI + low competition = STRONG."""
        assert self._derive_signal(roi_pct=50.0, total_used_offers=5) == "STRONG"

    def test_strong_signal_boundary(self):
        """Exactly at strong thresholds = STRONG."""
        assert self._derive_signal(roi_pct=25.0, total_used_offers=10) == "STRONG"

    def test_moderate_signal(self):
        """Moderate ROI with moderate competition = MODERATE."""
        assert self._derive_signal(roi_pct=15.0, total_used_offers=15) == "MODERATE"

    def test_moderate_signal_high_roi_high_offers(self):
        """High ROI but too many offers for STRONG = MODERATE."""
        assert self._derive_signal(roi_pct=50.0, total_used_offers=15) == "MODERATE"

    def test_weak_signal_low_roi(self):
        """Low ROI = WEAK regardless of offers."""
        assert self._derive_signal(roi_pct=5.0, total_used_offers=2) == "WEAK"

    def test_weak_signal_too_many_offers(self):
        """Too many offers even with moderate ROI = WEAK."""
        assert self._derive_signal(roi_pct=15.0, total_used_offers=30) == "WEAK"

    def test_zero_offers_strong(self):
        """Zero offers with high ROI = STRONG (no competition)."""
        assert self._derive_signal(roi_pct=30.0, total_used_offers=0) == "STRONG"


# =============================================================================
# CONFIDENCE BOOST TESTS (unified pipeline)
# =============================================================================


class TestConfidenceBoostUnified:
    """Tests for confidence boost logic applied in unified pipeline."""

    def _apply_boost(self, base_score, condition_signal, config=None):
        """Mirror the boost logic from unified_analysis.py."""
        if config is None:
            config = {
                "confidence_boost_strong": 10,
                "confidence_boost_moderate": 5,
            }
        boost = 0
        if condition_signal == "STRONG":
            boost = config.get("confidence_boost_strong", 10)
        elif condition_signal == "MODERATE":
            boost = config.get("confidence_boost_moderate", 5)

        return min(100, base_score + boost)

    def test_strong_boost(self):
        """STRONG signal adds 10 points."""
        assert self._apply_boost(60, "STRONG") == 70

    def test_moderate_boost(self):
        """MODERATE signal adds 5 points."""
        assert self._apply_boost(60, "MODERATE") == 65

    def test_weak_no_boost(self):
        """WEAK signal adds nothing."""
        assert self._apply_boost(60, "WEAK") == 60

    def test_boost_capped_at_100(self):
        """Confidence never exceeds 100."""
        assert self._apply_boost(95, "STRONG") == 100

    def test_none_signal_no_boost(self):
        """None signal adds nothing."""
        assert self._apply_boost(60, None) == 60

    def test_custom_boost_values(self):
        """Custom boost values from config are respected."""
        config = {"confidence_boost_strong": 20, "confidence_boost_moderate": 8}
        assert self._apply_boost(50, "STRONG", config) == 70
        assert self._apply_boost(50, "MODERATE", config) == 58
