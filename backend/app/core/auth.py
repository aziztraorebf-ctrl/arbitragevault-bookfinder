"""Authentication and authorization dependencies.

This module provides Firebase-based authentication for all protected endpoints.
Firebase ID tokens are verified and mapped to local user records.
"""

from typing import List, Optional, Set

import structlog
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db_session
from .logging import set_user_context
from .security import scopes_for_role, validate_scopes

logger = structlog.get_logger()

# HTTP Bearer scheme for Firebase tokens
http_bearer = HTTPBearer(auto_error=False)


class CurrentUser:
    """Current authenticated user information."""

    def __init__(
        self, id: str, email: str, role: str, scopes: Set[str], is_active: bool = True
    ):
        self.id = id
        self.email = email
        self.role = role
        self.scopes = scopes
        self.is_active = is_active

    def has_scope(self, scope: str) -> bool:
        """Check if user has specific scope."""
        return scope in self.scopes

    def has_any_scope(self, scopes: List[str]) -> bool:
        """Check if user has any of the specified scopes."""
        return any(scope in self.scopes for scope in scopes)

    def has_all_scopes(self, scopes: List[str]) -> bool:
        """Check if user has all specified scopes."""
        return all(scope in self.scopes for scope in scopes)

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role.upper() == "ADMIN"

    @property
    def is_sourcer(self) -> bool:
        """Check if user has sourcer role."""
        return self.role.upper() == "SOURCER"


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db_session),
) -> CurrentUser:
    """
    Get current authenticated user from Firebase ID token.

    This is the primary authentication dependency for all protected endpoints.
    It verifies the Firebase ID token and returns the corresponding local user.
    """
    from ..services.firebase_auth_service import FirebaseAuthService
    from ..core.exceptions import InvalidTokenError, AccountInactiveError

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Check if credentials provided
    if not credentials:
        logger.warning("No authorization credentials provided")
        raise credentials_exception

    token = credentials.credentials

    try:
        # Verify Firebase token and get/create user
        auth_service = FirebaseAuthService(db)
        user, decoded_token = await auth_service.verify_token_and_get_user(token)

        # Get user scopes based on role
        user_scopes = scopes_for_role(user.role)

        # Set user context for logging
        set_user_context(user.id)

        logger.debug("User authenticated via Firebase", user_id=user.id, role=user.role)

        return CurrentUser(
            id=user.id,
            email=user.email,
            role=user.role,
            scopes=user_scopes,
            is_active=user.is_active,
        )

    except InvalidTokenError as e:
        logger.warning("Invalid Firebase token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AccountInactiveError:
        logger.warning("Inactive account attempted access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    except Exception as e:
        logger.error("Unexpected authentication error", error=str(e), error_type=type(e).__name__)
        raise credentials_exception


def require_scopes(required_scopes: List[str]):
    """Dependency factory to require specific scopes."""

    def scope_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        required_set = set(required_scopes)

        if not validate_scopes(required_set, current_user.scopes):
            logger.warning(
                "Insufficient scopes",
                user_id=current_user.id,
                required_scopes=required_scopes,
                user_scopes=list(current_user.scopes),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scopes: {required_scopes}",
            )

        return current_user

    return scope_checker


def require_role(required_role: str):
    """Dependency factory to require specific role."""

    def role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role.upper() != required_role.upper():
            logger.warning(
                "Insufficient role",
                user_id=current_user.id,
                required_role=required_role,
                user_role=current_user.role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )

        return current_user

    return role_checker


# Common dependency shortcuts
require_admin = require_role("ADMIN")
require_sourcer = require_role("SOURCER")

# Scope-based dependencies
require_analyses_read = require_scopes(["analyses:read"])
require_analyses_write = require_scopes(["analyses:write"])
require_batches_read = require_scopes(["batches:read"])
require_batches_write = require_scopes(["batches:write"])
require_users_admin = require_scopes(["users:admin"])


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[CurrentUser]:
    """Get current user if token is provided, otherwise return None."""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_current_user_id(
    current_user: CurrentUser = Depends(get_current_user),
) -> str:
    """Get current authenticated user ID."""
    return current_user.id
