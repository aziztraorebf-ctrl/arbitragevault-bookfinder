"""
Business Configuration Models - Dynamic config with hierarchical overrides.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base, JSONType


class ConfigScope(str, Enum):
    """Configuration scope levels for hierarchical overrides."""
    GLOBAL = "global"
    DOMAIN = "domain"      # domain:1, domain:2, etc.
    CATEGORY = "category"  # category:books, category:media, etc.


class BusinessConfig(Base):
    """
    Hierarchical business configuration storage.
    
    Supports global → domain → category override chain.
    Single-row constraint for global scope (id=1).
    """
    __tablename__ = "business_config"
    
    # Override Base id to use Integer for constraint logic
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Scope definition
    scope: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "global", "domain:1", "category:books"
    
    # Configuration data (JSON for flexibility)
    data: Mapped[Dict[str, Any]] = mapped_column(JSONType, nullable=False)
    
    # Versioning for optimistic concurrency
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Hierarchy reference (for domain/category configs)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("business_config.id", ondelete="CASCADE"), 
        nullable=True,
        index=True
    )
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    
    # Relationships
    children = relationship("BusinessConfig", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("BusinessConfig", back_populates="children", remote_side=[id])
    config_changes = relationship("ConfigChange", back_populates="config", cascade="all, delete-orphan")
    
    # Table constraints
    # Note: Regex constraint removed for SQLite compatibility in tests.
    # Scope format validation is handled at the application layer (Pydantic).
    __table_args__ = (
        # Ensure single global config (id=1)
        CheckConstraint(
            "(scope = 'global' AND id = 1) OR (scope != 'global')",
            name="single_global_config"
        ),
        # Scope format validation: 'global', 'domain:N', or 'category:name'
        # Using LIKE patterns instead of regex for SQLite compatibility
        CheckConstraint(
            "scope = 'global' OR scope LIKE 'domain:%' OR scope LIKE 'category:%'",
            name="valid_scope_format"
        )
    )
    
    def __repr__(self):
        return f"<BusinessConfig(scope='{self.scope}', version={self.version})>"
    
    def increment_version(self):
        """Increment version for optimistic concurrency control."""
        self.version += 1
    
    @property
    def scope_type(self) -> str:
        """Extract scope type from scope string."""
        return self.scope.split(":")[0]
    
    @property
    def scope_value(self) -> Optional[str]:
        """Extract scope value from scope string."""
        parts = self.scope.split(":", 1)
        return parts[1] if len(parts) > 1 else None


class ConfigChange(Base):
    """
    Audit trail for business configuration changes.
    
    Stores JSONPatch diffs for detailed change tracking.
    """
    __tablename__ = "config_changes"
    
    # Foreign key to config that was changed
    config_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("business_config.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Change details
    old_config: Mapped[Dict[str, Any]] = mapped_column(JSONType, nullable=True)  # Full config before change
    new_config: Mapped[Dict[str, Any]] = mapped_column(JSONType, nullable=False) # Full config after change
    diff_jsonpatch: Mapped[list] = mapped_column(JSONType, nullable=False)       # JSONPatch diff array
    
    # Change metadata
    changed_by: Mapped[str] = mapped_column(String(100), nullable=False)      # User/system identifier
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Optional description
    
    # Source of change
    change_source: Mapped[str] = mapped_column(
        String(20), 
        default="api", 
        nullable=False
    )  # "api", "migration", "system", etc.
    
    # Version tracking
    old_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    new_version: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relationships
    config = relationship("BusinessConfig", back_populates="config_changes")
    
    def __repr__(self):
        return f"<ConfigChange(config_id={self.config_id}, changed_by='{self.changed_by}', version={self.old_version}→{self.new_version})>"
    
    @property
    def summary(self) -> str:
        """Generate human-readable change summary."""
        if not self.diff_jsonpatch:
            return "No changes detected"
        
        change_count = len(self.diff_jsonpatch)
        operations = [change.get("op", "unknown") for change in self.diff_jsonpatch]
        op_summary = ", ".join(set(operations))
        
        return f"{change_count} changes ({op_summary})"


# Default configuration structure for seeding
DEFAULT_BUSINESS_CONFIG = {
    "roi": {
        "target_pct_default": 30.0,        # Default ROI target (30%)
        "min_for_buy": 15.0,               # Minimum ROI for BUY recommendation
        "excellent_threshold": 50.0,        # ROI for "excellent" tier
        "good_threshold": 30.0,            # ROI for "good" tier  
        "fair_threshold": 15.0             # ROI for "fair" tier
    },
    "combined_score": {
        "roi_weight": 0.6,                 # ROI weight in combined score
        "velocity_weight": 0.4             # Velocity weight in combined score
    },
    "fees": {
        "buffer_pct_default": 5.0,         # Safety buffer percentage
        "books": {
            "referral_fee_pct": 15.0,
            "closing_fee": 1.80,
            "fba_fee_base": 2.50,
            "fba_fee_per_lb": 0.40,
            "inbound_shipping": 0.40,
            "prep_fee": 0.20
        }
    },
    "velocity": {
        "fast_threshold": 80.0,            # Velocity score for "fast" tier
        "medium_threshold": 60.0,          # Velocity score for "medium" tier
        "slow_threshold": 40.0,            # Velocity score for "slow" tier
        "benchmarks": {
            "books": 100000,               # Books category BSR benchmark
            "media": 50000,                # Media category BSR benchmark
            "default": 150000              # Default category BSR benchmark
        }
    },
    "recommendation_rules": [
        {
            "label": "STRONG BUY",
            "min_roi": 30.0,
            "min_velocity": 70.0,
            "description": "High profit, fast moving"
        },
        {
            "label": "BUY", 
            "min_roi": 20.0,
            "min_velocity": 50.0,
            "description": "Good opportunity"
        },
        {
            "label": "CONSIDER",
            "min_roi": 15.0,
            "min_velocity": 0.0,
            "description": "Monitor for better entry"
        },
        {
            "label": "PASS",
            "min_roi": 0.0,
            "min_velocity": 0.0,
            "description": "Low profit/slow moving"
        }
    ],
    "demo_asins": [
        "B00FLIJJSA",                      # The Mirrored Heavens
        "B08N5WRWNW",                      # Technical book example
        "B07FNW9FGJ"                       # Popular fiction example
    ],
    "meta": {
        "version": "1.0.0",
        "created_by": "system_seed",
        "description": "Default business configuration for ArbitrageVault"
    }
}