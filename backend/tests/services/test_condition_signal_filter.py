"""Tests for condition_signal WEAK rejection with configurable threshold."""
from datetime import datetime, timedelta, timezone

from app.services.daily_review_service import classify_product, Classification


def _make_history(count: int, now: datetime):
    """Create N history entries within the last 24h."""
    return [
        {"tracked_at": now - timedelta(hours=i + 1), "bsr": 50000, "price": 30.0}
        for i in range(count)
    ]


class TestConditionSignalFilter:

    def test_weak_condition_low_roi_rejected_with_config(self):
        """WEAK + ROI < 20% + reject_weak=True -> REJECT."""
        now = datetime.now(timezone.utc)
        product = {
            "asin": "B000TEST01",
            "roi_percentage": 15.0,
            "bsr": 50000,
            "amazon_on_listing": False,
            "condition_signal": "WEAK",
        }
        history = _make_history(3, now)
        config = {"reject_weak": True, "reject_weak_roi_threshold": 20.0}

        result = classify_product(product, history, now=now, config=config)
        assert result == Classification.REJECT

    def test_weak_condition_high_roi_not_rejected(self):
        """WEAK + ROI >= 20% + reject_weak=True -> still STABLE."""
        now = datetime.now(timezone.utc)
        product = {
            "asin": "B000TEST02",
            "roi_percentage": 25.0,
            "bsr": 50000,
            "amazon_on_listing": False,
            "condition_signal": "WEAK",
        }
        history = _make_history(3, now)
        config = {"reject_weak": True, "reject_weak_roi_threshold": 20.0}

        result = classify_product(product, history, now=now, config=config)
        assert result == Classification.STABLE

    def test_strong_condition_always_stable(self):
        """STRONG condition + decent ROI -> STABLE regardless of config."""
        now = datetime.now(timezone.utc)
        product = {
            "asin": "B000TEST03",
            "roi_percentage": 20.0,
            "bsr": 50000,
            "amazon_on_listing": False,
            "condition_signal": "STRONG",
        }
        history = _make_history(3, now)
        config = {"reject_weak": True, "reject_weak_roi_threshold": 20.0}

        result = classify_product(product, history, now=now, config=config)
        assert result == Classification.STABLE

    def test_weak_condition_uses_hardcoded_5_without_config(self):
        """Without reject_weak=True, fallback to hardcoded 5% threshold."""
        now = datetime.now(timezone.utc)
        product = {
            "asin": "B000TEST04",
            "roi_percentage": 4.0,
            "bsr": 50000,
            "amazon_on_listing": False,
            "condition_signal": "WEAK",
        }
        history = _make_history(3, now)

        result = classify_product(product, history, now=now)
        assert result == Classification.REJECT

    def test_weak_condition_passes_at_6pct_without_config(self):
        """Without config, WEAK + ROI=6% (above 5% hardcoded) -> STABLE."""
        now = datetime.now(timezone.utc)
        product = {
            "asin": "B000TEST05",
            "roi_percentage": 16.0,
            "bsr": 50000,
            "amazon_on_listing": False,
            "condition_signal": "WEAK",
        }
        history = _make_history(3, now)

        result = classify_product(product, history, now=now)
        assert result == Classification.STABLE

    def test_no_condition_signal_not_affected(self):
        """Products without condition_signal are not affected by reject_weak."""
        now = datetime.now(timezone.utc)
        product = {
            "asin": "B000TEST06",
            "roi_percentage": 15.0,
            "bsr": 50000,
            "amazon_on_listing": False,
        }
        history = _make_history(3, now)
        config = {"reject_weak": True, "reject_weak_roi_threshold": 20.0}

        result = classify_product(product, history, now=now, config=config)
        assert result == Classification.STABLE
