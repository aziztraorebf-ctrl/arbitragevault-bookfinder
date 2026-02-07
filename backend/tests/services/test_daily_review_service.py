"""
Unit tests for Daily Review Service - Product Classification Engine.

TDD: These tests are written FIRST before implementation.
Tests the classification of AutoSourcing picks into 5 categories:
STABLE, JACKPOT, REVENANT, FLUKE, REJECT.
"""
import pytest
from datetime import datetime, timezone, timedelta

from app.services.daily_review_service import classify_product, generate_daily_review, Classification


# =============================================================================
# HELPERS
# =============================================================================


def make_pick(roi: float, bsr: int, amazon_on_listing: bool) -> dict:
    """Create a minimal product pick dict for testing."""
    return {
        "asin": "0593655036",
        "title": "Test Book",
        "roi_percentage": roi,
        "bsr": bsr,
        "amazon_on_listing": amazon_on_listing,
        "current_price": 15.99,
        "buy_price": 8.99,
    }


def make_history(hours_ago: float) -> dict:
    """Create a history entry with tracked_at set to N hours ago."""
    return {
        "tracked_at": datetime.now(timezone.utc) - timedelta(hours=hours_ago),
        "bsr": 300,
        "price": 15.99,
    }


# =============================================================================
# REJECT TESTS
# =============================================================================


