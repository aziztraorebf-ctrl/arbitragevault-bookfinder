"""
Webhook Service - Fire-and-forget webhook dispatch.

Sends HTTP POST notifications to configured webhook URLs when
AutoSourcing jobs complete. Uses HMAC-SHA256 for payload signing.

Key design decisions:
- NEVER raises exceptions (fire-and-forget pattern)
- Global kill switch via empty WEBHOOK_SECRET setting
- All errors logged via structlog, never propagated
"""
import hashlib
import hmac
import json
import structlog
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.models.webhook_config import WebhookConfig
from app.schemas.webhook import WebhookPayload

logger = structlog.get_logger()

# --- Constants ---
WEBHOOK_TIMEOUT_SECONDS = 10
EVENT_JOB_COMPLETED = "autosourcing.job.completed"


def _sign_payload(payload_bytes: bytes, secret: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload."""
    return hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()


def _build_payload(job: Any, event: str = EVENT_JOB_COMPLETED) -> WebhookPayload:
    """
    Build a WebhookPayload from an AutoSourcing job.

    Extracts relevant job data into a standardised payload format.
    Gracefully handles missing attributes.
    """
    job_id = str(getattr(job, "id", ""))
    # NOTE: AutoSourcingJob has no user_id column. This will always return "".
    # Kept for forward compatibility if user_id is added to the model later.
    user_id = str(getattr(job, "user_id", "")) if getattr(job, "user_id", None) else ""

    picks_count: int = getattr(job, "total_selected", 0) or 0

    picks = getattr(job, "picks", None) or []
    stable_count: int = sum(
        1 for p in picks
        if getattr(p, "overall_rating", None) in ("GOOD", "EXCELLENT")
    )

    duration_ms: Optional[int] = getattr(job, "duration_ms", None)
    duration_seconds: float = round(duration_ms / 1000.0, 1) if duration_ms else 0.0

    data: Dict[str, Any] = {
        "job_id": job_id,
        "user_id": user_id,
        "picks_count": picks_count,
        "stable_count": stable_count,
        "duration_seconds": duration_seconds,
    }

    return WebhookPayload(
        event=event,
        timestamp=datetime.now(timezone.utc).isoformat(),
        data=data,
    )


async def _deliver(
    url: str,
    payload_bytes: bytes,
    signature: str,
) -> None:
    """POST payload to a single webhook URL with timeout."""
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": f"sha256={signature}",
    }
    async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT_SECONDS) as client:
        response = await client.post(url, content=payload_bytes, headers=headers)
        logger.info(
            "Webhook delivered",
            extra={
                "url": url,
                "status_code": response.status_code,
            },
        )


async def dispatch_webhook(
    job: Any,
    event: str = EVENT_JOB_COMPLETED,
    db: Optional[AsyncSession] = None,
) -> None:
    """
    Dispatch webhook notifications for a completed AutoSourcing job.

    Fire-and-forget: this function NEVER raises. All errors are caught
    and logged so that webhook failures never block job completion.

    Creates its own DB session to avoid using a potentially expired
    caller session (since this runs as an asyncio.create_task).

    Args:
        job: AutoSourcing job object with id, status, query_name, etc.
        event: Event type string (default: autosourcing.job.completed).
        db: Optional DB session (ignored, kept for backwards compat).
    """
    try:
        # --- Global kill switch: empty secret means webhooks disabled ---
        settings = get_settings()
        if not settings.webhook_secret:
            logger.debug("Webhook dispatch skipped: WEBHOOK_SECRET is empty")
            return

        # --- Create a fresh DB session to avoid expired caller session ---
        from app.core.db import db_manager

        async with db_manager.session() as fresh_db:
            # --- Query active webhook configs for this user ---
            user_id = getattr(job, "user_id", None)
            stmt = select(WebhookConfig).where(WebhookConfig.active.is_(True))
            if user_id is not None:
                stmt = stmt.where(WebhookConfig.user_id == str(user_id))

            result = await fresh_db.execute(stmt)
            configs: List[WebhookConfig] = list(result.scalars().all())

        if not configs:
            logger.debug("No active webhook configs found")
            return

        # --- Build and sign payload ---
        payload = _build_payload(job, event=event)
        payload_bytes = json.dumps(
            payload.model_dump(), default=str
        ).encode("utf-8")
        signature = _sign_payload(payload_bytes, settings.webhook_secret)

        # --- Deliver to each config whose event_types match ---
        for config in configs:
            try:
                config_events = config.event_types or []
                if config_events and event not in config_events:
                    logger.debug(
                        "Skipping webhook config %s: event %s not in %s",
                        config.id,
                        event,
                        config_events,
                    )
                    continue

                await _deliver(config.url, payload_bytes, signature)
            except Exception:
                logger.exception(
                    "Webhook delivery failed for config %s (url=%s)",
                    config.id,
                    config.url,
                )

        # --- Send push notification for stable picks ---
        try:
            stable_count = payload.data.get("stable_count", 0) if hasattr(payload, "data") else 0
            if stable_count > 0:
                from app.services.notification_service import notify_picks_found

                picks = getattr(job, "picks", None) or []
                picks_data = [
                    {
                        "title": getattr(p, "title", ""),
                        "asin": getattr(p, "asin", ""),
                        "bsr": getattr(p, "bsr", 0),
                        "roi_percentage": getattr(p, "roi_percentage", 0.0),
                        # NOTE: classification is computed dynamically by daily_review_service,
                    # not stored on AutoSourcingPick. Will always return "" here.
                    "classification": getattr(p, "classification", ""),
                    }
                    for p in picks
                ][:10]
                await notify_picks_found(
                    stable_count=stable_count,
                    job_id=str(getattr(job, "id", "")),
                    picks_summary=picks_data,
                )
        except Exception:
            logger.exception("Push notification for stable picks failed")

    except Exception:
        logger.exception("Webhook dispatch failed")
