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
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.models.webhook_config import WebhookConfig
from app.schemas.webhook import WebhookPayload

logger = logging.getLogger(__name__)

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
    data: Dict[str, Any] = {}

    for attr in ("id", "status", "query_name", "total_results", "user_id"):
        val = getattr(job, attr, None)
        if val is not None:
            data[attr] = str(val) if attr in ("id", "user_id") else val

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
    db: AsyncSession,
    job: Any,
    event: str = EVENT_JOB_COMPLETED,
) -> None:
    """
    Dispatch webhook notifications for a completed AutoSourcing job.

    Fire-and-forget: this function NEVER raises. All errors are caught
    and logged so that webhook failures never block job completion.

    Args:
        db: Async database session for querying webhook configs.
        job: AutoSourcing job object with id, status, query_name, etc.
        event: Event type string (default: autosourcing.job.completed).
    """
    try:
        # --- Global kill switch: empty secret means webhooks disabled ---
        settings = get_settings()
        if not settings.webhook_secret:
            logger.debug("Webhook dispatch skipped: WEBHOOK_SECRET is empty")
            return

        # --- Query active webhook configs for this user ---
        user_id = getattr(job, "user_id", None)
        stmt = select(WebhookConfig).where(WebhookConfig.active.is_(True))
        if user_id is not None:
            stmt = stmt.where(WebhookConfig.user_id == str(user_id))

        result = await db.execute(stmt)
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

    except Exception:
        logger.exception("Webhook dispatch failed")
