"""
SQLAlchemy models for search history tracking.

This module defines the database table for storing user search history,
particularly for Product Finder searches.
"""

from sqlalchemy import Column, String, JSON, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class SearchHistory(Base):
    """
    Search history table for tracking Product Finder searches.

    This table stores user searches for later reuse, analytics,
    and cache optimization.
    """

    __tablename__ = "search_history"

    id = Column(String, primary_key=True)

    # User relationship (nullable for anonymous searches in MVP)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    # Search type
    search_type = Column(
        String,
        nullable=False,
        default="product_finder",
        index=True
    )  # product_finder, manual_analysis, autosourcing

    # Search parameters
    search_params = Column(JSON, nullable=False)
    # Example structure:
    # {
    #     "category_id": 1234,
    #     "category_name": "Books",
    #     "bsr_range": [1000, 50000],
    #     "price_range": [10.00, 100.00],
    #     "exclude_variations": true,
    #     "require_buy_box": true,
    #     "additional_filters": {}
    # }

    # Results metadata
    results_count = Column(Integer, default=0)
    asins_found = Column(ARRAY(String), nullable=True)  # List of ASINs found

    # Performance metrics
    keepa_tokens_used = Column(Integer, default=0)
    response_time_ms = Column(Integer, nullable=True)
    cache_hit = Column(String, nullable=True)  # full, partial, miss

    # User interaction tracking
    asins_selected = Column(
        ARRAY(String),
        nullable=True
    )  # ASINs user actually analyzed
    asins_purchased = Column(
        ARRAY(String),
        nullable=True
    )  # ASINs user marked as purchased (for tracking)

    # Optional user notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Optional expiry for cache management
    expires_at = Column(DateTime, nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="search_history", lazy="joined")


class SavedSearch(Base):
    """
    Saved searches for quick access.

    Users can save frequently used search configurations.
    """

    __tablename__ = "saved_searches"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Search metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Search configuration
    search_type = Column(String, nullable=False, default="product_finder")
    search_params = Column(JSON, nullable=False)

    # Usage tracking
    use_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="saved_searches", lazy="joined")