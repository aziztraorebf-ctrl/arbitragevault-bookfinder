"""
Advanced Analytics models for Phase 8.0
Historical tracking of ASINs, runs, and decision outcomes.
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    Text, ForeignKey, JSON, Numeric, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class ASINHistory(Base):
    """
    Historical tracking of ASIN metrics over time.
    Updated daily by background Celery job.
    """
    __tablename__ = "asin_history"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))

    asin = Column(String(10), nullable=False, index=True)
    tracked_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")

    price = Column(Numeric(10, 2), nullable=True)
    lowest_fba_price = Column(Numeric(10, 2), nullable=True)
    bsr = Column(Integer, nullable=True)
    seller_count = Column(Integer, nullable=True)
    amazon_on_listing = Column(Boolean, nullable=True)
    fba_seller_count = Column(Integer, nullable=True)

    extra_data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")

    __table_args__ = (
        Index('idx_asin_history_asin_tracked', 'asin', 'tracked_at'),
        Index('idx_asin_history_tracked_at', 'tracked_at'),
    )


class RunHistory(Base):
    """
    Historical tracking of AutoSourcing job executions.
    Stores configuration snapshots and results.
    """
    __tablename__ = "run_history"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))

    job_id = Column(PG_UUID(as_uuid=False), nullable=False, index=True)
    config_snapshot = Column(JSON, nullable=False)

    total_products_discovered = Column(Integer, nullable=False)
    total_picks_generated = Column(Integer, nullable=False)
    success_rate = Column(Numeric(5, 2), nullable=True)

    tokens_consumed = Column(Integer, nullable=False, default=0)
    execution_time_seconds = Column(Float, nullable=True)

    executed_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")

    __table_args__ = (
        Index('idx_run_history_job_id', 'job_id'),
        Index('idx_run_history_executed_at', 'executed_at'),
    )


class DecisionOutcome(Base):
    """
    Tracking of predicted vs actual decision outcomes.
    Used for model accuracy validation and improvement.
    """
    __tablename__ = "decision_outcomes"

    id = Column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))

    asin = Column(String(10), nullable=False, index=True)
    decision = Column(String(20), nullable=False)
    predicted_roi = Column(Numeric(5, 2), nullable=True)
    predicted_velocity = Column(Numeric(5, 2), nullable=True)
    predicted_risk_score = Column(Numeric(5, 2), nullable=True)

    actual_outcome = Column(String(20), nullable=True)
    actual_roi = Column(Numeric(5, 2), nullable=True)
    time_to_sell_days = Column(Integer, nullable=True)

    outcome_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")

    __table_args__ = (
        Index('idx_decision_outcome_asin', 'asin'),
        Index('idx_decision_outcome_decision', 'decision'),
        Index('idx_decision_outcome_created_at', 'created_at'),
    )
