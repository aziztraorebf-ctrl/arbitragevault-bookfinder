"""Batch model for managing analysis batches."""

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, CheckConstraint, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class BatchStatus(enum.Enum):
    """Status of a batch analysis."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Batch(Base):
    """
    Batch model for managing ISBN/ASIN analysis batches.
    
    Tracks lists of ISBN/ASIN codes being processed, their status,
    and links to strategy profiles and analysis results.
    """
    __tablename__ = "batches"

    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )

    # Batch metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[BatchStatus] = mapped_column(
        SAEnum(BatchStatus, name="batch_status", native_enum=True),
        default=BatchStatus.PENDING, 
        nullable=False
    )

    # Progress tracking
    items_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timing fields
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )

    # Strategy configuration snapshot (JSON)
    strategy_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSON, 
        nullable=True
    )

    # Relationships
    analyses: Mapped[List["Analysis"]] = relationship(
        "Analysis",
        back_populates="batch",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("items_total >= 0", name="check_items_total_positive"),
        CheckConstraint("items_processed >= 0", name="check_items_processed_positive"),
        CheckConstraint("items_processed <= items_total", name="check_processed_not_exceed_total"),
        Index("ix_batches_user_created", "user_id", "created_at"),
        Index("ix_batches_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Batch(id='{self.id}', name='{self.name}', status='{self.status.value}')>"

    @property
    def is_completed(self) -> bool:
        """Check if batch is in a completed state (completed, failed, or cancelled)."""
        return self.status in (BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED)

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.items_total == 0 or self.items_total is None:
            return 0.0
        processed = self.items_processed or 0  # Handle None case
        return (processed / self.items_total) * 100

    def can_transition_to(self, new_status: BatchStatus) -> bool:
        """Check if batch can transition to new status."""
        valid_transitions = {
            BatchStatus.PENDING: [BatchStatus.PROCESSING],
            BatchStatus.PROCESSING: [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED],
            BatchStatus.COMPLETED: [],
            BatchStatus.FAILED: [],
            BatchStatus.CANCELLED: []
        }
        return new_status in valid_transitions.get(self.status, [])