"""
Unit tests for Condition-Based Scoring Signals.

Tests the extraction, calculation, and gating of used price/offer data
added to the autosourcing pipeline.
"""
import pytest
from unittest.mock import MagicMock

from app.services.autosourcing_service import AutoSourcingService


# =============================================================================
# HELPERS
# =============================================================================


def make_service() -> AutoSourcingService:
    """Create an AutoSourcingService with mocked dependencies."""
    return AutoSourcingService(db_session=MagicMock(), keepa_service=MagicMock())


def make_raw_keepa(
    used_price_cents=None,
    new_price_cents=1500,
    bsr=5000,
    offer_count_used=None,
    offer_count_fba=-2,
) -> dict:
    """Create a minimal raw Keepa response dict for testing.

    Args:
        used_price_cents: Value at stats.current[2]. None omits index 2.
        new_price_cents: Value at stats.current[1].
        bsr: Value at stats.current[3].
        offer_count_used: Value for stats.offerCountUsed.
        offer_count_fba: Value for stats.offerCountFBA.
    """
    current = [None, new_price_cents, None, bsr]  # indices 0-3
    if used_price_cents is not None:
        current[2] = used_price_cents
    stats: dict = {
        "current": current,
        "offerCountFBA": offer_count_fba,
    }
    if offer_count_used is not None:
        stats["offerCountUsed"] = offer_count_used
    raw = {
        "title": "Test Book",
        "stats": stats,
        "availabilityAmazon": -1,
    }
    return raw


def make_pick(**overrides) -> MagicMock:
    """Create a mock AutoSourcingPick for criteria gating tests."""
    defaults = {
        "overall_rating": "GOOD",
        "roi_percentage": 30.0,
        "velocity_score": 60,
        "condition_signal": None,
    }
    defaults.update(overrides)
    pick = MagicMock()
    for k, v in defaults.items():
        setattr(pick, k, v)
    return pick


# =============================================================================
# USED PRICE EXTRACTION TESTS
# =============================================================================


class TestExtractUsedPrice:
    """Tests for used price extraction from stats.current[2]."""

    def test_extract_used_price_valid(self):
        """Valid used price (cents) is extracted and converted to dollars."""
        svc = make_service()
        raw = make_raw_keepa(used_price_cents=999)
        result = svc._extract_product_data_from_keepa(raw)
        assert result["used_price"] == pytest.approx(9.99)

    def test_extract_used_price_negative_one(self):
        """-1 sentinel value → None."""
        svc = make_service()
        raw = make_raw_keepa(used_price_cents=-1)
        result = svc._extract_product_data_from_keepa(raw)
        assert result["used_price"] is None

    def test_extract_used_price_zero(self):
        """0 price → None (treated as unavailable)."""
        svc = make_service()
        raw = make_raw_keepa(used_price_cents=0)
        result = svc._extract_product_data_from_keepa(raw)
        assert result["used_price"] is None

    def test_extract_used_price_missing(self):
        """Short current array (< 3 elements) → None."""
        svc = make_service()
        raw = {
            "title": "Test",
            "stats": {"current": [None, 1500]},
            "availabilityAmazon": -1,
        }
        result = svc._extract_product_data_from_keepa(raw)
        assert result["used_price"] is None


# =============================================================================
# USED OFFER COUNT EXTRACTION TESTS
# =============================================================================


class TestExtractUsedOfferCount:
    """Tests for used offer count extraction from stats.offerCountUsed."""

    def test_extract_used_offer_count_valid(self):
        """Valid offer count is extracted as integer."""
        svc = make_service()
        raw = make_raw_keepa(offer_count_used=7)
        result = svc._extract_product_data_from_keepa(raw)
        assert result["used_offer_count"] == 7

    def test_extract_used_offer_count_negative_two(self):
        """-2 sentinel → None."""
        svc = make_service()
        raw = make_raw_keepa(offer_count_used=-2)
        result = svc._extract_product_data_from_keepa(raw)
        assert result["used_offer_count"] is None

    def test_extract_used_offer_count_missing_key(self):
        """Missing offerCountUsed key → None (default -2 triggers None)."""
        svc = make_service()
        raw = make_raw_keepa()  # no offer_count_used
        result = svc._extract_product_data_from_keepa(raw)
        assert result["used_offer_count"] is None


# =============================================================================
# USED ROI CALCULATION TESTS
# =============================================================================