class TestClassifyProduct:
    """Tests for classify_product function."""

    def test_reject_amazon_seller(self):
        """Amazon on listing -> REJECT regardless of other metrics."""
        product = make_pick(roi=30.0, bsr=500, amazon_on_listing=True)
        result = classify_product(product, history=[])
        assert result == Classification.REJECT

    def test_reject_negative_roi(self):
        """Negative ROI -> REJECT."""
        product = make_pick(roi=-5.0, bsr=500, amazon_on_listing=False)
        result = classify_product(product, history=[])
        assert result == Classification.REJECT

    def test_reject_bad_bsr(self):
        """BSR <= 0 -> REJECT even with good history."""
        product = make_pick(roi=30.0, bsr=-1, amazon_on_listing=False)
        result = classify_product(product, history=[make_history(hours_ago=48)])
        assert result == Classification.REJECT

    def test_reject_zero_bsr(self):
        """BSR == 0 -> REJECT."""
        product = make_pick(roi=30.0, bsr=0, amazon_on_listing=False)
        result = classify_product(product, history=[make_history(hours_ago=12)])
        assert result == Classification.REJECT

    # =============================================================================
    # FLUKE TESTS
    # =============================================================================

    def test_fluke_no_history(self):
        """No history at all -> FLUKE (never seen before)."""
        product = make_pick(roi=30.0, bsr=500, amazon_on_listing=False)
        result = classify_product(product, history=[])
        assert result == Classification.FLUKE

    def test_fluke_empty_history_list(self):
        """Explicit empty list -> FLUKE."""
        product = make_pick(roi=50.0, bsr=1000, amazon_on_listing=False)
        result = classify_product(product, history=[])
        assert result == Classification.FLUKE

    # =============================================================================
    # JACKPOT TESTS
    # =============================================================================

    def test_jackpot_high_roi(self):
        """ROI > 80% with history -> JACKPOT."""
        product = make_pick(roi=95.0, bsr=200, amazon_on_listing=False)
        result = classify_product(product, history=[make_history(hours_ago=48)])
        assert result == Classification.JACKPOT

    def test_jackpot_roi_boundary_80(self):
        """ROI = 80.1% -> JACKPOT (just above threshold)."""
        product = make_pick(roi=80.1, bsr=300, amazon_on_listing=False)
        result = classify_product(product, history=[make_history(hours_ago=12)])
        assert result == Classification.JACKPOT

    def test_jackpot_roi_exactly_80_not_jackpot(self):
        """ROI = 80.0% exactly -> NOT JACKPOT (threshold is strictly >80)."""
        product = make_pick(roi=80.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=12), make_history(hours_ago=36)]
        result = classify_product(product, history=history)
        assert result != Classification.JACKPOT

    def test_jackpot_no_history_becomes_fluke(self):
        """ROI > 80% but no history -> FLUKE (FLUKE takes priority over JACKPOT)."""
        product = make_pick(roi=95.0, bsr=200, amazon_on_listing=False)
        result = classify_product(product, history=[])
        assert result == Classification.FLUKE

    # =============================================================================
    # REVENANT TESTS
    # =============================================================================

    def test_revenant_returns_after_gap(self):
        """Last seen 72h ago, reappears -> REVENANT."""
        product = make_pick(roi=35.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=72)]
        result = classify_product(product, history=history)
        assert result == Classification.REVENANT

    def test_revenant_gap_under_24h(self):
        """Last seen 23h ago -> NOT REVENANT (need gap > 24h)."""
        product = make_pick(roi=35.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=23)]
        result = classify_product(product, history=history)
        assert result != Classification.REVENANT

    def test_revenant_gap_just_over_24h(self):
        """Last seen 25h ago -> REVENANT."""
        product = make_pick(roi=35.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=25)]
        result = classify_product(product, history=history)
        assert result == Classification.REVENANT

    # =============================================================================
    # STABLE TESTS
    # =============================================================================

    def test_stable_consistent(self):
        """2+ sightings, ROI 15-80%, BSR > 0, no Amazon -> STABLE."""
        product = make_pick(roi=40.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=12), make_history(hours_ago=36)]
        result = classify_product(product, history=history)
        assert result == Classification.STABLE

    def test_stable_roi_boundary_15(self):
        """ROI = 15.0% exactly -> STABLE (inclusive boundary)."""
        product = make_pick(roi=15.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=12), make_history(hours_ago=36)]
        result = classify_product(product, history=history)
        assert result == Classification.STABLE

    def test_stable_roi_below_15_not_stable(self):
        """ROI = 14.9% -> NOT STABLE (below min ROI threshold)."""
        product = make_pick(roi=14.9, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=12), make_history(hours_ago=36)]
        result = classify_product(product, history=history)
        assert result != Classification.STABLE

    def test_stable_only_one_sighting_not_stable(self):
        """Only 1 sighting -> NOT STABLE (need 2+)."""
        product = make_pick(roi=40.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=12)]
        result = classify_product(product, history=history)
        assert result != Classification.STABLE

    def test_low_roi_with_history_not_stable(self):
        """ROI in [0, 15) with 2+ sightings -> FLUKE (below STABLE_MIN_ROI)."""
        product = make_pick(roi=5.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=12), make_history(hours_ago=36)]
        result = classify_product(product, history=history)
        assert result == Classification.FLUKE

    # =============================================================================
    # PRIORITY ORDER TESTS
    # =============================================================================

    def test_reject_takes_priority_over_jackpot(self):
        """Amazon on listing with ROI > 80% -> REJECT (not JACKPOT)."""
        product = make_pick(roi=95.0, bsr=200, amazon_on_listing=True)
        result = classify_product(product, history=[make_history(hours_ago=48)])
        assert result == Classification.REJECT

    def test_reject_takes_priority_over_stable(self):
        """Negative ROI with good history -> REJECT (not STABLE)."""
        product = make_pick(roi=-10.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=12), make_history(hours_ago=36)]
        result = classify_product(product, history=history)
        assert result == Classification.REJECT

    def test_jackpot_takes_priority_over_revenant(self):
        """ROI > 80% + gap > 24h -> JACKPOT (not REVENANT)."""
        product = make_pick(roi=95.0, bsr=200, amazon_on_listing=False)
        history = [make_history(hours_ago=72)]
        result = classify_product(product, history=history)
        assert result == Classification.JACKPOT

    # =============================================================================
    # EDGE CASES / DEFAULT FALLBACK
    # =============================================================================

    def test_default_fluke_low_roi_single_sighting(self):
        """Single recent sighting with low ROI -> FLUKE (default fallback)."""
        product = make_pick(roi=10.0, bsr=300, amazon_on_listing=False)
        history = [make_history(hours_ago=6)]
        result = classify_product(product, history=history)
        assert result == Classification.FLUKE

    def test_missing_roi_field_defaults_safely(self):
        """Product dict without roi_percentage -> defaults to 0.0, no crash.
        ROI 0.0 is not < 0, so not REJECT. With no history -> FLUKE."""
        product = {
            "asin": "0593655036",
            "title": "Test Book",
            "bsr": 500,
            "amazon_on_listing": False,
            "current_price": 15.99,
            "buy_price": 8.99,
        }
        result = classify_product(product, history=[])
        assert result == Classification.FLUKE

    def test_missing_bsr_field_defaults_safely(self):
        """Product dict without bsr -> should not crash."""
        product = {
            "asin": "0593655036",
            "title": "Test Book",
            "roi_percentage": 30.0,
            "amazon_on_listing": False,
            "current_price": 15.99,
            "buy_price": 8.99,
        }
        result = classify_product(product, history=[])
        assert result == Classification.REJECT


