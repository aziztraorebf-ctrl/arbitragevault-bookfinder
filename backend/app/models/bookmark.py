"""Bookmark models for saving user niches and analysis configurations."""

from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SavedNiche(Base):
    """Model for saving discovered niches for later re-analysis."""

    __tablename__ = "saved_niches"

    # Basic identification
    niche_name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True,
        comment="User-defined name for the niche (e.g., 'Engineering Textbooks')"
    )
    
    # User association (assuming user_id exists in user table)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, index=True,
        comment="ID of the user who saved this niche"
    )

    # Niche configuration
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="Keepa category ID used for the niche discovery"
    )
    
    category_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="Human-readable category name"
    )
    
    # Analysis parameters stored as JSON
    filters: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Complete analysis parameters (price ranges, BSR thresholds, etc.)"
    )
    
    # Discovery results metadata
    last_score: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="Last calculated niche score when discovered"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Optional user description or notes about the niche"
    )

    # Relationships
    # user = relationship("User", back_populates="saved_niches")

    def __repr__(self) -> str:
        return f"<SavedNiche(id='{self.id}', name='{self.niche_name}', user_id='{self.user_id}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with formatted data."""
        result = super().to_dict()
        # Ensure filters is properly serialized
        result['filters'] = self.filters or {}
        return result

    @classmethod
    def create_from_discovery_result(
        cls,
        user_id: str,
        niche_name: str,
        category_id: Optional[int],
        category_name: Optional[str],
        filters: Dict[str, Any],
        last_score: Optional[float] = None,
        description: Optional[str] = None
    ) -> "SavedNiche":
        """Factory method to create SavedNiche from discovery results."""
        return cls(
            user_id=user_id,
            niche_name=niche_name,
            category_id=category_id,
            category_name=category_name,
            filters=filters,
            last_score=last_score,
            description=description
        )