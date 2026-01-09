"""Authentication endpoints."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.db import get_db_session
from app.core.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidTokenError,
    WeakPasswordError,
)
from app.core.settings import get_settings
from app.schemas.auth import (
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

logger = structlog.get_logger()
router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Register a new user account.

    Returns JWT tokens on successful registration.
    """
    try:
        auth_service = AuthService(db)
        user, access_token, refresh_token = await auth_service.register(data)

        settings = get_settings()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.details,
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Login with email/password using OAuth2 password flow.

    Note: OAuth2 spec uses 'username' field, but we treat it as email.
    """
    try:
        auth_service = AuthService(db)
        user, access_token, refresh_token = await auth_service.login(
            email=form_data.username,  # OAuth2 uses 'username'
            password=form_data.password,
        )

        settings = get_settings()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=e.message,
        )
    except AccountInactiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Refresh access token using refresh token.
    """
    try:
        auth_service = AuthService(db)
        access_token = await auth_service.refresh_access_token(data.refresh_token)

        settings = get_settings()

        return TokenResponse(
            access_token=access_token,
            refresh_token=data.refresh_token,  # Return same refresh token
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
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


@router.post("/logout")
async def logout():
    """
    Logout user.

    Note: With JWT, logout is primarily client-side (delete tokens).
    Server-side token blacklisting can be added later if needed.
    """
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get current authenticated user information.
    """
    try:
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(current_user.id)

        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AccountInactiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
