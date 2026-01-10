"""User model for authentication and authorization."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserRole(str, Enum):
    """User roles for role-based access control."""
    ADMIN = "ADMIN"
    SOURCER = "SOURCER"


class User(Base):
    """User model with role-based access control."""

    __tablename__ = "users"

    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    # Firebase UID (primary auth method)
    # Threshold: Max 128 chars
    # Justification: Firebase UIDs are 28 chars, extra margin for future changes
    # Nullable: True for legacy users created before Firebase migration
    firebase_uid: Mapped[Optional[str]] = mapped_column(
        String(128), unique=True, index=True, nullable=True
    )

    # Password hash (legacy, nullable for Firebase users)
    # Nullable: True because Firebase users don't have passwords stored locally
    password_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Profile information
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Role-based access control
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="SOURCER")

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps for security
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Account management
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)

    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Verification
    verification_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    verification_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Password reset
    reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email.split("@")[0]

    @property
    def is_locked(self) -> bool:
        """Check if account is temporarily locked."""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until

    def can_attempt_login(self) -> bool:
        """Check if user can attempt to login."""
        return self.is_active and not self.is_locked

    def increment_failed_attempts(self) -> None:
        """Increment failed login attempts counter."""
        self.failed_login_attempts += 1

    def reset_failed_attempts(self) -> None:
        """Reset failed login attempts counter."""
        self.failed_login_attempts = 0
        self.locked_until = None

    def lock_account(self, until: datetime) -> None:
        """Lock account until specified datetime."""
        self.locked_until = until

    def set_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()

    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id='{self.id}', email='{self.email}', role='{self.role}')>"
