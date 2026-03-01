"""Admin CRUD endpoints for API key management."""

from typing import List
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, require_admin
from app.core.api_key_auth import generate_api_key
from app.core.db import get_db_session
from app.models.api_key import APIKey
from app.schemas.api_key import (
    APIKeyCreatedResponse,
    APIKeyDeleteResponse,
    APIKeyResponse,
    CreateAPIKeyRequest,
    UpdateAPIKeyRequest,
)

logger = structlog.get_logger()
router = APIRouter()


@router.post("", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new API key. The raw key is returned only once."""
    raw_key, key_hash, key_prefix = generate_api_key()

    api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=request.name,
        scopes=request.scopes or ["daily_review:read", "autosourcing:read"],
        expires_at=request.expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info("API key created", key_prefix=key_prefix, user_id=current_user.id)

    return APIKeyCreatedResponse(
        id=str(api_key.id),
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        key=raw_key,
    )


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """List all API keys (without raw key values)."""
    result = await db.execute(
        select(APIKey).order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()

    return [
        APIKeyResponse(
            id=str(key.id),
            name=key.name,
            key_prefix=key.key_prefix,
            scopes=key.scopes,
            is_active=key.is_active,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            created_at=key.created_at,
        )
        for key in keys
    ]


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: UUID,
    request: UpdateAPIKeyRequest,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Update an API key's name, scopes, or active status."""
    result = await db.execute(select(APIKey).where(APIKey.id == str(key_id)))
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    if request.name is not None:
        api_key.name = request.name
    if request.scopes is not None:
        api_key.scopes = request.scopes
    if request.is_active is not None:
        api_key.is_active = request.is_active

    await db.commit()
    await db.refresh(api_key)

    logger.info("API key updated", key_prefix=api_key.key_prefix, user_id=current_user.id)

    return APIKeyResponse(
        id=str(api_key.id),
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.delete("/{key_id}", response_model=APIKeyDeleteResponse)
async def delete_api_key(
    key_id: UUID,
    current_user: CurrentUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Deactivate (soft-delete) an API key."""
    result = await db.execute(select(APIKey).where(APIKey.id == str(key_id)))
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    api_key.is_active = False
    await db.commit()

    logger.info("API key deleted", key_prefix=api_key.key_prefix, user_id=current_user.id)

    return APIKeyDeleteResponse(
        message="API key deactivated",
        id=str(key_id),
    )
