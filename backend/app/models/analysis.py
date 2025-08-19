"""Analysis model for individual book analysis results."""

from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    CheckConstraint, 
    ForeignKey, 
    Index, 
    Integer, 
    JSON,
    Numeric, 
    String, 
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Analysis(Base):
    """
    Analysis model for individual book analysis results.
    
    Stores calculated metrics for each ISBN/ASIN within a batch,
    including profit calculations, ROI, velocity scores, and raw Keepa data.
    """
    __tablename__ = "analyses"

    # Foreign key to batch
    batch_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("batches.id", ondelete="CASCADE"), 
        nullable=False
    )

    # Book identifier (normalized)
    isbn_or_asin: Mapped[str] = mapped_column(String(20), nullable=False)

    # Financial calculations (using Decimal for precision)
    buy_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), 
        nullable=False
    )
    fees: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), 
        nullable=False
    )
    expected_sale_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), 
        nullable=False
    )
    profit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), 
        nullable=False
    )
    roi_percent: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), 
        nullable=False
    )

    # Velocity and market data
    velocity_score: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), 
        nullable=False
    )
    rank_snapshot: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
    )
    offers_count: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
    )

    # Raw Keepa data (for debugging/traceability)
    raw_keepa: Mapped[Optional[dict]] = mapped_column(
        JSON, 
        nullable=True
    )

    # Relationships
    batch: Mapped["Batch"] = relationship(
        "Batch", 
        back_populates="analyses"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("batch_id", "isbn_or_asin", name="uq_analysis_batch_isbn"),
        CheckConstraint("velocity_score >= 0", name="check_velocity_score_min"),
        CheckConstraint("velocity_score <= 100", name="check_velocity_score_max"),
        CheckConstraint("buy_price >= 0", name="check_buy_price_positive"),
        CheckConstraint("fees >= 0", name="check_fees_positive"),
        CheckConstraint("expected_sale_price >= 0", name="check_sale_price_positive"),
        Index("ix_analyses_batch_id", "batch_id"),
        Index("ix_analyses_isbn", "isbn_or_asin"),
        Index("ix_analyses_roi", "roi_percent"),
        Index("ix_analyses_velocity", "velocity_score"),
    )

    def __repr__(self) -> str:
        return f"<Analysis(id='{self.id}', isbn='{self.isbn_or_asin}', roi={self.roi_percent}%)>"

    @property
    def is_profitable(self) -> bool:
        """Check if analysis shows positive profit."""
        return self.profit > 0

    def meets_roi_threshold(self, threshold: Decimal) -> bool:
        """Check if analysis meets minimum ROI threshold."""
        return self.roi_percent >= threshold

    @property
    def risk_level(self) -> str:
        """Calculate risk level based on velocity score and ROI."""
        if self.velocity_score >= 70 and self.roi_percent >= 30:
            return "low"
        elif self.velocity_score >= 40 and self.roi_percent >= 15:
            return "medium"
        else:
            return "high"

    def validate_profit_calculation(self) -> bool:
        """Validate that profit matches expected calculation."""
        expected_profit = self.expected_sale_price - (self.buy_price + self.fees)
        # Use small tolerance for decimal comparison
        tolerance = Decimal("0.01")
        return abs(self.profit - expected_profit) <= tolerance