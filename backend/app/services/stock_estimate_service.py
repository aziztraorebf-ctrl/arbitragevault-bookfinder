"""
Stock Estimate Service
Simple stock availability estimation based on FBA offers count
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.stock_estimate import StockEstimateCache
from app.services.keepa_service import KeepaService
import logging

logger = logging.getLogger(__name__)


class StockEstimateService:
    """Service for estimating stock availability from marketplace data"""
    
    def __init__(self, db: AsyncSession, keepa_service: KeepaService):
        self.db = db
        self.keepa_service = keepa_service
        
        # Configuration - ultra simple defaults
        self.config = {
            "ttl_hours": 24,
            "price_band_pct": 0.15,  # ±15% around target price
            "max_estimate": 10,
            "timeout_seconds": 4
        }
    
    async def get_stock_estimate(self, asin: str, price_target: Optional[float] = None) -> Dict[str, Any]:
        """
        Get stock estimate for single ASIN
        Cache-first approach with 24h TTL
        """
        try:
            # 1. Check cache first
            cached = await self._get_cached_estimate(asin)
            if cached and not cached.is_expired():
                logger.info(f"Stock estimate cache hit for {asin}")
                return cached.to_dict(source="cache")
            
            # 2. Cache miss - get fresh data from Keepa
            logger.info(f"Stock estimate cache miss for {asin}, fetching from Keepa")
            offers_data = await self._fetch_keepa_offers(asin)
            
            if not offers_data:
                # No offers data available
                return self._create_empty_estimate(asin)
            
            # 3. Calculate estimate using simple heuristic
            estimate_result = self._calculate_simple_estimate(offers_data, price_target)
            
            # 4. Cache result
            cache_entry = await self._cache_estimate(asin, estimate_result)
            
            return cache_entry.to_dict(source="fresh")
            
        except Exception as e:
            logger.error(f"Error getting stock estimate for {asin}: {e}")
            # Try returning cached data even if expired
            cached = await self._get_cached_estimate(asin)
            if cached:
                return cached.to_dict(source="cache_fallback")
            
            # Last resort - return error state
            return {
                "asin": asin,
                "units_available_estimate": 0,
                "offers_fba": 0,
                "offers_mfn": 0,
                "source": "error",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "ttl": 0,
                "error": str(e)
            }
    
    async def _get_cached_estimate(self, asin: str) -> Optional[StockEstimateCache]:
        """Retrieve cached estimate from database"""
        result = await self.db.execute(
            select(StockEstimateCache).where(StockEstimateCache.asin == asin)
        )
        return result.scalar_one_or_none()
    
    async def _fetch_keepa_offers(self, asin: str) -> Optional[Dict]:
        """Fetch offers data from Keepa API"""
        try:
            # Use existing Keepa service to get product data with offers
            product_data = await self.keepa_service.get_product_data(asin, include_offers=True)
            
            if not product_data or 'offers' not in product_data:
                logger.warning(f"No offers data for {asin}")
                return None
                
            return product_data.get('offers', [])
            
        except Exception as e:
            logger.error(f"Failed to fetch Keepa offers for {asin}: {e}")
            return None
    
    def _calculate_simple_estimate(self, offers_data: List[Dict], price_target: Optional[float]) -> Dict[str, Any]:
        """
        Ultra-simple heuristic v1:
        Count FBA offers in reasonable price range
        """
        try:
            if not offers_data:
                return {"units": 0, "fba_count": 0, "mfn_count": 0}
            
            # Count FBA vs MFN offers
            fba_offers = [offer for offer in offers_data if offer.get('isFBA', False)]
            mfn_offers = [offer for offer in offers_data if not offer.get('isFBA', False)]
            
            # If we have price target, filter by price range
            if price_target and price_target > 0:
                price_low = price_target * (1 - self.config["price_band_pct"])
                price_high = price_target * (1 + self.config["price_band_pct"])
                
                fba_offers = [
                    offer for offer in fba_offers 
                    if price_low <= offer.get('price', 0) <= price_high
                ]
            
            fba_count = len(fba_offers)
            mfn_count = len(mfn_offers)
            
            # Ultra-simple estimate: min(max_estimate, max(1, fba_count))
            # At least 1 if any FBA offers exist, capped at max_estimate
            units_estimate = min(
                self.config["max_estimate"],
                max(1 if fba_count > 0 else 0, fba_count)
            )
            
            logger.info(f"Stock estimate calculated: {units_estimate} units ({fba_count} FBA, {mfn_count} MFN)")
            
            return {
                "units": units_estimate,
                "fba_count": fba_count,
                "mfn_count": mfn_count,
                "source_meta": {
                    "total_offers": len(offers_data),
                    "price_target": price_target,
                    "price_band_pct": self.config["price_band_pct"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating stock estimate: {e}")
            return {"units": 0, "fba_count": 0, "mfn_count": 0}
    
    async def _cache_estimate(self, asin: str, estimate_result: Dict[str, Any]) -> StockEstimateCache:
        """Store estimate in cache"""
        try:
            # Upsert cache entry
            result = await self.db.execute(
                select(StockEstimateCache).where(StockEstimateCache.asin == asin)
            )
            cache_entry = result.scalar_one_or_none()
            
            if cache_entry:
                # Update existing
                cache_entry.units_available_estimate = estimate_result["units"]
                cache_entry.offers_fba = estimate_result["fba_count"]
                cache_entry.offers_mfn = estimate_result["mfn_count"]
                cache_entry.updated_at = datetime.utcnow()
                cache_entry.ttl_seconds = self.config["ttl_hours"] * 3600
                cache_entry.source_meta = estimate_result.get("source_meta")
            else:
                # Create new
                cache_entry = StockEstimateCache(
                    asin=asin,
                    units_available_estimate=estimate_result["units"],
                    offers_fba=estimate_result["fba_count"],
                    offers_mfn=estimate_result["mfn_count"],
                    updated_at=datetime.utcnow(),
                    ttl_seconds=self.config["ttl_hours"] * 3600,
                    source_meta=estimate_result.get("source_meta")
                )
                self.db.add(cache_entry)
            
            await self.db.commit()
            await self.db.refresh(cache_entry)
            
            return cache_entry
            
        except Exception as e:
            logger.error(f"Error caching stock estimate for {asin}: {e}")
            await self.db.rollback()
            raise
    
    def _create_empty_estimate(self, asin: str) -> Dict[str, Any]:
        """Create empty estimate when no data available"""
        return {
            "asin": asin,
            "units_available_estimate": 0,
            "offers_fba": 0,
            "offers_mfn": 0,
            "source": "no_data",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "ttl": 0
        }