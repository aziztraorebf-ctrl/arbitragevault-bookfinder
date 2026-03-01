"""
Tests for API key authentication logic.

Tests cover:
- Key generation (format, uniqueness, hashing)
- Key hashing
- Key verification
- Dual-auth dependency
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_auth import (
    API_KEY_PREFIX,
    generate_api_key,
    hash_api_key,
    verify_api_key,
    get_api_or_firebase_user,
)


class TestGenerateAPIKey:
    """Tests for generate_api_key function."""

    def test_returns_three_tuple(self):
        """generate_api_key returns (raw_key, key_hash, key_prefix)."""
        result = generate_api_key()
        assert len(result) == 3

    def test_raw_key_starts_with_prefix(self):
        """Raw key starts with 'avk_'."""
        raw_key, _, _ = generate_api_key()
        assert raw_key.startswith(API_KEY_PREFIX)

    def test_raw_key_length(self):
        """Raw key is exactly 36 characters."""
        raw_key, _, _ = generate_api_key()
        assert len(raw_key) == 36

    def test_key_hash_is_sha256(self):
        """Key hash matches SHA-256 of raw key."""
        raw_key, key_hash, _ = generate_api_key()
        expected = hashlib.sha256(raw_key.encode()).hexdigest()
        assert key_hash == expected

    def test_key_prefix_is_first_8_chars(self):
        """Key prefix is first 8 characters of raw key."""
        raw_key, _, key_prefix = generate_api_key()
        assert key_prefix == raw_key[:8]

    def test_unique_keys(self):
        """Each call generates a unique key."""
        keys = {generate_api_key()[0] for _ in range(10)}
        assert len(keys) == 10


class TestHashAPIKey:
    """Tests for hash_api_key function."""

    def test_deterministic(self):
        """Same input produces same hash."""
        assert hash_api_key("test_key") == hash_api_key("test_key")

    def test_sha256_format(self):
        """Hash is a 64-character hex string (SHA-256)."""
        result = hash_api_key("test_key")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_different_keys_different_hashes(self):
        """Different keys produce different hashes."""
        assert hash_api_key("key_a") != hash_api_key("key_b")


class TestVerifyAPIKey:
    """Tests for verify_api_key function."""

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_key(self):
        """Returns None when key hash not found in database."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await verify_api_key("avk_unknown_key_here_padding", mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_expired_key(self):
        """Returns None when key is expired."""
        mock_api_key = MagicMock()
        mock_api_key.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        mock_api_key.is_active = True

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_key
        mock_db.execute.return_value = mock_result

        result = await verify_api_key("avk_expired_key_here_pad", mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_inactive_user(self):
        """Returns None when associated user is inactive."""
        mock_api_key = MagicMock()
        mock_api_key.expires_at = None
        mock_api_key.user_id = "user-123"
        mock_api_key.scopes = ["read"]

        mock_user = MagicMock()
        mock_user.is_active = False

        mock_db = AsyncMock(spec=AsyncSession)
        # First call returns api_key, second returns user
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = mock_api_key
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = mock_user
        mock_db.execute.side_effect = [mock_result1, mock_result2]

        with patch("app.core.api_key_auth.set_user_context"):
            result = await verify_api_key("avk_valid_key_here_padd", mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_current_user_for_valid_key(self):
        """Returns CurrentUser when key and user are valid."""
        mock_api_key = MagicMock()
        mock_api_key.expires_at = None
        mock_api_key.user_id = "user-123"
        mock_api_key.scopes = ["read", "write"]
        mock_api_key.last_used_at = None

        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.role = "admin"
        mock_user.is_active = True

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = mock_api_key
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = mock_user
        mock_db.execute.side_effect = [mock_result1, mock_result2]

        with patch("app.core.api_key_auth.set_user_context"):
            result = await verify_api_key("avk_valid_key_here_padd", mock_db)

        assert result is not None
        assert result.id == "user-123"
        assert result.email == "test@example.com"
        assert result.scopes == {"read", "write"}


class TestGetAPIOrFirebaseUser:
    """Tests for get_api_or_firebase_user dual-auth dependency."""

    @pytest.mark.asyncio
    async def test_raises_401_when_no_auth_provided(self):
        """Raises 401 when neither API key nor Bearer token provided."""
        from fastapi import HTTPException

        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await get_api_or_firebase_user(
                x_api_key=None, credentials=None, db=mock_db
            )
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_uses_api_key_when_provided(self):
        """Uses API key auth when X-API-Key header is provided."""
        from app.core.auth import CurrentUser

        mock_user = CurrentUser(
            id="u1", email="a@b.com", role="admin", scopes={"read"}, is_active=True
        )
        mock_db = AsyncMock(spec=AsyncSession)

        with patch("app.core.api_key_auth.verify_api_key", new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = mock_user
            result = await get_api_or_firebase_user(
                x_api_key="avk_somekey", credentials=None, db=mock_db
            )

        assert result.id == "u1"
        mock_verify.assert_called_once_with("avk_somekey", mock_db)

    @pytest.mark.asyncio
    async def test_raises_401_for_invalid_api_key(self):
        """Raises 401 when API key is invalid."""
        from fastapi import HTTPException

        mock_db = AsyncMock(spec=AsyncSession)

        with patch("app.core.api_key_auth.verify_api_key", new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = None
            with pytest.raises(HTTPException) as exc_info:
                await get_api_or_firebase_user(
                    x_api_key="avk_badkey", credentials=None, db=mock_db
                )
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_falls_back_to_firebase_when_no_api_key(self):
        """Falls back to Firebase auth when no API key provided."""
        from app.core.auth import CurrentUser

        mock_user = CurrentUser(
            id="u2", email="b@c.com", role="sourcer", scopes={"read"}, is_active=True
        )
        mock_creds = MagicMock()
        mock_db = AsyncMock(spec=AsyncSession)

        with patch("app.core.api_key_auth.get_current_user", new_callable=AsyncMock) as mock_fb:
            mock_fb.return_value = mock_user
            result = await get_api_or_firebase_user(
                x_api_key=None, credentials=mock_creds, db=mock_db
            )

        assert result.id == "u2"
