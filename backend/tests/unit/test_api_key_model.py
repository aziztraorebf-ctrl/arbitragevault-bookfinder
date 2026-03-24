"""
Tests for API Key model properties and methods.

Tests cover:
- Model properties (is_expired, is_valid)
- Model methods (revoke, update_last_used)
- String representation
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.api_key import APIKey


def _make_api_key(**overrides) -> APIKey:
    """Create an APIKey instance with sensible defaults."""
    defaults = {
        "id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "key_hash": "abc123hash",
        "key_prefix": "avk_test",
        "name": "Test Key",
        "scopes": ["read"],
        "is_active": True,
        "last_used_at": None,
        "expires_at": None,
    }
    defaults.update(overrides)
    return APIKey(**defaults)


class TestAPIKeyIsExpired:
    """Tests for APIKey.is_expired property."""

    def test_not_expired_when_no_expiry(self):
        """Key without expiration is never expired."""
        key = _make_api_key(expires_at=None)
        assert key.is_expired is False

    def test_not_expired_when_future_expiry(self):
        """Key with future expiration is not expired."""
        key = _make_api_key(expires_at=datetime.now(timezone.utc) + timedelta(days=30))
        assert key.is_expired is False

    def test_expired_when_past_expiry(self):
        """Key with past expiration is expired."""
        key = _make_api_key(expires_at=datetime.now(timezone.utc) - timedelta(days=1))
        assert key.is_expired is True


class TestAPIKeyIsValid:
    """Tests for APIKey.is_valid property."""

    def test_valid_when_active_and_not_expired(self):
        """Active key without expiration is valid."""
        key = _make_api_key(is_active=True, expires_at=None)
        assert key.is_valid is True

    def test_invalid_when_inactive(self):
        """Inactive key is not valid."""
        key = _make_api_key(is_active=False, expires_at=None)
        assert key.is_valid is False

    def test_invalid_when_expired(self):
        """Expired key is not valid."""
        key = _make_api_key(
            is_active=True,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        assert key.is_valid is False

    def test_invalid_when_inactive_and_expired(self):
        """Inactive and expired key is not valid."""
        key = _make_api_key(
            is_active=False,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        assert key.is_valid is False


class TestAPIKeyRevoke:
    """Tests for APIKey.revoke method."""

    def test_revoke_sets_inactive(self):
        """Revoking sets is_active to False."""
        key = _make_api_key(is_active=True)
        key.revoke()
        assert key.is_active is False

    def test_revoke_already_inactive(self):
        """Revoking already inactive key keeps it inactive."""
        key = _make_api_key(is_active=False)
        key.revoke()
        assert key.is_active is False


class TestAPIKeyUpdateLastUsed:
    """Tests for APIKey.update_last_used method."""

    def test_update_last_used_sets_timestamp(self):
        """update_last_used sets last_used_at to current time."""
        key = _make_api_key(last_used_at=None)
        before = datetime.now(timezone.utc)
        key.update_last_used()
        after = datetime.now(timezone.utc)

        assert key.last_used_at is not None
        assert before <= key.last_used_at <= after


class TestAPIKeyRepr:
    """Tests for APIKey.__repr__ method."""

    def test_repr_contains_key_info(self):
        """Repr includes id, name, and prefix."""
        key = _make_api_key(id="test-id", name="My Key", key_prefix="avk_abcd")
        result = repr(key)

        assert "test-id" in result
        assert "My Key" in result
        assert "avk_abcd" in result
