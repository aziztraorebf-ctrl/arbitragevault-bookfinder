"""User repository with authentication and security features."""

from typing import Optional
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base_repository import BaseRepository
from app.models.user import User
from app.core.exceptions import DuplicateEmailError

logger = structlog.get_logger()


class UserRepository(BaseRepository[User]):
    """Repository for User model with authentication features."""
    
    SORTABLE_FIELDS = ["id", "email", "created_at", "first_name", "last_name", "role", "last_login_at"]
    FILTERABLE_FIELDS = ["id", "email", "role", "is_active", "is_verified", "first_name", "last_name"]

    def __init__(self, db_session: AsyncSession, model: type = User):
        """Initialize UserRepository with User model."""
        super().__init__(db_session, model)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        try:
            result = await self.db.execute(
                select(User).where(User.email == email.lower())
            )
            user = result.scalar_one_or_none()
            
            if user:
                logger.info("User retrieved by email", email=email, user_id=user.id)
            
            return user
            
        except Exception as e:
            logger.error("Failed to get user by email", email=email, error=str(e))
            raise

    async def is_email_taken(self, email: str, exclude_user_id: Optional[str] = None) -> bool:
        """Check if email is already taken by another user."""
        try:
            query = select(User.id).where(User.email == email.lower())
            
            if exclude_user_id:
                query = query.where(User.id != exclude_user_id)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error("Failed to check email availability", email=email, error=str(e))
            raise

    async def create_user(
        self,
        email: str,
        password_hash: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: str = "sourcer",
        is_active: bool = True,
        is_verified: bool = False
    ) -> User:
        """
        Create a new user with duplicate email validation.
        
        Raises:
            DuplicateEmailError: If email is already taken
        """
        try:
            email_lower = email.lower()
            
            # Check for duplicate email first
            if await self.is_email_taken(email_lower):
                raise DuplicateEmailError(email_lower)
            
            user = User(
                email=email_lower,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                role=role.lower(),
                is_active=is_active,
                is_verified=is_verified,
                password_changed_at=datetime.utcnow()
            )
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(
                "User created successfully", 
                user_id=user.id, 
                email=email_lower, 
                role=role
            )
            
            return user
            
        except DuplicateEmailError:
            await self.db.rollback()
            raise
        except IntegrityError as e:
            await self.db.rollback()
            if "UNIQUE constraint failed: users.email" in str(e):
                raise DuplicateEmailError(email_lower)
            logger.error("Database integrity error creating user", email=email, error=str(e))
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to create user", email=email, error=str(e))
            raise

    async def safe_get_user_for_auth(self, email: str) -> Optional[dict]:
        """
        Get user data for authentication without exposing sensitive fields.
        
        Returns:
            Dict with safe user data or None if not found
        """
        try:
            user = await self.get_by_email(email)
            
            if not user:
                return None
            
            # Return safe subset of user data
            return {
                "id": user.id,
                "email": user.email,
                "password_hash": user.password_hash,  # Needed for verification
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_locked": user.is_locked,
                "failed_login_attempts": user.failed_login_attempts,
                "can_attempt_login": user.can_attempt_login(),
                "full_name": user.full_name
            }
            
        except Exception as e:
            logger.error("Failed to get user for auth", email=email, error=str(e))
            raise

    async def update_login_tracking(
        self, 
        user_id: str, 
        success: bool, 
        reset_attempts: bool = False
    ) -> Optional[User]:
        """Update user login tracking information."""
        try:
            user = await self.get_by_id(user_id)
            
            if not user:
                return None
            
            if success:
                user.set_last_login()
                user.reset_failed_attempts()
            else:
                user.increment_failed_attempts()
                
                # Lock account after 5 failed attempts for 15 minutes
                if user.failed_login_attempts >= 5:
                    from datetime import timedelta
                    lock_until = datetime.utcnow() + timedelta(minutes=15)
                    user.lock_account(lock_until)
                    logger.warning(
                        "Account locked due to failed attempts",
                        user_id=user_id,
                        attempts=user.failed_login_attempts
                    )
            
            if reset_attempts:
                user.reset_failed_attempts()
            
            await self.db.commit()
            await self.db.refresh(user)
            
            return user
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to update login tracking", user_id=user_id, error=str(e))
            raise

    async def update_password(self, user_id: str, new_password_hash: str) -> Optional[User]:
        """Update user password and reset related security fields."""
        try:
            updates = {
                "password_hash": new_password_hash,
                "password_changed_at": datetime.utcnow(),
                "reset_token": None,
                "reset_token_expires_at": None,
            }
            
            user = await self.update(user_id, **updates)
            
            if user:
                logger.info("Password updated successfully", user_id=user_id)
            
            return user
            
        except Exception as e:
            logger.error("Failed to update password", user_id=user_id, error=str(e))
            raise

    async def set_verification_token(
        self, 
        user_id: str, 
        token: str, 
        expires_at: datetime
    ) -> Optional[User]:
        """Set email verification token."""
        try:
            updates = {
                "verification_token": token,
                "verification_token_expires_at": expires_at
            }
            
            user = await self.update(user_id, **updates)
            
            if user:
                logger.info("Verification token set", user_id=user_id)
            
            return user
            
        except Exception as e:
            logger.error("Failed to set verification token", user_id=user_id, error=str(e))
            raise

    async def verify_user(self, token: str) -> Optional[User]:
        """Verify user by token and mark as verified."""
        try:
            result = await self.db.execute(
                select(User).where(
                    User.verification_token == token,
                    User.verification_token_expires_at > datetime.utcnow()
                )
            )
            user = result.scalar_one_or_none()
            
            if user:
                updates = {
                    "is_verified": True,
                    "verification_token": None,
                    "verification_token_expires_at": None
                }
                
                user = await self.update(user.id, **updates)
                logger.info("User verified successfully", user_id=user.id)
            
            return user
            
        except Exception as e:
            logger.error("Failed to verify user", token=token, error=str(e))
            raise

    async def set_reset_token(
        self, 
        user_id: str, 
        token: str, 
        expires_at: datetime
    ) -> Optional[User]:
        """Set password reset token."""
        try:
            updates = {
                "reset_token": token,
                "reset_token_expires_at": expires_at
            }
            
            user = await self.update(user_id, **updates)
            
            if user:
                logger.info("Reset token set", user_id=user_id)
            
            return user
            
        except Exception as e:
            logger.error("Failed to set reset token", user_id=user_id, error=str(e))
            raise

    async def get_by_reset_token(self, token: str) -> Optional[User]:
        """Get user by valid reset token."""
        try:
            result = await self.db.execute(
                select(User).where(
                    User.reset_token == token,
                    User.reset_token_expires_at > datetime.utcnow()
                )
            )
            
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get user by reset token", token=token, error=str(e))
            raise

    async def get_active_users_count(self) -> int:
        """Get count of active users."""
        try:
            return await self.count(filters={"is_active": True})
        except Exception as e:
            logger.error("Failed to get active users count", error=str(e))
            raise

    async def get_users_by_role(self, role: str, active_only: bool = True) -> list[User]:
        """Get users by role with optional active filter."""
        try:
            filters = {"role": role.lower()}
            
            if active_only:
                filters["is_active"] = True
            
            page = await self.list(
                filters=filters,
                sort_by=["last_login_at", "created_at"],
                sort_order=["desc", "desc"],
                limit=1000  # Reasonable limit
            )
            
            return page.items
            
        except Exception as e:
            logger.error("Failed to get users by role", role=role, error=str(e))
            raise