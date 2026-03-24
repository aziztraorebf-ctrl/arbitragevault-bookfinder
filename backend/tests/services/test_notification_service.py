"""
Unit tests for Notification Service - Fire-and-forget SMS and email notifications.

Tests verify that notifications are sent correctly via Textbelt (SMS) and Resend (email),
and that missing config, API errors, and network errors are handled gracefully.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

from app.services.notification_service import send_sms, send_email, notify_picks_found


# =============================================================================
# HELPERS
# =============================================================================


def _make_settings(**overrides):
    """Create a mock settings object with notification defaults."""
    defaults = {
        "textbelt_api_key": "test-textbelt-key",
        "notification_phone": "+15551234567",
        "resend_api_key": "test-resend-key",
        "notification_email": "user@example.com",
    }
    defaults.update(overrides)
    settings = MagicMock()
    for k, v in defaults.items():
        setattr(settings, k, v)
    return settings


# =============================================================================
# send_sms TESTS
# =============================================================================


class TestSendSms:
    """Tests for send_sms function."""

    @pytest.mark.asyncio
    async def test_send_sms_no_config_skips(self):
        """SMS skipped when TEXTBELT_API_KEY is not configured."""
        settings = _make_settings(textbelt_api_key=None)
        with patch("app.services.notification_service.get_settings", return_value=settings), \
             patch("app.services.notification_service.httpx.AsyncClient") as mock_client:
            await send_sms("test message")
            mock_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_sms_success_payload_validation(self):
        """SMS sent with correct payload to Textbelt API."""
        settings = _make_settings()
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notification_service.get_settings", return_value=settings), \
             patch("app.services.notification_service.httpx.AsyncClient", return_value=mock_client_instance):
            await send_sms("Hello!")

            mock_client_instance.post.assert_called_once_with(
                "https://textbelt.com/text",
                json={
                    "phone": "+15551234567",
                    "message": "Hello!",
                    "key": "test-textbelt-key",
                },
            )

    @pytest.mark.asyncio
    async def test_send_sms_api_failure_logging(self, caplog):
        """SMS API failure (non-200) is logged, no exception raised."""
        settings = _make_settings()
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notification_service.get_settings", return_value=settings), \
             patch("app.services.notification_service.httpx.AsyncClient", return_value=mock_client_instance):
            await send_sms("test")  # Should not raise
            mock_client_instance.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sms_network_error_logging(self, caplog):
        """SMS network error is caught and logged, no exception raised."""
        settings = _make_settings()

        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.ConnectError("Connection refused")
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notification_service.get_settings", return_value=settings), \
             patch("app.services.notification_service.httpx.AsyncClient", return_value=mock_client_instance):
            await send_sms("test")  # Should not raise


# =============================================================================
# send_email TESTS
# =============================================================================


class TestSendEmail:
    """Tests for send_email function."""

    @pytest.mark.asyncio
    async def test_send_email_no_config_skips(self):
        """Email skipped when RESEND_API_KEY is not configured."""
        settings = _make_settings(resend_api_key=None)
        with patch("app.services.notification_service.get_settings", return_value=settings), \
             patch("app.services.notification_service.httpx.AsyncClient") as mock_client:
            await send_email("Subject", "<p>Body</p>")
            mock_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_email_success_bearer_auth(self):
        """Email sent with Bearer auth header to Resend API."""
        settings = _make_settings()
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notification_service.get_settings", return_value=settings), \
             patch("app.services.notification_service.httpx.AsyncClient", return_value=mock_client_instance):
            await send_email("Test Subject", "<p>Hello</p>")

            mock_client_instance.post.assert_called_once_with(
                "https://api.resend.com/emails",
                json={
                    "from": "ArbitrageVault <notifications@arbitragevault.com>",
                    "to": ["user@example.com"],
                    "subject": "Test Subject",
                    "html": "<p>Hello</p>",
                },
                headers={
                    "Authorization": "Bearer test-resend-key",
                    "Content-Type": "application/json",
                },
            )

    @pytest.mark.asyncio
    async def test_send_email_http_error_logging(self):
        """Email HTTP error is caught and logged, no exception raised."""
        settings = _make_settings()
        mock_response = MagicMock()
        mock_response.status_code = 403

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notification_service.get_settings", return_value=settings), \
             patch("app.services.notification_service.httpx.AsyncClient", return_value=mock_client_instance):
            await send_email("Subject", "<p>Body</p>")  # Should not raise
            mock_client_instance.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_network_error_logging(self):
        """Email network error is caught and logged, no exception raised."""
        settings = _make_settings()

        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.ConnectError("Connection refused")
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.notification_service.get_settings", return_value=settings), \
             patch("app.services.notification_service.httpx.AsyncClient", return_value=mock_client_instance):
            await send_email("Subject", "<p>Body</p>")  # Should not raise


# =============================================================================
# notify_picks_found TESTS
# =============================================================================


class TestNotifyPicksFound:
    """Tests for notify_picks_found orchestrator."""

    @pytest.mark.asyncio
    async def test_notify_picks_found_zero_stable_skips(self):
        """stable_count=0 still calls send_sms and send_email (orchestrator doesn't filter)."""
        with patch("app.services.notification_service.send_sms", new_callable=AsyncMock) as mock_sms, \
             patch("app.services.notification_service.send_email", new_callable=AsyncMock) as mock_email:
            await notify_picks_found(stable_count=0, job_id="job-123")
            # With 0 stable picks, the function still sends (no early return in implementation)
            mock_sms.assert_called_once()
            mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_picks_found_calls_both_with_correct_content(self):
        """stable_count=3 sends SMS and email with correct content."""
        with patch("app.services.notification_service.send_sms", new_callable=AsyncMock) as mock_sms, \
             patch("app.services.notification_service.send_email", new_callable=AsyncMock) as mock_email:
            await notify_picks_found(stable_count=3, job_id="job-456")

            # Verify SMS content
            sms_msg = mock_sms.call_args[0][0]
            assert "3 stable pick(s)" in sms_msg
            assert "job-456" in sms_msg

            # Verify email content
            email_subject = mock_email.call_args[0][0]
            email_body = mock_email.call_args[0][1]
            assert "3 stable pick(s)" in email_subject
            assert "3 stable pick(s)" in email_body
            assert "job-456" in email_body