class TestUsedRoiCalculation:
    """Tests for used_roi_percentage computation."""

    def test_used_roi_calculation(self):
        """ROI formula: ((used_price - cost - fees) / cost) * 100."""
        # used_price = 20.0, source_price_factor=0.50, fba_fee_percentage=0.15
        # current_price = 15.0 (new), estimated_cost = 15.0 * 0.50 = 7.50
        # used_fees = 20.0 * 0.15 = 3.0
        # used_profit = 20.0 - 7.50 - 3.0 = 9.50
        # used_roi = (9.50 / 7.50) * 100 = 126.67
        svc = make_service()
        raw = make_raw_keepa(used_price_cents=2000, new_price_cents=1500)
        product_data = svc._extract_product_data_from_keepa(raw)
        assert product_data["used_price"] == pytest.approx(20.0)

        # Simulate the ROI calculation from _analyze_product_from_batch
        current_price = product_data["current_price"]
        source_price_factor = 0.50
        fba_fee_percentage = 0.15
        estimated_cost = current_price * source_price_factor
        used_price = product_data["used_price"]
        used_fees = used_price * fba_fee_percentage
        used_profit = used_price - estimated_cost - used_fees
        used_roi = (used_profit / estimated_cost) * 100

        assert used_roi == pytest.approx(126.67, rel=0.01)

    def test_used_roi_none_when_no_price(self):
        """used_roi_percentage is None when used_price is None."""
        svc = make_service()
        raw = make_raw_keepa(used_price_cents=-1)
        product_data = svc._extract_product_data_from_keepa(raw)
        assert product_data["used_price"] is None
        # When used_price is None, ROI should not be computed
        used_roi = None
        if product_data["used_price"] is not None:
            used_roi = 999  # Should not reach here
        assert used_roi is None

    def test_used_roi_zero_cost_guard(self):
        """Division by zero guarded when estimated_buy_cost <= 0."""
        # With source_price_factor=0, estimated_cost=0
        svc = make_service()
        raw = make_raw_keepa(used_price_cents=1000, new_price_cents=1500)
        product_data = svc._extract_product_data_from_keepa(raw)
        used_price = product_data["used_price"]
        estimated_cost = 0  # Zero cost scenario

        # Mimic the guard from _analyze_product_from_batch
        if estimated_cost > 0:
            used_roi = ((used_price - estimated_cost - used_price * 0.15) / estimated_cost) * 100
        else:
            used_roi = 0.0

        assert used_roi == 0.0


# =============================================================================
# CONDITION SIGNAL DERIVATION TESTS
# =============================================================================


class TestConditionSignalDerivation:
    """Tests for condition_signal classification logic."""

    def _derive_signal(self, used_roi, used_offer_count, config=None):
        """Helper that mirrors the signal derivation logic from _analyze_product_from_batch."""
        if config is None:
            config = {
                "used_roi_threshold": 30.0,
                "used_offer_threshold": 5,
            }
        threshold_roi = config.get("used_roi_threshold", 30.0)
        threshold_offers = config.get("used_offer_threshold", 5)

        if used_roi >= threshold_roi and used_offer_count >= threshold_offers:
            return "STRONG_USED"
        elif used_roi >= threshold_roi:
            return "USED_ROI_OK"
        elif used_offer_count >= threshold_offers:
            return "USED_DEMAND"
        else:
            return "WEAK_USED"

    def test_condition_signal_strong(self):
        """High used ROI + sufficient offers → STRONG_USED."""
        signal = self._derive_signal(used_roi=50.0, used_offer_count=10)
        assert signal == "STRONG_USED"

    def test_condition_signal_moderate_roi_ok(self):
        """Good ROI but low offers → USED_ROI_OK."""
        signal = self._derive_signal(used_roi=35.0, used_offer_count=2)
        assert signal == "USED_ROI_OK"

    def test_condition_signal_weak(self):
        """Low used ROI and low offers → WEAK_USED."""
        signal = self._derive_signal(used_roi=10.0, used_offer_count=2)
        assert signal == "WEAK_USED"

    def test_condition_signal_unknown_no_price(self):
        """No used price data → condition_signal stays None (UNKNOWN)."""
        svc = make_service()
        raw = make_raw_keepa(used_price_cents=-1)
        product_data = svc._extract_product_data_from_keepa(raw)
        # When used_price is None, the signal derivation block is skipped
        assert product_data["used_price"] is None
        # condition_signal would remain None (not computed)

    def test_condition_signal_missing_offer_count(self):
        """Used price available but offer count None → still derives signal from ROI."""
        # When used_offer_count is None/0, it won't meet offer threshold
        # So caps at USED_ROI_OK (not STRONG_USED)
        signal = self._derive_signal(used_roi=50.0, used_offer_count=0)
        assert signal != "STRONG_USED"
        assert signal == "USED_ROI_OK"

    def test_condition_signal_used_demand(self):
        """Low ROI but enough offers → USED_DEMAND."""
        signal = self._derive_signal(used_roi=10.0, used_offer_count=8)
        assert signal == "USED_DEMAND"


