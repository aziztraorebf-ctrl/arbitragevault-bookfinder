"""
SQLAlchemy models for configuration management.

This module defines the database tables for storing business configuration
and category-specific overrides.
"""

from sqlalchemy import Column, String, JSON, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class Configuration(Base):
    """Main configuration table."""

    __tablename__ = "configurations"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)

    # Configuration sections stored as JSON
    fees = Column(JSON, nullable=False)
    roi = Column(JSON, nullable=False)
    velocity = Column(JSON, nullable=False)
    data_quality = Column(JSON, nullable=False)
    product_finder = Column(JSON, nullable=False)

    # Activation status
    is_active = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category_overrides = relationship(
        "CategoryOverride",
        back_populates="configuration",
        cascade="all, delete-orphan"
    )


class CategoryOverride(Base):
    """Category-specific configuration overrides."""

    __tablename__ = "category_overrides"

    id = Column(String, primary_key=True)
    config_id = Column(String, ForeignKey("configurations.id"), nullable=False)
    category_id = Column(Integer, nullable=False, index=True)
    category_name = Column(String, nullable=False)

    # Override sections (NULL means use base config)
    fees = Column(JSON, nullable=True)
    roi = Column(JSON, nullable=True)
    velocity = Column(JSON, nullable=True)

    # Relationship
    configuration = relationship("Configuration", back_populates="category_overrides")