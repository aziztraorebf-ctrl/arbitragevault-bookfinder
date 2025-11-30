"""
Product Cache Models - Phase 2 Jour 5

Cache PostgreSQL pour résultats discovery et scoring.
Évite appels API redondants et améliore performance.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, String, Integer, Float, JSON,
    DateTime, Index, Boolean, Text
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class ProductDiscoveryCache(Base):
    """
    Cache pour résultats Product Discovery.

    TTL: 24h par défaut (Keepa data freshness).
    """

    __tablename__ = "product_discovery_cache"

    # Primary key
    cache_key = Column(String(255), primary_key=True, index=True)

    # Discovery parameters (for cache key generation)
    domain = Column(Integer, nullable=False)
    category = Column(Integer, nullable=True)
    bsr_min = Column(Integer, nullable=True)
    bsr_max = Column(Integer, nullable=True)
    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)

    # Cached results
    asins = Column(JSON, nullable=False)  # List[str]
    count = Column(Integer, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, default=0, nullable=False)

    # Indexes for efficient lookup
    __table_args__ = (
        Index('idx_discovery_cache_expiry', 'expires_at'),
        Index('idx_discovery_cache_params', 'domain', 'category', 'bsr_min', 'bsr_max'),
    )


class ProductScoringCache(Base):
    """
    Cache pour resultats Product Scoring.

    Stocke analyses completes avec ROI/Velocity.
    Schema synchronise avec production Neon (Phase 6 fix).
    """

    __tablename__ = "product_scoring_cache"

    # Primary key - matches production schema
    cache_key = Column(String(255), primary_key=True, index=True)
    asin = Column(String(20), nullable=False, index=True)

    # Scoring results - order matches production
    roi_percent = Column(Float, nullable=False)
    velocity_score = Column(Float, nullable=False)
    recommendation = Column(String(50), nullable=False)
    title = Column(Text, nullable=True)
    price = Column(Float, nullable=True)  # Changed to nullable per production
    bsr = Column(Integer, nullable=True)  # Changed to nullable per production

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, default=0, nullable=False)

    # Indexes - matches production
    __table_args__ = (
        Index('idx_scoring_expires_at', 'expires_at'),
        Index('idx_scoring_asin', 'asin'),
        Index('idx_scoring_roi', 'roi_percent'),
        Index('idx_scoring_velocity', 'velocity_score'),
    )


class SearchHistory(Base):
    """
    Historique des recherches pour analytics.

    Track patterns et optimise suggestions.
    """

    __tablename__ = "search_history"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Search parameters
    search_params = Column(JSON, nullable=False)
    search_type = Column(String(50), nullable=False)  # 'discovery', 'scoring'

    # Results summary
    results_count = Column(Integer, nullable=False)
    top_result_asin = Column(String(20), nullable=True)
    avg_roi = Column(Float, nullable=True)
    avg_velocity = Column(Float, nullable=True)

    # Performance metrics
    api_calls_made = Column(Integer, default=1)
    cache_hits = Column(Integer, default=0)
    response_time_ms = Column(Integer, nullable=True)

    # User tracking (if auth implemented)
    user_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_search_history_date', 'created_at'),
        Index('idx_search_history_type', 'search_type'),
    )