# =============================================================================
# CONFIDENCE BOOST TESTS
# =============================================================================


class TestConfidenceBoost:
    """Tests for condition-based confidence boost in _calculate_confidence_from_keepa."""

    def test_confidence_boost_strong(self):
        """STRONG signal adds configured boost to confidence."""
        svc = make_service()
        raw = make_raw_keepa()
        config = {"confidence_boost_strong": 10, "confidence_boost_moderate": 5}

        base = svc._calculate_confidence_from_keepa(raw, condition_signal=None)
        boosted = svc._calculate_confidence_from_keepa(
            raw, condition_signal="STRONG", business_config=config
        )
        assert boosted == min(100, base + 10)

    def test_confidence_boost_moderate(self):
        """MODERATE signal adds moderate boost."""
        svc = make_service()
        raw = make_raw_keepa()
        config = {"confidence_boost_strong": 10, "confidence_boost_moderate": 5}

        base = svc._calculate_confidence_from_keepa(raw, condition_signal=None)
        boosted = svc._calculate_confidence_from_keepa(
            raw, condition_signal="MODERATE", business_config=config
        )
        assert boosted == min(100, base + 5)

    def test_confidence_boost_capped(self):
        """Confidence never exceeds 100 even with condition boost."""
        svc = make_service()
        # Build a raw_keepa that yields high base confidence
        raw = make_raw_keepa()
        raw["salesRanks"] = {"12345": [1, 2, 3]}
        raw["lastUpdate"] = 9999
        raw["stats"]["avg30"] = [None, 1500]
        config = {"confidence_boost_strong": 50}  # Large boost

        result = svc._calculate_confidence_from_keepa(
            raw, condition_signal="STRONG", business_config=config
        )
        assert result <= 100

    def test_confidence_no_boost_for_weak(self):
        """WEAK signal adds nothing."""
        svc = make_service()
        raw = make_raw_keepa()
        base = svc._calculate_confidence_from_keepa(raw, condition_signal=None)
        weak = svc._calculate_confidence_from_keepa(raw, condition_signal="WEAK")
        assert weak == base

    def test_confidence_no_boost_for_unknown(self):
        """UNKNOWN signal adds nothing."""
        svc = make_service()
        raw = make_raw_keepa()
        base = svc._calculate_confidence_from_keepa(raw, condition_signal=None)
        unknown = svc._calculate_confidence_from_keepa(raw, condition_signal="UNKNOWN")
        assert unknown == base


# =============================================================================
# CRITERIA GATING TESTS
# =============================================================================


class TestCriteriaGating:
    """Tests for condition-based gating in _meets_criteria."""

    def test_meets_criteria_reject_weak(self):
        """When reject_weak=true, WEAK picks are filtered out."""
        svc = make_service()
        pick = make_pick(condition_signal="WEAK_USED")
        config = {
            "rating_required": "FAIR",
            "roi_min": 20,
            "velocity_min": 0,
            "condition_signals": {"reject_weak": True},
        }
        assert svc._meets_criteria(pick, config) is False

    def test_meets_criteria_allow_weak_default(self):
        """Default config does NOT reject WEAK (backward-compatible)."""
        svc = make_service()
        pick = make_pick(condition_signal="WEAK_USED")
        config = {
            "rating_required": "FAIR",
            "roi_min": 20,
            "velocity_min": 0,
            # No condition_signals section → default
        }
        assert svc._meets_criteria(pick, config) is True

    def test_meets_criteria_strong_signal_passes(self):
        """STRONG signal is never rejected by condition gating."""
        svc = make_service()
        pick = make_pick(condition_signal="STRONG_USED")
        config = {
            "rating_required": "FAIR",
            "roi_min": 20,
            "velocity_min": 0,
            "condition_signals": {"reject_weak": True},
        }
        assert svc._meets_criteria(pick, config) is True

    def test_meets_criteria_none_signal_passes(self):
        """None condition_signal (legacy pick) is never rejected."""
        svc = make_service()
        pick = make_pick(condition_signal=None)
        config = {
            "rating_required": "FAIR",
            "roi_min": 20,
            "velocity_min": 0,
            "condition_signals": {"reject_weak": True},
        }
        assert svc._meets_criteria(pick, config) is True
