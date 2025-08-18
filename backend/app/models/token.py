"""Token model for refresh token management."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class RefreshToken(Base):
    """Refresh token model for JWT token management."""

    __tablename__ = "refresh_tokens"

    # User relationship
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Token data
    token_hash: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )

    # Expiration
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Revocation
    is_revoked: Mapped[bool] = mapped_column(default=False, nullable=False)

    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Metadata for security tracking
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True  # IPv6 max length
    )

    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Last used tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="select")

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)."""
        return not self.is_expired and not self.is_revoked

    def revoke(self) -> None:
        """Revoke the token."""
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()

    def update_last_used(self, ip_address: Optional[str] = None) -> None:
        """Update last used timestamp and IP address."""
        self.last_used_at = datetime.utcnow()
        if ip_address:
            self.ip_address = ip_address

    def __repr__(self) -> str:
        """String representation of the token."""
        return f"<RefreshToken(id='{self.id}', user_id='{self.user_id}', expires_at='{self.expires_at}')>"
