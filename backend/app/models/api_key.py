"""API Key model for external automation authentication."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, JSONType

if TYPE_CHECKING:
    from .user import User


class APIKey(Base):
    """API Key model for authenticating external services like N8N."""

    __tablename__ = "api_keys"

    # Owner relationship
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Key storage (SHA-256 hash, never store raw key)
    key_hash: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True
    )

    # First 8 chars of key for identification (e.g. "avk_abc1...")
    key_prefix: Mapped[str] = mapped_column(
        String(12), nullable=False,
    )

    # Human-readable name for the key
    name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )

    # Scopes this key is authorized for
    scopes: Mapped[Optional[list]] = mapped_column(
        JSONType, nullable=True, default=lambda: [],
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="select")

    @property
    def is_expired(self) -> bool:
        """Check if key is expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if key is valid (active and not expired)."""
        return self.is_active and not self.is_expired

    def revoke(self) -> None:
        """Revoke the API key."""
        self.is_active = False

    def update_last_used(self) -> None:
        """Update last used timestamp."""
        self.last_used_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """String representation of the API key."""
        return f"<APIKey(id='{self.id}', name='{self.name}', prefix='{self.key_prefix}')>"
