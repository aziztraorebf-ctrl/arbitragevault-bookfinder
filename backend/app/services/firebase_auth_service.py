"""Firebase Authentication Service."""

from typing import Optional, Tuple

import structlog
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError, RevokedIdTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AccountInactiveError,
    InvalidTokenError,
)
from app.core.firebase import verify_firebase_token
from app.models.user import User
from app.repositories.user_repository import UserRepository

logger = structlog.get_logger()


class FirebaseAuthService:
    """Service for Firebase-based authentication."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def verify_token_and_get_user(self, id_token: str) -> Tuple[User, dict]:
        """
        Verify Firebase ID token and get/create the corresponding user.

        This is the main entry point for authenticating requests.
        It handles:
        1. Token verification with Firebase
        2. User lookup/creation in our database
        3. Account status checks

        Args:
            id_token: Firebase ID token from client

        Returns:
            Tuple of (User, decoded_token_claims)

        Raises:
            InvalidTokenError: Token is invalid, expired, or revoked
            AccountInactiveError: User account is deactivated
        """
        # Verify token with Firebase
        try:
            decoded_token = verify_firebase_token(id_token)
        except ExpiredIdTokenError:
            raise InvalidTokenError("Token has expired")
        except RevokedIdTokenError:
            raise InvalidTokenError("Token has been revoked")
        except InvalidIdTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error verifying token", error=str(e))
            raise InvalidTokenError("Token verification failed")

        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")

        if not firebase_uid or not email:
            raise InvalidTokenError("Token missing required claims")

        # Get or create user
        user = await self._get_or_create_user(firebase_uid, email, decoded_token)

        # Check account status
        if not user.is_active:
            raise AccountInactiveError()

        # Update last login
        await self.user_repo.update_login_tracking(user.id, success=True)

        return user, decoded_token

    async def _get_or_create_user(
        self,
        firebase_uid: str,
        email: str,
        decoded_token: dict,
    ) -> User:
        """
        Get existing user or create new one from Firebase token.

        Handles these scenarios:
        1. User exists with firebase_uid -> return user
        2. User exists with email but no firebase_uid -> link and return
        3. User doesn't exist -> create new user
        """
        # Try to find by Firebase UID first
        user = await self.user_repo.get_by_firebase_uid(firebase_uid)
        if user:
            return user

        # Try to find by email (for linking existing accounts)
        user = await self.user_repo.get_by_email(email)
        if user:
            # Link Firebase UID to existing user
            user = await self.user_repo.link_firebase_uid(user.id, firebase_uid)
            logger.info(
                "Linked Firebase UID to existing user",
                user_id=user.id,
                firebase_uid=firebase_uid,
            )
            return user

        # Create new user
        # Extract name from Firebase token if available
        name = decoded_token.get("name", "")
        first_name = None
        last_name = None

        if name:
            parts = name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else None

        # Default role: "sourcer" - standard user role for book arbitrage platform
        # Admin role must be assigned manually by existing admin
        user = await self.user_repo.create_user_from_firebase(
            firebase_uid=firebase_uid,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role="sourcer",
        )

        logger.info(
            "Created new user from Firebase",
            user_id=user.id,
            firebase_uid=firebase_uid,
        )

        return user

    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """Get user by Firebase UID."""
        return await self.user_repo.get_by_firebase_uid(firebase_uid)

    async def sync_user_from_firebase(
        self,
        firebase_uid: str,
        email: str,
        name: Optional[str] = None,
    ) -> User:
        """
        Sync user data from Firebase (called after registration on frontend).

        This creates the user in our database if they don't exist.
        """
        user = await self.user_repo.get_by_firebase_uid(firebase_uid)
        if user:
            return user

        # Parse name
        first_name = None
        last_name = None
        if name:
            parts = name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else None

        return await self.user_repo.create_user_from_firebase(
            firebase_uid=firebase_uid,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
