"""Authentication service with business logic."""

from datetime import timedelta
from typing import Tuple

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidTokenError,
    WeakPasswordError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.core.settings import get_settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest

logger = structlog.get_logger()


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.settings = get_settings()

    async def register(self, data: RegisterRequest) -> Tuple[User, str, str]:
        """
        Register a new user.

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            DuplicateEmailError: If email already exists
            WeakPasswordError: If password doesn't meet requirements
        """
        # Validate password strength
        password_errors = validate_password_strength(data.password)
        if password_errors:
            raise WeakPasswordError(password_errors)

        # Hash password
        password_hash = hash_password(data.password)

        # Create user (raises DuplicateEmailError if email exists)
        user = await self.user_repo.create_user(
            email=data.email,
            password_hash=password_hash,
            first_name=data.first_name,
            last_name=data.last_name,
            role="sourcer",
            is_active=True,
            is_verified=False,
        )

        # Generate tokens
        access_token, refresh_token = self._generate_tokens(user)

        logger.info("User registered successfully", user_id=user.id, email=user.email)

        return user, access_token, refresh_token

    async def login(self, email: str, password: str) -> Tuple[User, str, str]:
        """
        Authenticate user with email/password.

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            InvalidCredentialsError: If credentials are wrong
            AccountLockedError: If account is locked
            AccountInactiveError: If account is deactivated
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)

        if not user:
            logger.warning("Login attempt for non-existent email", email=email)
            raise InvalidCredentialsError()

        # Check if account is locked
        if user.is_locked:
            logger.warning("Login attempt on locked account", user_id=user.id)
            raise AccountLockedError(
                locked_until=user.locked_until.isoformat() if user.locked_until else None
            )

        # Check if account is active
        if not user.is_active:
            logger.warning("Login attempt on inactive account", user_id=user.id)
            raise AccountInactiveError()

        # Verify password
        if not verify_password(password, user.password_hash):
            # Update failed attempts
            await self.user_repo.update_login_tracking(user.id, success=False)
            logger.warning("Invalid password attempt", user_id=user.id)
            raise InvalidCredentialsError()

        # Success - update login tracking
        await self.user_repo.update_login_tracking(user.id, success=True)

        # Generate tokens
        access_token, refresh_token = self._generate_tokens(user)

        logger.info("User logged in successfully", user_id=user.id)

        return user, access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate new access token from refresh token.

        Returns:
            New access token

        Raises:
            InvalidTokenError: If refresh token is invalid
        """
        # Decode refresh token
        payload = decode_token(refresh_token)

        if not payload:
            raise InvalidTokenError("Invalid refresh token")

        # Verify token type
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")

        # Get user
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Invalid token payload")

        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise InvalidTokenError("User not found")

        if not user.is_active:
            raise AccountInactiveError()

        # Generate new access token
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )

        logger.info("Access token refreshed", user_id=user.id)

        return access_token

    async def get_current_user(self, user_id: str) -> User:
        """
        Get user by ID for /me endpoint.

        Raises:
            InvalidTokenError: If user not found or inactive
        """
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise InvalidTokenError("User not found")

        if not user.is_active:
            raise AccountInactiveError()

        return user

    def _generate_tokens(self, user: User) -> Tuple[str, str]:
        """Generate access and refresh tokens for user."""
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
        }

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data={"sub": user.id})

        return access_token, refresh_token
