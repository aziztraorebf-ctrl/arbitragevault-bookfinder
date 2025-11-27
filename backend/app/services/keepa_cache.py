"""
Keepa Service - Cache Management
=================================
Multi-tier caching system for Keepa API responses.

Separated from keepa_service.py for SRP compliance.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from .keepa_models import CacheEntry


logger = logging.getLogger(__name__)


class KeepaCache:
    """
    Multi-tier cache for Keepa API responses.

    Features:
    - Different TTLs by data type (meta, pricing, bsr)
    - Quick cache for repeated test calls
    - Automatic expiry cleanup
    - Cache statistics tracking
    """

    def __init__(self):
        # Main cache with different TTL by data type
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_ttl = {
            'meta': timedelta(hours=24),      # Product metadata (stable)
            'pricing': timedelta(minutes=30), # Prices (volatile)
            'bsr': timedelta(minutes=60)      # BSR data (semi-volatile)
        }

        # Quick cache for repeated test calls (10 min TTL)
        self._quick_cache: Dict[str, Tuple[Any, datetime]] = {}
        self._quick_cache_ttl = timedelta(minutes=10)

        # Statistics tracking
        self._cache_hits = 0
        self._cache_misses = 0

    @property
    def cache(self) -> Dict[str, CacheEntry]:
        """Access to underlying cache dict."""
        return self._cache

    def get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key from endpoint and params."""
        # Sort params for consistent keys
        sorted_params = sorted(params.items())
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params)
        return f"{endpoint}?{param_str}"

    def get(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if not expired."""
        entry = self._cache.get(cache_key)
        if entry and not entry.is_expired():
            logger.debug(f"Cache HIT for {cache_key}")
            self._cache_hits += 1
            return entry.data

        # Remove expired entry
        if entry and entry.is_expired():
            del self._cache[cache_key]

        logger.debug(f"Cache MISS for {cache_key}")
        self._cache_misses += 1
        return None

    def set(self, cache_key: str, data: Any, cache_type: str = 'pricing'):
        """Store data in cache with appropriate TTL."""
        ttl = self._cache_ttl.get(cache_type, self._cache_ttl['pricing'])
        expires_at = datetime.now() + ttl

        self._cache[cache_key] = CacheEntry(
            data=data,
            expires_at=expires_at,
            cache_type=cache_type
        )

        logger.debug(f"Cache SET for {cache_key} (TTL: {ttl})")

    def get_ttl(self, cache_type: str) -> timedelta:
        """Get TTL for a specific cache type."""
        return self._cache_ttl.get(cache_type, self._cache_ttl['pricing'])

    # Quick cache methods
    def get_quick(self, identifier: str) -> Optional[Any]:
        """Get from quick cache (ultra-short TTL for testing)."""
        cache_key = f"quick:product:{identifier}"

        if cache_key in self._quick_cache:
            cached_data, timestamp = self._quick_cache[cache_key]
            if datetime.now() - timestamp < self._quick_cache_ttl:
                logger.debug(f"Quick cache HIT for {identifier}")
                return cached_data

        return None

    def set_quick(self, identifier: str, data: Any):
        """Store in quick cache with auto-cleanup."""
        cache_key = f"quick:product:{identifier}"
        self._quick_cache[cache_key] = (data, datetime.now())

        # Simple GC - clean if too many entries
        if len(self._quick_cache) > 100:
            cutoff = datetime.now() - self._quick_cache_ttl
            self._quick_cache = {
                k: v for k, v in self._quick_cache.items()
                if v[1] > cutoff
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired())

        by_type = {}
        for entry in self._cache.values():
            cache_type = entry.cache_type
            by_type[cache_type] = by_type.get(cache_type, 0) + 1

        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / max(total_requests, 1)

        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "active_entries": total_entries - expired_entries,
            "entries_by_type": by_type,
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate": hit_rate
        }

    def clear(self):
        """Clear all caches."""
        self._cache.clear()
        self._quick_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0


# Backward compatibility exports
__all__ = [
    'KeepaCache',
]
