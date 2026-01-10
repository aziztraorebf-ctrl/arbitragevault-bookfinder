"""Authentication endpoints for Firebase-based auth."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.core.exceptions import (
    AccountInactiveError,
    DuplicateEmailError,
    InvalidTokenError,
)
from app.schemas.auth import (
    UserResponse,
)
from app.services.firebase_auth_service import FirebaseAuthService

logger = structlog.get_logger()
router = APIRouter()


async def get_firebase_token(authorization: str = Header(...)) -> str:
    """Extract Firebase ID token from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization[7:]  # Remove "Bearer " prefix


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(get_firebase_token),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get current authenticated user information.

    Verifies Firebase ID token and returns user data.
    Creates user in database if first login.
    """
    try:
        auth_service = FirebaseAuthService(db)
        user, _ = await auth_service.verify_token_and_get_user(token)

        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
        )

    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AccountInactiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )


@router.post("/sync", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def sync_user(
    token: str = Depends(get_firebase_token),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Sync user from Firebase to our database.

    Called after successful Firebase registration/login.
    Creates user if not exists, returns existing user otherwise.
    """
    try:
        auth_service = FirebaseAuthService(db)
        user, decoded_token = await auth_service.verify_token_and_get_user(token)

        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
        )

    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except AccountInactiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )


@router.post("/logout")
async def logout():
    """
    Logout endpoint (placeholder).

    With Firebase, logout is handled client-side by:
    1. Calling firebase.auth().signOut()
    2. Clearing stored tokens

    This endpoint exists for API completeness.
    """
    return {"message": "Logged out successfully"}


@router.get("/verify")
async def verify_token(
    token: str = Depends(get_firebase_token),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Verify Firebase token without creating/updating user.

    Useful for checking if a token is valid.
    """
    try:
        auth_service = FirebaseAuthService(db)
        user, decoded_token = await auth_service.verify_token_and_get_user(token)

        return {
            "valid": True,
            "user_id": user.id,
            "firebase_uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
        }

    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AccountInactiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
