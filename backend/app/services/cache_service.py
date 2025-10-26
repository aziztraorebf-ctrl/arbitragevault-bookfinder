"""
Cache Service - Phase 2 Jour 5

Gestion du cache PostgreSQL pour Product Finder.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.product_cache import (
    ProductDiscoveryCache,
    ProductScoringCache,
    SearchHistory
)


class CacheService:
    """
    Service de cache pour optimiser performance.

    Features:
    - Cache discovery results (24h TTL)
    - Cache scoring results (6h TTL)
    - Track search history
    - Automatic expiration
    """

    def __init__(self, db: Session):
        """Initialize cache service."""
        self.db = db

    def get_discovery_cache(
        self,
        domain: int,
        category: Optional[int] = None,
        bsr_min: Optional[int] = None,
        bsr_max: Optional[int] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None
    ) -> Optional[List[str]]:
        """
        Get cached discovery results.

        Returns ASINs if cache hit, None if miss.
        """
        # Generate cache key
        cache_key = self._generate_discovery_key(
            domain, category, bsr_min, bsr_max, price_min, price_max
        )

        # Query cache
        cache_entry = self.db.query(ProductDiscoveryCache).filter(
            and_(
                ProductDiscoveryCache.cache_key == cache_key,
                ProductDiscoveryCache.expires_at > datetime.utcnow()
            )
        ).first()

        if cache_entry:
            # Update hit count
            cache_entry.hit_count += 1
            self.db.commit()
            return cache_entry.asins

        return None

    def set_discovery_cache(
        self,
        domain: int,
        asins: List[str],
        category: Optional[int] = None,
        bsr_min: Optional[int] = None,
        bsr_max: Optional[int] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        ttl_hours: int = 24
    ) -> str:
        """
        Store discovery results in cache.

        Returns cache key.
        """
        # Generate cache key
        cache_key = self._generate_discovery_key(
            domain, category, bsr_min, bsr_max, price_min, price_max
        )

        # Check if exists
        existing = self.db.query(ProductDiscoveryCache).filter(
            ProductDiscoveryCache.cache_key == cache_key
        ).first()

        if existing:
            # Update existing
            existing.asins = asins
            existing.count = len(asins)
            existing.created_at = datetime.utcnow()
            existing.expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        else:
            # Create new
            cache_entry = ProductDiscoveryCache(
                cache_key=cache_key,
                domain=domain,
                category=category,
                bsr_min=bsr_min,
                bsr_max=bsr_max,
                price_min=price_min,
                price_max=price_max,
                asins=asins,
                count=len(asins),
                expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
            )
            self.db.add(cache_entry)

        self.db.commit()
        return cache_key

    def get_scoring_cache(self, asin: str) -> Optional[Dict[str, Any]]:
        """
        Get cached scoring results for ASIN.

        Returns scoring data if cache hit, None if miss.
        """
        cache_entry = self.db.query(ProductScoringCache).filter(
            and_(
                ProductScoringCache.asin == asin,
                ProductScoringCache.expires_at > datetime.utcnow()
            )
        ).order_by(ProductScoringCache.created_at.desc()).first()

        if cache_entry:
            return {
                "asin": cache_entry.asin,
                "title": cache_entry.title,
                "price": cache_entry.price,
                "bsr": cache_entry.bsr,
                "roi_percent": cache_entry.roi_percent,
                "velocity_score": cache_entry.velocity_score,
                "recommendation": cache_entry.recommendation
            }

        return None

    def set_scoring_cache(
        self,
        asin: str,
        title: str,
        price: float,
        bsr: int,
        roi_percent: float,
        velocity_score: float,
        recommendation: str,
        keepa_data: Optional[Dict] = None,
        config_hash: Optional[str] = None,
        ttl_hours: int = 6
    ) -> int:
        """
        Store scoring results in cache.

        Returns cache entry ID.
        """
        # Create new entry (always append, don't update)
        cache_entry = ProductScoringCache(
            asin=asin,
            title=title[:500] if title else None,  # Truncate long titles
            price=price,
            bsr=bsr,
            roi_percent=roi_percent,
            velocity_score=velocity_score,
            recommendation=recommendation,
            keepa_data=keepa_data,
            config_hash=config_hash,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
        )

        self.db.add(cache_entry)
        self.db.commit()

        return cache_entry.id

    def record_search(
        self,
        search_params: Dict[str, Any],
        search_type: str,
        results_count: int,
        api_calls: int = 1,
        cache_hits: int = 0,
        response_time_ms: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> int:
        """
        Record search for analytics.

        Returns history entry ID.
        """
        # Calculate averages if scoring results
        avg_roi = None
        avg_velocity = None

        if search_type == "scoring" and "products" in search_params:
            products = search_params["products"]
            if products:
                roi_values = [p.get("roi_percent", 0) for p in products]
                velocity_values = [p.get("velocity_score", 0) for p in products]
                avg_roi = sum(roi_values) / len(roi_values) if roi_values else None
                avg_velocity = sum(velocity_values) / len(velocity_values) if velocity_values else None

        # Create history entry
        history = SearchHistory(
            search_params=search_params,
            search_type=search_type,
            results_count=results_count,
            avg_roi=avg_roi,
            avg_velocity=avg_velocity,
            api_calls_made=api_calls,
            cache_hits=cache_hits,
            response_time_ms=response_time_ms,
            user_id=user_id
        )

        self.db.add(history)
        self.db.commit()

        return history.id

    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.

        Returns number of entries deleted.
        """
        count = 0

        # Cleanup discovery cache
        expired_discovery = self.db.query(ProductDiscoveryCache).filter(
            ProductDiscoveryCache.expires_at < datetime.utcnow()
        ).all()

        for entry in expired_discovery:
            self.db.delete(entry)
            count += 1

        # Cleanup scoring cache
        expired_scoring = self.db.query(ProductScoringCache).filter(
            ProductScoringCache.expires_at < datetime.utcnow()
        ).all()

        for entry in expired_scoring:
            self.db.delete(entry)
            count += 1

        self.db.commit()
        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns usage metrics.
        """
        discovery_total = self.db.query(ProductDiscoveryCache).count()
        discovery_active = self.db.query(ProductDiscoveryCache).filter(
            ProductDiscoveryCache.expires_at > datetime.utcnow()
        ).count()

        scoring_total = self.db.query(ProductScoringCache).count()
        scoring_active = self.db.query(ProductScoringCache).filter(
            ProductScoringCache.expires_at > datetime.utcnow()
        ).count()

        search_count = self.db.query(SearchHistory).count()

        # Calculate hit rate from search history
        recent_searches = self.db.query(SearchHistory).limit(100).all()
        total_api_calls = sum(s.api_calls_made for s in recent_searches)
        total_cache_hits = sum(s.cache_hits for s in recent_searches)
        hit_rate = (total_cache_hits / (total_api_calls + total_cache_hits) * 100) if (total_api_calls + total_cache_hits) > 0 else 0

        return {
            "discovery_cache": {
                "total": discovery_total,
                "active": discovery_active,
                "expired": discovery_total - discovery_active
            },
            "scoring_cache": {
                "total": scoring_total,
                "active": scoring_active,
                "expired": scoring_total - scoring_active
            },
            "search_history": {
                "total": search_count
            },
            "performance": {
                "hit_rate": round(hit_rate, 2),
                "api_calls_saved": total_cache_hits
            }
        }

    def _generate_discovery_key(
        self,
        domain: int,
        category: Optional[int],
        bsr_min: Optional[int],
        bsr_max: Optional[int],
        price_min: Optional[float],
        price_max: Optional[float]
    ) -> str:
        """Generate deterministic cache key."""
        params = {
            "domain": domain,
            "category": category,
            "bsr_min": bsr_min,
            "bsr_max": bsr_max,
            "price_min": price_min,
            "price_max": price_max
        }

        # Sort keys for consistency
        sorted_params = json.dumps(params, sort_keys=True)

        # Generate hash
        return hashlib.md5(sorted_params.encode()).hexdigest()