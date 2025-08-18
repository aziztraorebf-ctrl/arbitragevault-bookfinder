"""User repository for user-specific database operations."""

from datetime import datetime
from typing import List, Optional

import structlog
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

from .base_repo import BaseRepository

logger = structlog.get_logger()


class UserRepository(BaseRepository[User]):
    """Repository for user operations."""

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        try:
            result = await self.db.execute(
                select(User).where(User.email == email.lower())
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error("Failed to get user by email", email=email, error=str(e))
            raise

    async def create_user(
        self,
        email: str,
        password_hash: str,
        role: str = "SOURCER",
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_verified: bool = False,
    ) -> User:
        """Create a new user with validation."""
        try:
            # Check if user already exists
            existing_user = await self.get_by_email(email)
            if existing_user:
                raise ValueError(f"User with email {email} already exists")

            user = await self.create(
                email=email.lower(),
                password_hash=password_hash,
                role=role.upper(),
                first_name=first_name,
                last_name=last_name,
                is_verified=is_verified,
                password_changed_at=datetime.utcnow(),
            )

            logger.info(
                "User created successfully", user_id=user.id, email=email, role=role
            )
            return user

        except Exception as e:
            logger.error("Failed to create user", email=email, role=role, error=str(e))
            raise

    async def update_password(
        self, user_id: str, new_password_hash: str
    ) -> Optional[User]:
        """Update user password and password change timestamp."""
        try:
            user = await self.update(
                user_id,
                password_hash=new_password_hash,
                password_changed_at=datetime.utcnow(),
                failed_login_attempts=0,  # Reset failed attempts
                locked_until=None,  # Unlock account
            )

            if user:
                logger.info("Password updated successfully", user_id=user_id)

            return user

        except Exception as e:
            logger.error("Failed to update password", user_id=user_id, error=str(e))
            raise

    async def update_last_login(self, user_id: str) -> Optional[User]:
        """Update user's last login timestamp."""
        try:
            user = await self.update(user_id, last_login_at=datetime.utcnow())

            if user:
                logger.info("Last login updated", user_id=user_id)

            return user

        except Exception as e:
            logger.error("Failed to update last login", user_id=user_id, error=str(e))
            raise

    async def increment_failed_login(self, user_id: str) -> Optional[User]:
        """Increment failed login attempts for user."""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return None

            new_attempts = user.failed_login_attempts + 1
            locked_until = None

            # Lock account if too many failed attempts (5 attempts = 15 min lock)
            if new_attempts >= 5:
                locked_until = datetime.utcnow().replace(microsecond=0)
                locked_until = locked_until.replace(minute=locked_until.minute + 15)
                logger.warning(
                    "Account locked due to failed login attempts",
                    user_id=user_id,
                    attempts=new_attempts,
                    locked_until=locked_until,
                )

            updated_user = await self.update(
                user_id, failed_login_attempts=new_attempts, locked_until=locked_until
            )

            return updated_user

        except Exception as e:
            logger.error(
                "Failed to increment failed login attempts",
                user_id=user_id,
                error=str(e),
            )
            raise

    async def reset_failed_login_attempts(self, user_id: str) -> Optional[User]:
        """Reset failed login attempts and unlock account."""
        try:
            user = await self.update(
                user_id, failed_login_attempts=0, locked_until=None
            )

            if user:
                logger.info("Failed login attempts reset", user_id=user_id)

            return user

        except Exception as e:
            logger.error(
                "Failed to reset failed login attempts", user_id=user_id, error=str(e)
            )
            raise

    async def set_verification_token(
        self, user_id: str, token: str, expires_at: datetime
    ) -> Optional[User]:
        """Set email verification token."""
        try:
            user = await self.update(
                user_id,
                verification_token=token,
                verification_token_expires_at=expires_at,
            )

            if user:
                logger.info("Verification token set", user_id=user_id)

            return user

        except Exception as e:
            logger.error(
                "Failed to set verification token", user_id=user_id, error=str(e)
            )
            raise

    async def verify_user(self, user_id: str) -> Optional[User]:
        """Mark user as verified and clear verification token."""
        try:
            user = await self.update(
                user_id,
                is_verified=True,
                verification_token=None,
                verification_token_expires_at=None,
            )

            if user:
                logger.info("User verified successfully", user_id=user_id)

            return user

        except Exception as e:
            logger.error("Failed to verify user", user_id=user_id, error=str(e))
            raise

    async def set_reset_token(
        self, user_id: str, token: str, expires_at: datetime
    ) -> Optional[User]:
        """Set password reset token."""
        try:
            user = await self.update(
                user_id, reset_token=token, reset_token_expires_at=expires_at
            )

            if user:
                logger.info("Reset token set", user_id=user_id)

            return user

        except Exception as e:
            logger.error("Failed to set reset token", user_id=user_id, error=str(e))
            raise

    async def clear_reset_token(self, user_id: str) -> Optional[User]:
        """Clear password reset token."""
        try:
            user = await self.update(
                user_id, reset_token=None, reset_token_expires_at=None
            )

            if user:
                logger.info("Reset token cleared", user_id=user_id)

            return user

        except Exception as e:
            logger.error("Failed to clear reset token", user_id=user_id, error=str(e))
            raise

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users with pagination."""
        try:
            result = await self.db.execute(
                select(User)
                .where(User.is_active is True)
                .offset(skip)
                .limit(limit)
                .order_by(User.created_at.desc())
            )
            return result.scalars().all()

        except Exception as e:
            logger.error("Failed to get active users", error=str(e))
            raise

    async def search_users(
        self, query: str, role: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """Search users by email, first name, or last name."""
        try:
            search_filter = or_(
                User.email.ilike(f"%{query}%"),
                User.first_name.ilike(f"%{query}%"),
                User.last_name.ilike(f"%{query}%"),
            )

            filters = [search_filter]
            if role:
                filters.append(User.role == role.upper())

            result = await self.db.execute(
                select(User)
                .where(and_(*filters))
                .offset(skip)
                .limit(limit)
                .order_by(User.created_at.desc())
            )

            return result.scalars().all()

        except Exception as e:
            logger.error("Failed to search users", query=query, role=role, error=str(e))
            raise
