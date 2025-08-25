"""
Stock Estimate Cache Models
Simple cache for stock availability estimates
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON
from app.core.database import Base


class StockEstimateCache(Base):
    """Cache table for stock availability estimates"""
    __tablename__ = "stock_estimate_cache"
    
    # Primary key
    asin = Column(String(20), primary_key=True, index=True)
    
    # Estimate results
    units_available_estimate = Column(Integer, nullable=False, default=0)
    offers_fba = Column(Integer, nullable=False, default=0)
    offers_mfn = Column(Integer, nullable=False, default=0)
    
    # Cache metadata
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ttl_seconds = Column(Integer, nullable=False, default=86400)  # 24h default
    
    # Optional metadata for debugging/optimization
    source_meta = Column(JSON, nullable=True)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if not self.updated_at:
            return True
        
        from datetime import datetime, timedelta
        expiry_time = self.updated_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry_time
    
    def to_dict(self, source: str = "cache") -> dict:
        """Convert to API response dict"""
        return {
            "asin": self.asin,
            "units_available_estimate": self.units_available_estimate,
            "offers_fba": self.offers_fba,
            "offers_mfn": self.offers_mfn,
            "source": source,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
            "ttl": self.ttl_seconds - int((datetime.utcnow() - self.updated_at).total_seconds()) if self.updated_at else 0
        }