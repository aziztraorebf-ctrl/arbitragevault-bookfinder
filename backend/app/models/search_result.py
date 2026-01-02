"""
Search Result model for centralized search persistence.
Phase 11 - Mes Recherches feature.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

from sqlalchemy import String, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, JSONType


class SearchSource(str, Enum):
    """Source of the search results."""
    NICHE_DISCOVERY = "niche_discovery"
    AUTOSOURCING = "autosourcing"
    MANUAL_ANALYSIS = "manual_analysis"


class SearchResult(Base):
    """
    Centralized storage for search results from all modules.

    Stores product results with 30-day retention for later review.
    """

    __tablename__ = "search_results"

    # Search metadata
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True,
        comment="User-defined or auto-generated search name"
    )

    source: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="Source module: niche_discovery, autosourcing, manual_analysis"
    )

    # Search parameters used (for reference/re-run)
    search_params: Mapped[Dict[str, Any]] = mapped_column(
        JSONType, nullable=False, default=dict,
        comment="Original search parameters for reference"
    )

    # Product results stored as JSONB array
    products: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONType, nullable=False, default=list,
        comment="Array of product data (DisplayableProduct format)"
    )

    # Result statistics
    product_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Number of products in results"
    )

    # Optional notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="User notes about this search"
    )

    # Expiration for auto-cleanup (30 days from creation)
    expires_at: Mapped[datetime] = mapped_column(
        nullable=False, index=True,
        comment="Auto-cleanup date (created_at + 30 days)"
    )

    # Composite index for common queries
    __table_args__ = (
        Index('ix_search_results_source_created', 'source', 'created_at'),
    )

    def __init__(self, **kwargs):
        """Set expires_at to 30 days from now if not provided."""
        if 'expires_at' not in kwargs:
            kwargs['expires_at'] = datetime.utcnow() + timedelta(days=30)
        if 'product_count' not in kwargs and 'products' in kwargs:
            kwargs['product_count'] = len(kwargs['products'])
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<SearchResult(id='{self.id}', name='{self.name}', source='{self.source}', count={self.product_count})>"

    @classmethod
    def create_from_results(
        cls,
        name: str,
        source: SearchSource,
        products: List[Dict[str, Any]],
        search_params: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> "SearchResult":
        """Factory method to create SearchResult from module results."""
        return cls(
            name=name,
            source=source.value,
            products=products,
            product_count=len(products),
            search_params=search_params or {},
            notes=notes
        )
