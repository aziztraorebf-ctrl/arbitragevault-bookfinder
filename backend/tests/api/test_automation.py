"""Comprehensive tests for actionable buy list and webhook infrastructure."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.daily_review_service import (
    Classification,
    classify_product,
    generate_actionable_review,
    JACKPOT_ROI_THRESHOLD,
    STABLE_MIN_ROI,
    MIN_HISTORY_FOR_STABLE,
)
from app.schemas.webhook import WebhookConfigCreate, WebhookConfigResponse, WebhookPayload
from app.schemas.daily_review import ActionableBuyItem, ActionableBuyList


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2026, 2, 28, 12, 0, 0, tzinfo=timezone.utc)


def _make_pick(
    asin: str = "B000TEST01",
    roi: float = 30.0,
    bsr: int = 5000,
    amazon: bool = False,
    stability_score: float = 0.8,
    **kwargs: Any,
) -> Dict[str, Any]:
    return {
        "asin": asin,
        "title": f"Product {asin}",
        "roi_percentage": roi,
        "bsr": bsr,
        "amazon_on_listing": amazon,
        "current_price": 19.99,
        "buy_price": 12.99,
        "stability_score": stability_score,
        "confidence_score": 0.7,
        "velocity_score": 0.6,
        "overall_rating": 4.2,
        **kwargs,
    }


def _make_history(count: int = 3, hours_ago: float = 2.0) -> List[Dict[str, Any]]:
    """Create history entries recent enough to avoid REVENANT classification."""
    return [
        {
            "tracked_at": NOW - timedelta(hours=hours_ago + i),
            "bsr": 5000 + i * 100,
            "price": 19.99,
        }
        for i in range(count)
    ]


# ===========================================================================
# Unit Tests - classify_product
# ===========================================================================


class TestClassifyProduct:

    def test_reject_amazon_on_listing(self):
        pick = _make_pick(amazon=True, roi=30.0)
        assert classify_product(pick, _make_history(), now=NOW) == Classification.REJECT

    def test_reject_negative_roi(self):
        pick = _make_pick(roi=-5.0)
        assert classify_product(pick, _make_history(), now=NOW) == Classification.REJECT

    def test_reject_invalid_bsr(self):
        pick = _make_pick(bsr=0)
        assert classify_product(pick, _make_history(), now=NOW) == Classification.REJECT

    def test_fluke_no_history(self):
        pick = _make_pick(roi=30.0)
        assert classify_product(pick, [], now=NOW) == Classification.FLUKE

    def test_jackpot_high_roi(self):
        pick = _make_pick(roi=JACKPOT_ROI_THRESHOLD + 1)
        assert classify_product(pick, _make_history(), now=NOW) == Classification.JACKPOT

    def test_revenant_gap(self):
        pick = _make_pick(roi=30.0)
        old_history = [{"tracked_at": NOW - timedelta(hours=48), "bsr": 5000, "price": 19.99}]
        assert classify_product(pick, old_history, now=NOW) == Classification.REVENANT

    def test_stable_meets_criteria(self):
        pick = _make_pick(roi=30.0)
        history = _make_history(count=MIN_HISTORY_FOR_STABLE)
        assert classify_product(pick, history, now=NOW) == Classification.STABLE

    def test_fluke_insufficient_history(self):
        pick = _make_pick(roi=30.0)
        history = _make_history(count=1)
        assert classify_product(pick, history, now=NOW) == Classification.FLUKE


# ===========================================================================
# Unit Tests - generate_actionable_review
# ===========================================================================


class TestGenerateActionableReview:

    def test_stable_only(self):
        """Only STABLE picks returned; JACKPOT/FLUKE/REJECT/REVENANT excluded."""
        picks = [
            _make_pick(asin="STABLE1", roi=30.0),
            _make_pick(asin="JACKPOT1", roi=JACKPOT_ROI_THRESHOLD + 10),
            _make_pick(asin="REJECT1", roi=-5.0),
            _make_pick(asin="FLUKE1", roi=30.0),
        ]
        history_map = {
            "STABLE1": _make_history(count=3),
            "JACKPOT1": _make_history(count=3),
            "REJECT1": _make_history(count=3),
            # FLUKE1 has no history
        }
        result = generate_actionable_review(picks, history_map, now=NOW)
        asins = [item["asin"] for item in result["items"]]
        assert "STABLE1" in asins
        assert "JACKPOT1" not in asins
        assert "REJECT1" not in asins
        assert "FLUKE1" not in asins

    def test_sorting(self):
        """Results sorted by stability_score DESC, roi_percentage DESC."""
        picks = [
            _make_pick(asin="LOW", roi=20.0, stability_score=0.5),
            _make_pick(asin="HIGH", roi=40.0, stability_score=0.9),
            _make_pick(asin="MED", roi=50.0, stability_score=0.5),
        ]
        history_map = {
            "LOW": _make_history(),
            "HIGH": _make_history(),
            "MED": _make_history(),
        }
        result = generate_actionable_review(picks, history_map, now=NOW)
        asins = [item["asin"] for item in result["items"]]
        assert asins == ["HIGH", "MED", "LOW"]

    def test_min_roi_filter(self):
        """Picks below min_roi are excluded."""
        picks = [
            _make_pick(asin="GOOD", roi=25.0),
            _make_pick(asin="BAD", roi=10.0),
        ]
        history_map = {
            "GOOD": _make_history(),
            "BAD": _make_history(),
        }
        result = generate_actionable_review(picks, history_map, min_roi=20.0, now=NOW)
        asins = [item["asin"] for item in result["items"]]
        assert "GOOD" in asins
        assert "BAD" not in asins

    def test_max_results(self):
        """Result count does not exceed max_results."""
        picks = [_make_pick(asin=f"P{i}", roi=30.0 + i) for i in range(10)]
        history_map = {f"P{i}": _make_history() for i in range(10)}
        result = generate_actionable_review(picks, history_map, max_results=3, now=NOW)
        assert len(result["items"]) <= 3
        assert result["total_found"] == 10

    def test_empty_input(self):
        """Empty input returns empty items with total_found=0."""
        result = generate_actionable_review([], {}, now=NOW)
        assert result["items"] == []
        assert result["total_found"] == 0

    def test_min_roi_zero(self):
        """min_roi=0 returns all STABLE picks regardless of ROI."""
        picks = [_make_pick(asin="LOW_ROI", roi=STABLE_MIN_ROI)]
        history_map = {"LOW_ROI": _make_history()}
        result = generate_actionable_review(picks, history_map, min_roi=0, now=NOW)
        assert len(result["items"]) == 1

    def test_action_recommendation_is_buy(self):
        """Every item has action_recommendation = BUY."""
        picks = [_make_pick(roi=30.0)]
        history_map = {picks[0]["asin"]: _make_history()}
        result = generate_actionable_review(picks, history_map, now=NOW)
        for item in result["items"]:
            assert item["action_recommendation"] == "BUY"
            assert item["classification"] == "STABLE"

    def test_filters_applied_in_response(self):
        """Response includes filters_applied and generated_at."""
        result = generate_actionable_review([], {}, min_roi=25.0, max_results=5, now=NOW)
        assert result["filters_applied"]["min_roi"] == 25.0
        assert result["filters_applied"]["max_results"] == 5
        assert result["filters_applied"]["classification"] == "STABLE"
        assert result["generated_at"] == NOW.isoformat()


# ===========================================================================
# Unit Tests - Webhook Schemas
# ===========================================================================


class TestWebhookSchemas:

    def test_webhook_config_create_valid(self):
        config = WebhookConfigCreate(
            url="https://example.com/webhook",
            secret="my-secret",
            event_types=["autosourcing.job.completed"],
            active=True,
        )
        assert str(config.url) == "https://example.com/webhook"

    def test_webhook_config_create_invalid_url(self):
        with pytest.raises(Exception):
            WebhookConfigCreate(url="not-a-url")

    def test_webhook_config_create_defaults(self):
        config = WebhookConfigCreate(url="https://example.com/hook")
        assert config.secret == ""
        assert config.active is True
        assert "autosourcing.job.completed" in config.event_types

    def test_webhook_payload(self):
        payload = WebhookPayload(
            event="autosourcing.job.completed",
            timestamp="2026-02-28T12:00:00+00:00",
            data={"job_id": "123"},
        )
        assert payload.event == "autosourcing.job.completed"
        dumped = payload.model_dump()
        assert "data" in dumped

    def test_webhook_config_response_from_attributes(self):
        """WebhookConfigResponse can be created from dict (ORM compat)."""
        resp = WebhookConfigResponse(
            id="test-uuid-123",
            url="https://example.com/hook",
            secret="s",
            event_types=["autosourcing.job.completed"],
            active=True,
        )
        assert resp.id == "test-uuid-123"


# ===========================================================================
# Unit Tests - Webhook Dispatch
# ===========================================================================


class TestWebhookDispatch:

    @pytest.mark.asyncio
    async def test_dispatch_skipped_when_secret_empty(self):
        """No HTTP call made when WEBHOOK_SECRET is empty."""
        mock_settings = MagicMock()
        mock_settings.webhook_secret = ""

        with patch("app.services.webhook_service.get_settings", return_value=mock_settings):
            from app.services.webhook_service import dispatch_webhook

            mock_db = AsyncMock()
            mock_job = MagicMock()
            await dispatch_webhook(mock_db, mock_job)
            # db.execute should never be called when secret is empty
            mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_fire_and_forget(self):
        """Dispatch errors are caught, logged, never raised."""
        mock_settings = MagicMock()
        mock_settings.webhook_secret = "test-secret"

        with patch("app.services.webhook_service.get_settings", return_value=mock_settings):
            from app.services.webhook_service import dispatch_webhook

            mock_db = AsyncMock()
            mock_db.execute.side_effect = Exception("DB exploded")
            mock_job = MagicMock()
            mock_job.user_id = "user-123"
            # Should NOT raise
            await dispatch_webhook(mock_db, mock_job)

    @pytest.mark.asyncio
    async def test_dispatch_no_configs(self):
        """When no active configs found, dispatch returns silently."""
        mock_settings = MagicMock()
        mock_settings.webhook_secret = "test-secret"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with patch("app.services.webhook_service.get_settings", return_value=mock_settings):
            from app.services.webhook_service import dispatch_webhook

            mock_job = MagicMock()
            mock_job.user_id = "user-123"
            await dispatch_webhook(mock_db, mock_job)

    @pytest.mark.asyncio
    async def test_dispatch_delivers_to_config(self):
        """Webhook is delivered to matching config."""
        mock_settings = MagicMock()
        mock_settings.webhook_secret = "test-secret"

        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.url = "https://example.com/hook"
        mock_config.event_types = ["autosourcing.job.completed"]
        mock_config.active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_config]

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        mock_job = MagicMock()
        mock_job.user_id = "user-123"
        mock_job.id = "job-456"
        mock_job.status = "completed"
        mock_job.query_name = "test-query"
        mock_job.total_results = 10

        with (
            patch("app.services.webhook_service.get_settings", return_value=mock_settings),
            patch("app.services.webhook_service._deliver", new_callable=AsyncMock) as mock_deliver,
        ):
            from app.services.webhook_service import dispatch_webhook

            await dispatch_webhook(mock_db, mock_job)
            mock_deliver.assert_called_once()
            call_args = mock_deliver.call_args
            assert call_args[0][0] == "https://example.com/hook"

    @pytest.mark.asyncio
    async def test_dispatch_skips_non_matching_event(self):
        """Config with non-matching event_types is skipped."""
        mock_settings = MagicMock()
        mock_settings.webhook_secret = "test-secret"

        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.url = "https://example.com/hook"
        mock_config.event_types = ["some.other.event"]
        mock_config.active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_config]

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        mock_job = MagicMock()
        mock_job.user_id = "user-123"

        with (
            patch("app.services.webhook_service.get_settings", return_value=mock_settings),
            patch("app.services.webhook_service._deliver", new_callable=AsyncMock) as mock_deliver,
        ):
            from app.services.webhook_service import dispatch_webhook

            await dispatch_webhook(mock_db, mock_job)
            mock_deliver.assert_not_called()


# ===========================================================================
# Unit Tests - Webhook Service Helpers
# ===========================================================================


class TestWebhookHelpers:

    def test_sign_payload(self):
        from app.services.webhook_service import _sign_payload

        sig = _sign_payload(b'{"test": true}', "secret")
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA256 hex digest length

    def test_build_payload(self):
        from app.services.webhook_service import _build_payload

        mock_job = MagicMock()
        mock_job.id = "job-123"
        mock_job.status = "completed"
        mock_job.query_name = "test"
        mock_job.total_results = 5
        mock_job.user_id = "user-456"

        payload = _build_payload(mock_job)
        assert payload.event == "autosourcing.job.completed"
        assert payload.data["id"] == "job-123"
        assert payload.data["status"] == "completed"


# ===========================================================================
# Schema Tests - ActionableBuyList
# ===========================================================================


class TestActionableBuyListSchema:

    def test_actionable_buy_item(self):
        item = ActionableBuyItem(
            asin="B000TEST01",
            title="Test Product",
            current_price=19.99,
            roi_percentage=30.0,
            stability_score=0.8,
            confidence_score=0.7,
            velocity_score=0.6,
            bsr=5000,
            overall_rating=4.2,
        )
        assert item.classification == "STABLE"
        assert item.action_recommendation == "BUY"

    def test_actionable_buy_list(self):
        buy_list = ActionableBuyList(
            items=[],
            total_found=0,
            filters_applied={"min_roi": 15.0},
            generated_at="2026-02-28T12:00:00+00:00",
        )
        assert buy_list.total_found == 0
        assert buy_list.items == []
