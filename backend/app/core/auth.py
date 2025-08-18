"""Authentication and authorization dependencies."""

from typing import List, Optional, Set

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db_session
from .logging import set_user_context
from .security import decode_token, scopes_for_role, validate_scopes

logger = structlog.get_logger()

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scopes={
        "analyses:read": "Read analysis data",
        "analyses:write": "Create and update analyses",
        "analyses:delete": "Delete analyses",
        "batches:read": "Read batch data",
        "batches:write": "Create and update batches",
        "batches:delete": "Delete batches",
        "users:read": "Read user profiles",
        "users:write": "Update user profiles",
        "users:admin": "Administrative user operations",
    },
)


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
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db_session)
) -> CurrentUser:
    """Get current authenticated user from JWT token."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    payload = decode_token(token)
    if not payload:
        logger.warning("Invalid token provided")
        raise credentials_exception

    # Check token type
    token_type = payload.get("type")
    if token_type != "access":
        logger.warning("Invalid token type", token_type=token_type)
        raise credentials_exception

    # Extract user info
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Token missing user ID")
        raise credentials_exception

    # Import here to avoid circular imports
    from ..repositories.user_repo import UserRepository

    user_repo = UserRepository(db)

    # Get user from database
    user = await user_repo.get_by_id(user_id)
    if not user:
        logger.warning("User not found", user_id=user_id)
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
        )

    # Check if token is blacklisted (for access tokens, we check refresh token blacklist)
    # This is a simple approach - in production you might want separate blacklists

    # Get user scopes based on role
    user_scopes = scopes_for_role(user.role)

    # Set user context for logging
    set_user_context(user_id)

    logger.info("User authenticated", user_id=user_id, role=user.role)

    return CurrentUser(
        id=user.id,
        email=user.email,
        role=user.role,
        scopes=user_scopes,
        is_active=user.is_active,
    )


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
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[CurrentUser]:
    """Get current user if token is provided, otherwise return None."""
    if not token:
        return None

    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None
