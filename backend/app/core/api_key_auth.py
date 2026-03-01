"""API key authentication for external automation (N8N, agents).

This module provides API key generation, verification, and a dual-auth
dependency that accepts both X-API-Key headers and Firebase Bearer tokens.
"""

import hashlib
import secrets
from typing import Optional, Tuple

import structlog
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import CurrentUser, get_current_user, http_bearer
from .db import get_db_session
from .logging import set_user_context
from .security import scopes_for_role

logger = structlog.get_logger()

# API key prefix for identification
API_KEY_PREFIX = "avk_"
API_KEY_RANDOM_LENGTH = 32


def generate_api_key() -> Tuple[str, str, str]:
    """Generate a new API key.

    Returns:
        Tuple of (raw_key, key_hash, key_prefix).
        - raw_key: The full key to return to the user (shown once).
        - key_hash: SHA-256 hex digest for storage.
        - key_prefix: First 8 characters for identification.
    """
    random_part = secrets.token_urlsafe(API_KEY_RANDOM_LENGTH)
    raw_key = f"{API_KEY_PREFIX}{random_part}"

    # Truncate to exactly 36 characters
    raw_key = raw_key[:36]

    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:8]

    return raw_key, key_hash, key_prefix


def hash_api_key(raw_key: str) -> str:
    """Hash an API key using SHA-256.

    Args:
        raw_key: The raw API key string.

    Returns:
        SHA-256 hex digest of the key.
    """
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def verify_api_key(
    api_key: str,
    db: AsyncSession,
) -> Optional[CurrentUser]:
    """Verify an API key and return the associated user.

    Args:
        api_key: The raw API key from the request header.
        db: Database session.

    Returns:
        CurrentUser if the key is valid, None otherwise.
    """
    from ..models.api_key import APIKey
    from datetime import datetime, timezone

    key_hash = hash_api_key(api_key)

    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,  # noqa: E712
        )
    )
    api_key_record = result.scalar_one_or_none()

    if not api_key_record:
        logger.warning("API key not found or inactive", key_prefix=api_key[:8])
        return None

    # Check expiration
    if api_key_record.expires_at and api_key_record.expires_at < datetime.now(timezone.utc):
        logger.warning("API key expired", key_prefix=api_key[:8])
        return None

    # Update last used timestamp
    api_key_record.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    # Load the associated user
    from ..models.user import User

    user_result = await db.execute(
        select(User).where(User.id == api_key_record.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user or not user.is_active:
        logger.warning("API key owner not found or inactive", key_prefix=api_key[:8])
        return None

    # Build scopes from the API key's scopes (not the user's role scopes)
    api_key_scopes = set(api_key_record.scopes) if api_key_record.scopes else set()

    set_user_context(user.id)

    logger.debug(
        "User authenticated via API key",
        user_id=user.id,
        key_prefix=api_key[:8],
        scopes=list(api_key_scopes),
    )

    return CurrentUser(
        id=user.id,
        email=user.email,
        role=user.role,
        scopes=api_key_scopes,
        is_active=user.is_active,
    )


async def get_api_or_firebase_user(
    x_api_key: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db_session),
) -> CurrentUser:
    """Dual-auth dependency: accepts X-API-Key header or Firebase Bearer token.

    Tries API key first (if provided), then falls back to Firebase Bearer token.
    At least one authentication method must succeed.
    """
    # Try API key authentication first
    if x_api_key:
        user = await verify_api_key(x_api_key, db)
        if user:
            return user

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
        )

    # Fall back to Firebase Bearer token
    if credentials:
        return await get_current_user(credentials, db)

    # No authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide X-API-Key header or Bearer token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
