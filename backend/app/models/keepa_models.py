"""
Keepa data models for PostgreSQL with JSONB hybrid approach.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import String, DateTime, Text, ForeignKey, Numeric, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base, JSONType


class ProductStatus(str, Enum):
    """Product resolution status."""
    ACTIVE = "active"          # Successfully resolved and active
    UNRESOLVED = "unresolved"  # Could not resolve identifier  
    DISCONTINUED = "discontinued"  # Product no longer available
    RESTRICTED = "restricted"   # Access restricted (region, etc.)


class KeepaProduct(Base):
    """
    Keepa product metadata - stable data cached for 24h.
    
    Stores core product information that changes rarely.
    """
    __tablename__ = "keepa_products"
    
    # Keepa-specific fields (Base provides id, created_at, updated_at)
    asin: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True) 
    brand: Mapped[str] = mapped_column(String(200), nullable=True)
    manufacturer: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # Product dimensions/weight for FBA calculations  
    package_height: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)  # cm
    package_length: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)  # cm  
    package_width: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)   # cm
    package_weight: Mapped[float] = mapped_column(Numeric(10, 3), nullable=True)  # kg
    
    # Status and metadata
    status: Mapped[str] = mapped_column(String(20), default=ProductStatus.ACTIVE.value)
    domain: Mapped[int] = mapped_column(Integer, default=1)  # Keepa domain (1=US)
    
    # Original identifier used for resolution
    original_identifier: Mapped[str] = mapped_column(String(20), nullable=True)  # ISBN/ASIN used for lookup
    identifier_type: Mapped[str] = mapped_column(String(10), nullable=True)      # "asin", "isbn10", "isbn13"
    
    # Additional timestamp
    last_keepa_sync: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    snapshots = relationship("KeepaSnapshot", back_populates="product", cascade="all, delete-orphan")
    calc_metrics = relationship("CalcMetrics", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KeepaProduct(asin='{self.asin}', title='{self.title[:30]}...')>"


class KeepaSnapshot(Base):
    """
    Keepa product snapshot - volatile pricing/BSR data cached 30-60min.
    
    Uses JSONB for flexibility with Keepa's complex data structures.
    """
    __tablename__ = "keepa_snapshots"
    
    # Foreign key to product (UUID from Base)
    product_id: Mapped[str] = mapped_column(ForeignKey("keepa_products.id", ondelete="CASCADE"), index=True)
    
    # Snapshot metadata
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    data_window_days: Mapped[int] = mapped_column(Integer, default=30)  # Days of historical data
    
    # Current pricing (extracted for quick queries)
    current_buybox_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    current_amazon_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)  
    current_fba_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    current_fbm_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    current_bsr: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    
    # JSON storage for full Keepa data (uses JSONB on PostgreSQL, JSON on SQLite)
    raw_data: Mapped[dict] = mapped_column(JSONType, nullable=True)         # Complete Keepa API response
    metrics_data: Mapped[dict] = mapped_column(JSONType, nullable=True)     # Processed metrics for UI
    
    # Quick access metrics (denormalized for performance)
    offers_count: Mapped[int] = mapped_column(Integer, nullable=True)
    buybox_seller_type: Mapped[str] = mapped_column(String(20), nullable=True)  # "Amazon", "FBA", "FBM"
    is_prime_eligible: Mapped[str] = mapped_column(String(10), nullable=True)   # "Yes", "No", "Unknown"
    
    # Relationships  
    product = relationship("KeepaProduct", back_populates="snapshots")
    
    def __repr__(self):
        return f"<KeepaSnapshot(asin='{self.product.asin if self.product else 'unknown'}', snapshot_date='{self.snapshot_date}')>"


class CalcMetrics(Base):
    """
    Calculated business metrics - ROI, velocity, profitability analysis.
    
    Computed from Keepa snapshots + Amazon fee configuration.
    """
    __tablename__ = "calc_metrics"
    
    # Foreign keys (UUID from Base)
    product_id: Mapped[str] = mapped_column(ForeignKey("keepa_products.id", ondelete="CASCADE"), index=True)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey("keepa_snapshots.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Profit calculations
    estimated_sell_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)     # Target selling price
    estimated_buy_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)       # Current buy cost
    amazon_fees_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)        # All Amazon fees
    net_profit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True, index=True)   # Profit after all costs
    roi_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True, index=True) # ROI %
    margin_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)         # Margin %
    
    # Fee breakdown
    referral_fee: Mapped[float] = mapped_column(Numeric(8, 2), nullable=True)
    closing_fee: Mapped[float] = mapped_column(Numeric(8, 2), nullable=True)  
    fba_fee: Mapped[float] = mapped_column(Numeric(8, 2), nullable=True)
    inbound_shipping: Mapped[float] = mapped_column(Numeric(8, 2), nullable=True)
    prep_fee: Mapped[float] = mapped_column(Numeric(8, 2), nullable=True)
    
    # Pricing targets  
    target_buy_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)         # Max buy price for target ROI
    breakeven_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)          # Breakeven buy price
    
    # Velocity analysis (0-100 score)
    velocity_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True, index=True)
    rank_percentile_30d: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)       # BSR percentile trend
    rank_drops_30d: Mapped[int] = mapped_column(Integer, nullable=True)                  # Number of BSR improvements  
    buybox_uptime_30d: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)         # % time buybox available
    offers_volatility: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)         # Price volatility indicator
    
    # Risk assessment
    demand_consistency: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)        # Demand pattern stability
    price_volatility: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)          # Price variation coefficient
    competition_level: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)         # Number of active sellers
    
    # Configuration used (uses JSONB on PostgreSQL, JSON on SQLite)
    fee_config_used: Mapped[dict] = mapped_column(JSONType, nullable=True)                   # Fee configuration snapshot
    calculation_params: Mapped[dict] = mapped_column(JSONType, nullable=True)                # Calculation parameters used
    
    # Additional timestamp and version
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    calculation_version: Mapped[str] = mapped_column(String(10), default="1.0")
    
    # Relationships
    product = relationship("KeepaProduct", back_populates="calc_metrics") 
    snapshot = relationship("KeepaSnapshot")
    
    def __repr__(self):
        return f"<CalcMetrics(asin='{self.product.asin if self.product else 'unknown'}', roi={self.roi_percentage}%, velocity={self.velocity_score})>"


class IdentifierResolutionLog(Base):
    """
    Log of identifier resolution attempts (ISBN -> ASIN).
    
    Helps track success rates and avoid repeated failed lookups.
    """
    __tablename__ = "identifier_resolution_log"
    
    # Original identifier info
    original_identifier: Mapped[str] = mapped_column(String(20), index=True)
    identifier_type: Mapped[str] = mapped_column(String(10))  # "isbn10", "isbn13", "asin"
    
    # Resolution result
    resolved_asin: Mapped[str] = mapped_column(String(10), nullable=True, index=True)
    resolution_status: Mapped[str] = mapped_column(String(20))  # "success", "not_found", "error"
    
    # Keepa API response details
    keepa_product_code: Mapped[int] = mapped_column(Integer, nullable=True)  # Keepa's internal product code
    keepa_domain: Mapped[int] = mapped_column(Integer, default=1)
    
    # Error details (if any)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Additional timestamp
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<IdentifierResolutionLog(identifier='{self.original_identifier}' -> asin='{self.resolved_asin}', status='{self.resolution_status}')>"