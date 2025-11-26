"""
AutoSourcing models for intelligent product discovery and management.
Integrates with advanced scoring system v1.5.0.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4, UUID

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    Text, ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import relationship

from app.core.db import Base


class JobStatus(Enum):
    """Status of an AutoSourcing job execution."""
    PENDING = "pending"
    RUNNING = "running" 
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


class ActionStatus(Enum):
    """User action taken on a discovered product."""
    PENDING = "pending"      # No action yet
    TO_BUY = "to_buy"        # Marked for purchase
    FAVORITE = "favorite"    # Added to favorites
    IGNORED = "ignored"      # User chose to ignore
    ANALYZING = "analyzing"  # Deep analysis requested


class AutoSourcingJob(Base):
    """
    Represents a single AutoSourcing job execution.
    Each job discovers products based on user-defined criteria.
    """
    __tablename__ = "autosourcing_jobs"

    # Primary fields
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Job identification
    profile_name = Column(String(100), nullable=False, index=True)
    profile_id = Column(PG_UUID(as_uuid=True), ForeignKey("saved_profiles.id"), nullable=True)
    
    # Execution tracking
    launched_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)
    
    # Results summary
    total_tested = Column(Integer, nullable=False, default=0)
    total_selected = Column(Integer, nullable=False, default=0)
    
    # Configuration used (snapshot for reproducibility)
    discovery_config = Column(JSON, nullable=False)  # Keepa search criteria
    scoring_config = Column(JSON, nullable=False)    # Scoring thresholds used
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_count = Column(Integer, nullable=False, default=0)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    picks = relationship("AutoSourcingPick", back_populates="job", cascade="all, delete-orphan")
    profile = relationship("SavedProfile", back_populates="jobs")

    def __repr__(self):
        # Safe repr that works even with detached instances
        try:
            # Try to access id only - should work even if detached
            job_id = self.id
            return f"<AutoSourcingJob(id={job_id})>"
        except (AttributeError, TypeError):
            # Complete fallback if even id fails (detached SQLAlchemy instance)
            return "<AutoSourcingJob(detached)>"


class AutoSourcingPick(Base):
    """
    Represents a single product pick from an AutoSourcing job.
    Includes all scoring data and user actions.
    """
    __tablename__ = "autosourcing_picks"

    # Primary fields  
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(PG_UUID(as_uuid=True), ForeignKey("autosourcing_jobs.id"), nullable=False, index=True)
    
    # Product identification
    asin = Column(String(20), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    
    # Pricing data
    current_price = Column(Float, nullable=True)
    estimated_buy_cost = Column(Float, nullable=True)
    profit_net = Column(Float, nullable=True)
    
    # Core scoring (from v1.5.0 system)
    roi_percentage = Column(Float, nullable=False, index=True)
    velocity_score = Column(Integer, nullable=False, index=True) 
    stability_score = Column(Integer, nullable=False, index=True)
    confidence_score = Column(Integer, nullable=False, index=True)
    overall_rating = Column(String(20), nullable=False, index=True)  # EXCELLENT/GOOD/FAIR/PASS
    
    # Additional metrics
    bsr = Column(Integer, nullable=True)
    category = Column(String(100), nullable=True)
    
    # AI-generated summary
    readable_summary = Column(Text, nullable=True)
    
    # User actions (Quick Actions system)
    action_status = Column(SQLEnum(ActionStatus), nullable=False, default=ActionStatus.PENDING, index=True)
    action_taken_at = Column(DateTime, nullable=True)
    action_notes = Column(Text, nullable=True)
    
    # Action flags for quick filtering
    is_purchased = Column(Boolean, nullable=False, default=False, index=True)
    is_favorite = Column(Boolean, nullable=False, default=False, index=True)
    is_ignored = Column(Boolean, nullable=False, default=False, index=True)
    analysis_requested = Column(Boolean, nullable=False, default=False)
    
    # Advanced analysis data (populated when analysis_requested = True)
    deep_analysis_data = Column(JSON, nullable=True)
    
    # AutoScheduler Tier Classification (v1.7.0)
    priority_tier = Column(String(10), nullable=False, default="WATCH", index=True)  # HOT/TOP/WATCH/OTHER
    tier_reason = Column(Text, nullable=True)                                        # Explication classification
    is_featured = Column(Boolean, nullable=False, default=False, index=True)         # HOT deals = featured
    scheduler_run_id = Column(String(50), nullable=True, index=True)                 # ID du run scheduler
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    job = relationship("AutoSourcingJob", back_populates="picks")

    def __repr__(self):
        return f"<AutoSourcingPick(id={self.id}, asin='{self.asin}', roi={self.roi_percentage}%, rating='{self.overall_rating}')>"


class SavedProfile(Base):
    """
    User-defined search profiles for AutoSourcing.
    Stores both discovery criteria and scoring thresholds.
    """
    __tablename__ = "saved_profiles"

    # Primary fields
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Profile identification  
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Configuration
    discovery_config = Column(JSON, nullable=False)  # Keepa search criteria
    scoring_config = Column(JSON, nullable=False)    # Scoring thresholds
    
    # Settings
    max_results = Column(Integer, nullable=False, default=20)
    active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Usage tracking
    last_used_at = Column(DateTime, nullable=True, index=True)
    usage_count = Column(Integer, nullable=False, default=0)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jobs = relationship("AutoSourcingJob", back_populates="profile")

    def __repr__(self):
        return f"<SavedProfile(id={self.id}, name='{self.name}', active={self.active})>"

    @classmethod
    def create_default_profiles(cls) -> list["SavedProfile"]:
        """Create default profiles for new users."""
        return [
            cls(
                name="Textbooks Conservateur",
                description="Recherche de manuels scolaires avec ROI élevé et faible risque",
                discovery_config={
                    "categories": ["Books", "Textbooks"],
                    "bsr_range": [1000, 25000],
                    "price_range": [30, 300],
                    "availability": "amazon"
                },
                scoring_config={
                    "roi_min": 40,
                    "velocity_min": 70,
                    "stability_min": 80,
                    "confidence_min": 75,
                    "rating_required": "EXCELLENT"
                },
                max_results=15
            ),
            cls(
                name="Electronics Opportunity",
                description="Scanner électronique avec profit rapide",
                discovery_config={
                    "categories": ["Electronics"],
                    "bsr_range": [500, 50000],
                    "price_range": [20, 200],
                    "discount_min": 25
                },
                scoring_config={
                    "roi_min": 25,
                    "velocity_min": 80,
                    "stability_min": 60,
                    "confidence_min": 70,
                    "rating_required": "GOOD"
                },
                max_results=25
            ),
            cls(
                name="Niche Explorer",
                description="Découverte de niches spécialisées peu concurrencées",
                discovery_config={
                    "categories": ["Books", "Professional", "Medical"],
                    "bsr_range": [5000, 100000],
                    "price_range": [40, 500],
                    "availability": "amazon"
                },
                scoring_config={
                    "roi_min": 35,
                    "velocity_min": 60,
                    "stability_min": 85,
                    "confidence_min": 80,
                    "rating_required": "EXCELLENT"
                },
                max_results=10
            )
        ]