"""Authentication endpoints."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.auth import CurrentUser, get_current_user

logger = structlog.get_logger()
router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register():
    """
    Register a new user.

    This endpoint will be implemented in Cycle 1.3 with full authentication logic.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Registration endpoint not implemented yet (Phase 1, Cycle 1.3)",
    )


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login with email/password and get JWT tokens.

    This endpoint will be implemented in Cycle 1.3 with full authentication logic.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login endpoint not implemented yet (Phase 1, Cycle 1.3)",
    )


@router.post("/refresh")
async def refresh_token():
    """
    Refresh access token using refresh token.

    This endpoint will be implemented in Cycle 1.3 with full authentication logic.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh endpoint not implemented yet (Phase 1, Cycle 1.3)",
    )


@router.post("/logout")
async def logout():
    """
    Logout and invalidate refresh token.

    This endpoint will be implemented in Cycle 1.3 with full authentication logic.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Logout endpoint not implemented yet (Phase 1, Cycle 1.3)",
    )


@router.get("/me")
async def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current authenticated user information.

    This endpoint will be fully implemented in Cycle 1.3.
    For now, returns a placeholder to test the authentication dependency.
    """
    return {
        "message": "Authentication dependency works!",
        "note": "Full implementation in Cycle 1.3",
        "user_id": current_user.id if hasattr(current_user, "id") else None,
    }
