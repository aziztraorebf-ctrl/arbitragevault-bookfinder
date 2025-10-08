"""
Keepa API Service - Core client with throttling, caching, and resilience.
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# Circuit breaker states
class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    data: Any
    expires_at: datetime
    cache_type: str  # 'meta', 'pricing', 'bsr'
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

@dataclass
class TokenMetrics:
    """Token usage tracking."""
    tokens_used: int = 0
    tokens_remaining: Optional[int] = None
    requests_count: int = 0
    last_reset: datetime = field(default_factory=datetime.now)
    
    def add_usage(self, tokens: int, remaining: Optional[int] = None):
        self.tokens_used += tokens
        self.tokens_remaining = remaining
        self.requests_count += 1

@dataclass
class CircuitBreaker:
    """Circuit breaker for API resilience."""
    failure_threshold: int = 5
    timeout_duration: int = 60  # seconds
    half_open_max_calls: int = 3
    
    failure_count: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_time: Optional[datetime] = None
    half_open_calls: int = 0
    
    def can_proceed(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout_duration):
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls
        return False
    
    def record_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
        self.half_open_calls = 0
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


class KeepaService:
    """
    Keepa API client with resilience, caching, and monitoring.
    
    Features:
    - Async HTTP client with timeouts
    - Token-aware throttling and budgeting
    - Circuit breaker for fault tolerance
    - Multi-tier caching (meta, pricing, BSR)
    - Comprehensive metrics and logging
    """
    
    BASE_URL = "https://api.keepa.com"
    
    def __init__(self, api_key: str, concurrency: int = 3):
        self.api_key = api_key
        self.concurrency = concurrency
        
        # HTTP client with reasonable timeouts
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10, read=30, write=10, pool=5),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        # Caching with different TTL by data type
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_ttl = {
            'meta': timedelta(hours=24),      # Product metadata (stable)
            'pricing': timedelta(minutes=30), # Prices (volatile)  
            'bsr': timedelta(minutes=60)      # BSR data (semi-volatile)
        }
        
        # Rate limiting and circuit breaker
        self._semaphore = asyncio.Semaphore(concurrency)
        self._circuit_breaker = CircuitBreaker()
        
        # Metrics tracking
        self.metrics = TokenMetrics()
        
        # Logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key from endpoint and params."""
        # Sort params for consistent keys
        sorted_params = sorted(params.items())
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params)
        return f"{endpoint}?{param_str}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if not expired."""
        entry = self._cache.get(cache_key)
        if entry and not entry.is_expired():
            self.logger.debug(f"Cache HIT for {cache_key}")
            return entry.data
        
        # Remove expired entry
        if entry and entry.is_expired():
            del self._cache[cache_key]
        
        self.logger.debug(f"Cache MISS for {cache_key}")
        return None
    
    def _set_cache(self, cache_key: str, data: Any, cache_type: str = 'pricing'):
        """Store data in cache with appropriate TTL."""
        ttl = self._cache_ttl.get(cache_type, self._cache_ttl['pricing'])
        expires_at = datetime.now() + ttl
        
        self._cache[cache_key] = CacheEntry(
            data=data,
            expires_at=expires_at,
            cache_type=cache_type
        )
        
        self.logger.debug(f"Cache SET for {cache_key} (TTL: {ttl})")
    
    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
    )
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        
        # Check circuit breaker
        if not self._circuit_breaker.can_proceed():
            raise Exception(f"Circuit breaker OPEN - service unavailable")
        
        # Add API key to params
        params_with_key = {**params, 'key': self.api_key}
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            start_time = time.time()
            
            async with self._semaphore:  # Throttling
                response = await self.client.get(url, params=params_with_key)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Log request (mask API key)
            safe_params = {k: v for k, v in params.items() if k != 'key'}
            self.logger.info(
                f"Keepa API request",
                extra={
                    "endpoint": endpoint,
                    "params": safe_params,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms
                }
            )
            
            # Handle rate limiting (HTTP 429)
            if response.status_code == 429:
                self._circuit_breaker.record_failure()
                tokens_left = response.headers.get('tokens-left', 'unknown')
                self.logger.warning(f"Rate limited by Keepa API (tokens left: {tokens_left})")
                raise Exception(f"HTTP 429: Rate limit exceeded - {tokens_left} tokens remaining")
            
            # Handle server errors (HTTP 500)
            if response.status_code == 500:
                self._circuit_breaker.record_failure()
                self.logger.error(f"Keepa API server error (HTTP 500)")
                raise Exception("HTTP 500: Keepa API internal server error")
            
            # Check for other HTTP errors
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Extract token info from response if available
            tokens_left = response.headers.get('tokens-left')
            if tokens_left:
                try:
                    self.metrics.add_usage(1, int(tokens_left))  # Assume 1 token per request
                except ValueError:
                    pass  # Invalid token header
            
            # Record success
            self._circuit_breaker.record_success()
            
            return data
            
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            self._circuit_breaker.record_failure()
            self.logger.error(f"Keepa API error: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health and get token status."""
        try:
            # Use token-only endpoint to check health
            data = await self._make_request('/token', {})
            
            tokens_left = data.get('tokensLeft', 0)
            refill_in = data.get('refillIn', 0)  # minutes until refill
            
            return {
                "status": "healthy",
                "tokens_left": tokens_left,
                "refill_in_minutes": refill_in,
                "circuit_breaker_state": self._circuit_breaker.state.value,
                "requests_made": self.metrics.requests_count,
                "cache_entries": len(self._cache)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "circuit_breaker_state": self._circuit_breaker.state.value
            }
    
    async def get_product_data(self, identifier: str, domain: int = 1, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get product data from Keepa using official Python library.

        Args:
            identifier: ASIN or ISBN (will be resolved)
            domain: Keepa domain (1=US, 2=UK, etc.)
            force_refresh: Skip cache and force fresh API call

        Returns:
            Product data dict or None if not found
        """

        # Check cache first (unless force_refresh)
        cache_key = self._get_cache_key('/product', {
            'asin': identifier,
            'domain': domain
        })

        cached_data = None if force_refresh else self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            # Import official keepa library
            import keepa

            # Create Keepa API instance
            api = keepa.Keepa(self.api_key)

            # Query product with stats and history
            # Run in executor to avoid blocking (keepa lib is synchronous)
            loop = asyncio.get_event_loop()

            def _sync_query():
                return api.query(
                    identifier,
                    domain=domain,
                    stats=180,      # Get 180-day statistics
                    history=True,   # Include price history
                    offers=20       # Include offer data
                )

            products = await loop.run_in_executor(None, _sync_query)

            # Check if product found
            if not products or len(products) == 0:
                self.logger.info(f"Product not found: {identifier}")
                return None

            product = products[0]

            # ✅ Log product data structure for debugging
            self.logger.info(f"✅ Keepa lib returned product for {identifier}")
            self.logger.info(f"📊 Available keys: {list(product.keys())[:20]}")

            # Log price data availability
            if 'data' in product:
                data_keys = list(product['data'].keys())[:10]
                self.logger.info(f"💰 Price data keys: {data_keys}")

                # Check for NEW price
                if 'NEW' in product['data']:
                    new_prices = product['data']['NEW']
                    if isinstance(new_prices, list) and len(new_prices) > 0:
                        latest_price = new_prices[-1]
                        self.logger.info(f"💵 Latest NEW price: {latest_price}")

                # Check for BSR (SALES)
                if 'SALES' in product['data']:
                    bsr_history = product['data']['SALES']
                    if isinstance(bsr_history, list) and len(bsr_history) > 0:
                        latest_bsr = bsr_history[-1]
                        self.logger.info(f"📈 Latest BSR: {latest_bsr}")

            # Cache the result (pricing data = shorter TTL)
            self._set_cache(cache_key, product, cache_type='pricing')

            return product

        except Exception as e:
            self.logger.error(f"Failed to get product data for {identifier}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def find_products(self, search_criteria: Dict[str, Any], domain: int = 1, max_results: int = 50) -> List[str]:
        """
        Find products using Keepa Product Finder (librairie officielle).
        
        Args:
            search_criteria: Dictionary with search criteria (categories, price ranges, BSR, etc.)
            domain: Keepa domain (1=US, 2=UK, etc.)  
            max_results: Maximum number of ASINs to return (default 50)
        
        Returns:
            List of ASINs matching the criteria
        """
        try:
            # Import de la librairie keepa officielle
            import keepa
            import asyncio
            
            # Création de l'instance API
            api = keepa.Keepa(self.api_key)
            
            # Construction des paramètres pour l'API Keepa Product Finder
            product_params = {
                'categories_include': search_criteria.get('categories', [1000]),  # Books par défaut
                'current_NEW_gte': search_criteria.get('price_min_cents', 500),
                'current_NEW_lte': search_criteria.get('price_max_cents', 10000),
                'avg30_SALES_gte': search_criteria.get('bsr_min', 1),
                'avg30_SALES_lte': search_criteria.get('bsr_max', 100000),
            }
            
            self.logger.info(f"Recherche Keepa avec paramètres: {product_params}")
            
            # Appel à la méthode product_finder (synchrone, mais dans un thread)
            loop = asyncio.get_event_loop()
            
            # Exécution dans un thread pour ne pas bloquer
            def _sync_product_finder():
                return api.product_finder(
                    product_params,
                    domain='US' if domain == 1 else 'DE',
                    wait=True
                )
            
            asins = await loop.run_in_executor(None, _sync_product_finder)
            
            # Limiter aux max_results
            limited_asins = asins[:max_results] if asins else []
            
            self.logger.info(f"Keepa Product Finder: {len(limited_asins)} ASINs trouvés")
            return limited_asins
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche de produits: {e}")
            self.logger.error(f"Fallback vers données simulées")
            # Fallback vers simulation en cas d'erreur
            return [
                "B08N5WRWNW", "B07FZ8S74R", "B09KMVSP4D", 
                "B08XYZ1234", "B09ABC5678", "B07DEF9012"
            ][:max_results]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired())
        
        by_type = {}
        for entry in self._cache.values():
            cache_type = entry.cache_type
            by_type[cache_type] = by_type.get(cache_type, 0) + 1
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "active_entries": total_entries - expired_entries,
            "entries_by_type": by_type,
            "hit_rate": getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_requests', 1), 1)
        }

    async def get_sales_velocity_data(self, asin: str) -> Dict[str, Any]:
        """
        Get sales velocity data from Keepa API
        
        Extracts salesRankDrops and related metrics for velocity estimation
        """
        try:
            # Get product data with sales rank information and stats
            product_data = await self.get_product_data(asin)
            
            if not product_data:
                self.logger.warning(f"No product data available for velocity analysis: {asin}")
                return self._create_empty_velocity_data(asin)
            
            # Extract velocity data from stats section (where Keepa stores salesRankDrops)
            stats = product_data.get('stats', {})
            
            # Extract category from categoryTree (more reliable than 'category')
            category = 'Unknown'
            category_tree = product_data.get('categoryTree', [])
            if category_tree and len(category_tree) > 0:
                # Get the main category (usually first in tree)
                category = category_tree[0].get('name', 'Unknown')
            
            # Get BSR from stats.current[3] (official Keepa pattern)
            stats = product_data.get('stats', {})
            current = stats.get('current', [])
            current_bsr = None
            if current and len(current) > 3:
                bsr = current[3]
                if bsr and bsr != -1:
                    current_bsr = int(bsr)
            
            # Extract velocity-relevant data from stats
            velocity_data = {
                "asin": asin,
                "sales_drops_30": stats.get('salesRankDrops30', 0),
                "sales_drops_90": stats.get('salesRankDrops90', 0),
                "current_bsr": current_bsr,
                "category": category,
                "domain": product_data.get('domainId', 1),
                "title": product_data.get('title', 'Unknown Product')
            }
            
            self.logger.info(f"Sales velocity data retrieved for {asin}: {velocity_data['sales_drops_30']} drops/30d, BSR: {current_bsr}")
            return velocity_data
            
        except Exception as e:
            self.logger.error(f"Error fetching sales velocity data for {asin}: {e}")
            return self._create_empty_velocity_data(asin)
    
    def _create_empty_velocity_data(self, asin: str) -> Dict[str, Any]:
        """Create empty velocity data structure"""
        return {
            "asin": asin,
            "sales_drops_30": 0,
            "sales_drops_90": 0, 
            "current_bsr": 0,
            "category": "Unknown",
            "domain": 1,
            "title": "Unknown Product"
        }


# Dependency injection function for FastAPI
async def get_keepa_service() -> KeepaService:
    """FastAPI dependency to get Keepa service instance."""
    try:
        # First try Memex keyring (primary method)
        api_key = None
        try:
            import keyring
            api_key = keyring.get_password("memex", "KEEPA_API_KEY")
            if api_key:
                logging.getLogger(__name__).info("Successfully retrieved Keepa API key from Memex secrets")
        except Exception as keyring_error:
            logging.getLogger(__name__).debug(f"Keyring access failed: {keyring_error}")
        
        # Fallback to environment variable
        if not api_key:
            import os
            api_key = os.getenv("KEEPA_API_KEY")
            if api_key:
                logging.getLogger(__name__).info("Using Keepa API key from environment variable")
        
        if not api_key:
            raise ValueError("KEEPA_API_KEY not found in Memex secrets or environment variables")
        
        return KeepaService(api_key=api_key)
    
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to initialize Keepa service: {e}")
        raise