# =============================================================================
# DAILY REVIEW GENERATOR TESTS
# =============================================================================


class TestGenerateDailyReview:
    """Tests for generate_daily_review function."""

    def test_empty_picks_returns_empty_review(self):
        """Empty picks list returns zeroed-out review."""
        review = generate_daily_review(picks=[], history_map={})
        assert review["total"] == 0
        assert review["counts"] == {
            "STABLE": 0,
            "JACKPOT": 0,
            "REVENANT": 0,
            "FLUKE": 0,
            "REJECT": 0,
        }
        assert review["top_opportunities"] == []

    def test_mixed_picks_classified_correctly(self):
        """Mixed picks get correct classification counts."""
        picks = [
            make_pick(roi=40.0, bsr=300, amazon_on_listing=False),
            make_pick(roi=95.0, bsr=200, amazon_on_listing=False),
            make_pick(roi=30.0, bsr=500, amazon_on_listing=True),
        ]
        picks[0]["asin"] = "ASIN001"
        picks[1]["asin"] = "ASIN002"
        picks[2]["asin"] = "ASIN003"
        history_map = {
            "ASIN001": [make_history(12), make_history(36)],
            "ASIN002": [make_history(48)],
            "ASIN003": [],
        }
        review = generate_daily_review(picks=picks, history_map=history_map)
        assert review["total"] == 3
        assert review["counts"]["STABLE"] == 1
        assert review["counts"]["JACKPOT"] == 1
        assert review["counts"]["REJECT"] == 1

    def test_top_opportunities_sorted_by_roi(self):
        """Top opportunities are sorted by ROI descending."""
        picks = [
            make_pick(roi=30.0, bsr=300, amazon_on_listing=False),
            make_pick(roi=60.0, bsr=200, amazon_on_listing=False),
            make_pick(roi=45.0, bsr=250, amazon_on_listing=False),
        ]
        for i, p in enumerate(picks):
            p["asin"] = f"ASIN{i:03d}"
        history_map = {
            p["asin"]: [make_history(12), make_history(36)] for p in picks
        }
        review = generate_daily_review(picks=picks, history_map=history_map)
        rois = [opp["roi_percentage"] for opp in review["top_opportunities"]]
        assert rois == sorted(rois, reverse=True)

    def test_top_opportunities_max_3(self):
        """Top opportunities list is capped at 3 items."""
        picks = [
            make_pick(roi=30 + i, bsr=300, amazon_on_listing=False)
            for i in range(10)
        ]
        for i, p in enumerate(picks):
            p["asin"] = f"ASIN{i:03d}"
        history_map = {
            p["asin"]: [make_history(12), make_history(36)] for p in picks
        }
        review = generate_daily_review(picks=picks, history_map=history_map)
        assert len(review["top_opportunities"]) <= 3

    def test_summary_text_generated(self):
        """Summary text is a non-empty string."""
        picks = [make_pick(roi=40.0, bsr=300, amazon_on_listing=False)]
        picks[0]["asin"] = "ASIN001"
        history_map = {"ASIN001": [make_history(12), make_history(36)]}
        review = generate_daily_review(picks=picks, history_map=history_map)
        assert isinstance(review["summary"], str)
        assert len(review["summary"]) > 0

    def test_review_date_present(self):
        """Review includes a review_date in YYYY-MM-DD format."""
        review = generate_daily_review(picks=[], history_map={})
        assert "review_date" in review
        assert len(review["review_date"]) == 10  # YYYY-MM-DD format

    def test_top_opportunities_excludes_reject_and_fluke(self):
        """Top opportunities never include REJECT or FLUKE products."""
        picks = [
            make_pick(roi=90.0, bsr=300, amazon_on_listing=True),   # REJECT
            make_pick(roi=50.0, bsr=200, amazon_on_listing=False),  # FLUKE (no history)
            make_pick(roi=40.0, bsr=300, amazon_on_listing=False),  # STABLE (with history)
        ]
        picks[0]["asin"] = "REJECT1"
        picks[1]["asin"] = "FLUKE1"
        picks[2]["asin"] = "STABLE1"
        history_map = {
            "REJECT1": [],
            "FLUKE1": [],
            "STABLE1": [make_history(12), make_history(36)],
        }
        review = generate_daily_review(picks=picks, history_map=history_map)
        classifications = [o["classification"] for o in review["top_opportunities"]]
        assert "REJECT" not in classifications
        assert "FLUKE" not in classifications
