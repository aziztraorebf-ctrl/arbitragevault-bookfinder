"""
Notification Service - Fire-and-forget SMS and email notifications.

Sends SMS via Textbelt and email via Resend when AutoSourcing jobs
find stable picks. Skips silently when config is missing.

Key design decisions:
- NEVER raises exceptions (fire-and-forget pattern)
- Skips silently when API keys or recipients are not configured
- All errors logged via standard logging, never propagated
"""
import logging
from typing import Optional

import httpx

from app.core.settings import get_settings

logger = logging.getLogger(__name__)

# --- Constants ---
TEXTBELT_URL = "https://textbelt.com/text"
RESEND_URL = "https://api.resend.com/emails"
HTTP_TIMEOUT = 10.0


async def send_sms(message: str) -> None:
    """
    Send an SMS via the Textbelt API.

    Fire-and-forget: this function NEVER raises. Skips silently
    when TEXTBELT_API_KEY or NOTIFICATION_PHONE is not configured.

    Args:
        message: The text message body to send.
    """
    try:
        settings = get_settings()
        if not settings.textbelt_api_key or not settings.notification_phone:
            logger.debug("SMS skipped: TEXTBELT_API_KEY or NOTIFICATION_PHONE not set")
            return

        payload = {
            "phone": settings.notification_phone,
            "message": message,
            "key": settings.textbelt_api_key,
        }

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(TEXTBELT_URL, json=payload)
            logger.info(
                "SMS sent: status_code=%d phone=%s",
                response.status_code,
                settings.notification_phone,
            )
    except Exception:
        logger.exception("SMS send failed")


async def send_email(subject: str, html_body: str) -> None:
    """
    Send an email via the Resend API.

    Fire-and-forget: this function NEVER raises. Skips silently
    when RESEND_API_KEY or NOTIFICATION_EMAIL is not configured.

    Args:
        subject: Email subject line.
        html_body: HTML content for the email body.
    """
    try:
        settings = get_settings()
        if not settings.resend_api_key or not settings.notification_email:
            logger.debug("Email skipped: RESEND_API_KEY or NOTIFICATION_EMAIL not set")
            return

        headers = {
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": "ArbitrageVault <notifications@arbitragevault.com>",
            "to": [settings.notification_email],
            "subject": subject,
            "html": html_body,
        }

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(RESEND_URL, json=payload, headers=headers)
            logger.info(
                "Email sent: status_code=%d to=%s",
                response.status_code,
                settings.notification_email,
            )
    except Exception:
        logger.exception("Email send failed")


async def notify_picks_found(
    stable_count: int,
    job_id: str,
    picks_summary: Optional[str] = None,
) -> None:
    """
    Orchestrate SMS and email notifications for found picks.

    Fire-and-forget: this function NEVER raises. Sends both SMS
    and email with details about the stable picks found.

    Args:
        stable_count: Number of stable (GOOD/EXCELLENT) picks found.
        job_id: The AutoSourcing job ID.
        picks_summary: Optional HTML summary of picks for the email body.
    """
    try:
        sms_message = (
            f"ArbitrageVault: {stable_count} stable pick(s) found in job {job_id}."
        )
        await send_sms(sms_message)

        subject = f"ArbitrageVault: {stable_count} stable pick(s) found"
        html_body = picks_summary or (
            f"<h2>{stable_count} stable pick(s) found</h2>"
            f"<p>Job ID: <strong>{job_id}</strong></p>"
        )
        await send_email(subject, html_body)
    except Exception:
        logger.exception("notify_picks_found failed")
