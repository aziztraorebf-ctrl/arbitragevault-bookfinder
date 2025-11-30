"""Base model class with common fields and utilities."""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, func, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class JSONType(TypeDecorator):
    """
    Cross-database JSON type.

    Uses JSONB on PostgreSQL for better performance and indexing.
    Falls back to JSON on SQLite and other databases for test compatibility.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class Base(DeclarativeBase):
    """Base class for all database models."""

    # Common fields for all models
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model fields from dictionary."""
        for key, value in data.items():
            if hasattr(self, key) and key not in ("id", "created_at", "updated_at"):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id='{self.id}')>"
