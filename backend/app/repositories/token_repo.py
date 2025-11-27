"""Token repository for refresh token management."""

from datetime import datetime
from typing import List, Optional

import structlog
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import RefreshToken

from .base_repository import BaseRepository

logger = structlog.get_logger()


class TokenRepository(BaseRepository[RefreshToken]):
    """Repository for refresh token operations."""

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, RefreshToken)

    async def create_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RefreshToken:
        """Create a new refresh token."""
        try:
            token = await self.create(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(
                "Refresh token created",
                token_id=token.id,
                user_id=user_id,
                expires_at=expires_at,
            )

            return token

        except Exception as e:
            logger.error(
                "Failed to create refresh token", user_id=user_id, error=str(e)
            )
            raise

    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by token hash."""
        try:
            result = await self.db.execute(
                select(RefreshToken).where(RefreshToken.token_hash == token_hash)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error("Failed to get token by hash", error=str(e))
            raise

    async def get_user_tokens(
        self, user_id: str, active_only: bool = True
    ) -> List[RefreshToken]:
        """Get all tokens for a user."""
        try:
            query = select(RefreshToken).where(RefreshToken.user_id == user_id)

            if active_only:
                query = query.where(
                    and_(
                        RefreshToken.is_revoked is False,
                        RefreshToken.expires_at > datetime.utcnow(),
                    )
                )

            result = await self.db.execute(
                query.order_by(RefreshToken.created_at.desc())
            )

            return result.scalars().all()

        except Exception as e:
            logger.error("Failed to get user tokens", user_id=user_id, error=str(e))
            raise

    async def revoke_token(self, token_id: str) -> Optional[RefreshToken]:
        """Revoke a refresh token."""
        try:
            token = await self.update(
                token_id, is_revoked=True, revoked_at=datetime.utcnow()
            )

            if token:
                logger.info(
                    "Refresh token revoked", token_id=token_id, user_id=token.user_id
                )

            return token

        except Exception as e:
            logger.error("Failed to revoke token", token_id=token_id, error=str(e))
            raise

    async def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user."""
        try:
            # Get all active tokens for user
            active_tokens = await self.get_user_tokens(user_id, active_only=True)

            revoked_count = 0
            for token in active_tokens:
                await self.revoke_token(token.id)
                revoked_count += 1

            logger.info(
                "User tokens revoked", user_id=user_id, revoked_count=revoked_count
            )

            return revoked_count

        except Exception as e:
            logger.error("Failed to revoke user tokens", user_id=user_id, error=str(e))
            raise

    async def update_last_used(
        self, token_id: str, ip_address: Optional[str] = None
    ) -> Optional[RefreshToken]:
        """Update token last used timestamp."""
        try:
            update_data = {"last_used_at": datetime.utcnow()}
            if ip_address:
                update_data["ip_address"] = ip_address

            token = await self.update(token_id, **update_data)

            return token

        except Exception as e:
            logger.error(
                "Failed to update token last used", token_id=token_id, error=str(e)
            )
            raise

    async def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from database."""
        try:
            result = await self.db.execute(
                delete(RefreshToken).where(RefreshToken.expires_at <= datetime.utcnow())
            )

            deleted_count = result.rowcount
            await self.db.commit()

            logger.info("Expired tokens cleaned up", deleted_count=deleted_count)

            return deleted_count

        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to cleanup expired tokens", error=str(e))
            raise

    async def cleanup_revoked_tokens(self, days_old: int = 30) -> int:
        """Remove old revoked tokens from database."""
        try:
            cutoff_date = datetime.utcnow().replace(microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)

            result = await self.db.execute(
                delete(RefreshToken).where(
                    and_(
                        RefreshToken.is_revoked is True,
                        RefreshToken.revoked_at <= cutoff_date,
                    )
                )
            )

            deleted_count = result.rowcount
            await self.db.commit()

            logger.info(
                "Old revoked tokens cleaned up",
                deleted_count=deleted_count,
                days_old=days_old,
            )

            return deleted_count

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to cleanup old revoked tokens", days_old=days_old, error=str(e)
            )
            raise

    async def validate_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Validate refresh token and return if valid."""
        try:
            token = await self.get_by_token_hash(token_hash)

            if not token:
                logger.warning("Token not found", token_hash=token_hash[:10] + "...")
                return None

            if not token.is_valid:
                logger.warning(
                    "Invalid token",
                    token_id=token.id,
                    is_revoked=token.is_revoked,
                    is_expired=token.is_expired,
                )
                return None

            # Update last used
            await self.update_last_used(token.id)

            return token

        except Exception as e:
            logger.error("Failed to validate token", error=str(e))
            raise
