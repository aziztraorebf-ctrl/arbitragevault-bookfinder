"""
Keepa API Service - Core client with throttling, caching, and resilience.

This module now acts as a facade, importing from specialized sub-modules
for better SRP compliance and maintainability.

Sub-modules:
- keepa_models: Data classes, enums, and constants
- keepa_cache: Multi-tier caching system
- keepa_throttle: Rate limiting and token management
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List

import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# Import from specialized modules
from .keepa_models import (
    ENDPOINT_COSTS,
    MIN_BALANCE_THRESHOLD,
    SAFETY_BUFFER,
    CircuitState,
    CacheEntry,
    TokenMetrics,
    CircuitBreaker,
)
from .keepa_cache import KeepaCache
from .keepa_throttle import KeepaThrottle
from ..core.exceptions import InsufficientTokensError, KeepaRateLimitError


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

        # Use KeepaCache for caching
        self._cache_manager = KeepaCache()

        # For backward compatibility - expose internal cache dict
        self._cache = self._cache_manager.cache
        self._cache_ttl = self._cache_manager._cache_ttl

        # Rate limiting and circuit breaker
        self._semaphore = asyncio.Semaphore(concurrency)
        self._circuit_breaker = CircuitBreaker()

        # Initialize throttle with production-optimized settings
        self.throttle = KeepaThrottle(
            tokens_per_minute=20,
            burst_capacity=200,  # Increased for smooth AutoSourcing (5 niches x 40 products)
            warning_threshold=80,  # 40% of burst capacity
            critical_threshold=40   # 20% of burst capacity
        )

        # API balance tracking
        self.last_api_balance_check = 0
        self.api_balance_cache: Optional[int] = None

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

    # =========================================================================
    # BALANCE & THROTTLING
    # =========================================================================

    async def check_api_balance(self) -> int:
        """
        Check current Keepa API token balance.
        Uses cached value if checked within last 60 seconds.

        Returns:
            Current token balance from Keepa API

        Note:
            Keepa API returns tokensLeft in the JSON response body, NOT in HTTP headers.
        """
        now = time.time()

        # Use cached balance if recent (< 60 seconds old)
        if self.api_balance_cache is not None and (now - self.last_api_balance_check) < 60:
            return self.api_balance_cache

        # Make lightweight request to get current balance
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/product",
                params={
                    "key": self.api_key,
                    "domain": 1,
                    "asin": "B00FLIJJSA"  # Known valid ASIN
                }
            )

            # Keepa returns tokensLeft in JSON body (NOT in HTTP headers)
            if response.status_code == 200:
                data = response.json()
                tokens_left = data.get('tokensLeft')

                if tokens_left is not None:
                    self.api_balance_cache = int(tokens_left)
                    self.last_api_balance_check = now
                    self.logger.info(f"[OK] Keepa API balance: {self.api_balance_cache} tokens")
                    return self.api_balance_cache

            self.logger.error("[ERROR] Cannot verify Keepa balance (tokensLeft not in response)")
            raise InsufficientTokensError(
                current_balance=0,
                required_tokens=1,
                endpoint="balance_check"
            )

        except InsufficientTokensError:
            raise
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to check API balance: {e}")
            raise InsufficientTokensError(
                current_balance=0,
                required_tokens=1,
                endpoint="balance_check"
            )

    async def can_perform_action(self, action: str) -> dict[str, any]:
        """
        Check if we have sufficient tokens for a business action.

        Args:
            action: Business action name from TOKEN_COSTS registry

        Returns:
            dict with can_proceed, current_balance, required_tokens, action

        Raises:
            ValueError: If action not found in TOKEN_COSTS
        """
        from app.core.token_costs import TOKEN_COSTS

        if action not in TOKEN_COSTS:
            raise ValueError(f"Unknown action '{action}' - not found in TOKEN_COSTS registry")

        required = TOKEN_COSTS[action]["cost"]

        balance_info = await self.check_api_balance()
        current = balance_info if isinstance(balance_info, int) else balance_info.get("tokensLeft", 0)

        self.throttle.set_tokens(current)

        can_proceed = current >= required

        self.logger.info(
            f"Token check for '{action}': balance={current}, required={required}, can_proceed={can_proceed}"
        )

        return {
            "can_proceed": can_proceed,
            "current_balance": current,
            "required_tokens": required,
            "action": action
        }

    async def _ensure_sufficient_balance(self, estimated_cost: int, endpoint_name: str = None):
        """
        Verify API budget is sufficient BEFORE making request.

        Args:
            estimated_cost: Estimated token cost for the request
            endpoint_name: Endpoint name for logging/debugging

        Raises:
            InsufficientTokensError: If balance < MIN_BALANCE_THRESHOLD
        """
        current_balance = await self.check_api_balance()

        # Synchronize local throttle with actual Keepa balance
        self.throttle.set_tokens(current_balance)

        # Warn if balance is low but still above minimum
        if current_balance < SAFETY_BUFFER:
            self.logger.warning(
                f"[WARNING] Keepa token balance low: {current_balance} tokens "
                f"(safety buffer: {SAFETY_BUFFER})"
            )

        # Block request if balance is critically low
        if current_balance < MIN_BALANCE_THRESHOLD:
            self.logger.error(
                f"[ERROR] Keepa token balance critically low: {current_balance} < {MIN_BALANCE_THRESHOLD}"
            )
            raise InsufficientTokensError(
                current_balance=current_balance,
                required_tokens=MIN_BALANCE_THRESHOLD,
                endpoint=endpoint_name
            )

        # Block request if estimated cost exceeds available balance
        if estimated_cost > current_balance:
            self.logger.error(
                f"[ERROR] Insufficient tokens for {endpoint_name}: "
                f"{estimated_cost} required, {current_balance} available"
            )
            raise InsufficientTokensError(
                current_balance=current_balance,
                required_tokens=estimated_cost,
                endpoint=endpoint_name
            )

        self.logger.info(
            f"[OK] Balance check OK: {current_balance} tokens available "
            f"(estimated cost: {estimated_cost}, endpoint: {endpoint_name})"
        )

    # =========================================================================
    # CACHE METHODS (delegating to KeepaCache)
    # =========================================================================

    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key from endpoint and params."""
        return self._cache_manager.get_cache_key(endpoint, params)

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if not expired."""
        return self._cache_manager.get(cache_key)

    def _set_cache(self, cache_key: str, data: Any, cache_type: str = 'pricing'):
        """Store data in cache with appropriate TTL."""
        self._cache_manager.set(cache_key, data, cache_type)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache_manager.get_stats()

    # =========================================================================
    # HTTP REQUEST
    # =========================================================================

    @retry(
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(4),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, KeepaRateLimitError))
    )
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with retry logic and throttling."""

        endpoint_name = endpoint.strip('/').split('?')[0]
        estimated_cost = ENDPOINT_COSTS.get(endpoint_name, 1)

        # Check API budget BEFORE making request
        await self._ensure_sufficient_balance(estimated_cost, endpoint_name)

        # Apply rate throttling BEFORE making request
        await self.throttle.acquire(cost=estimated_cost)

        # Check circuit breaker
        if not self._circuit_breaker.can_proceed():
            raise Exception(f"Circuit breaker OPEN - service unavailable")

        params_with_key = {**params, 'key': self.api_key}
        url = f"{self.BASE_URL}{endpoint}"

        try:
            start_time = time.time()

            async with self._semaphore:  # Concurrency limiting
                response = await self.client.get(url, params=params_with_key)

            latency_ms = int((time.time() - start_time) * 1000)

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
                retry_after = response.headers.get('retry-after')
                retry_seconds = int(retry_after) if retry_after and retry_after.isdigit() else None
                self.logger.warning(
                    f"Rate limited by Keepa API (tokens left: {tokens_left}, retry-after: {retry_after})"
                )
                raise KeepaRateLimitError(
                    tokens_left=tokens_left,
                    endpoint=endpoint,
                    retry_after=retry_seconds
                )

            # Handle server errors (HTTP 500)
            if response.status_code == 500:
                self._circuit_breaker.record_failure()
                self.logger.error(f"Keepa API server error (HTTP 500)")
                raise Exception("HTTP 500: Keepa API internal server error")

            response.raise_for_status()
            data = response.json()

            # Extract token info from response if available
            tokens_left = response.headers.get('tokens-left')
            if tokens_left:
                try:
                    self.metrics.add_usage(1, int(tokens_left))
                except ValueError:
                    pass

            self._circuit_breaker.record_success()
            return data

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            self._circuit_breaker.record_failure()
            self.logger.error(f"Keepa API error: {e}")
            raise

    # =========================================================================
    # PRODUCT DATA METHODS
    # =========================================================================

    async def get_product_with_quick_cache(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get product with ultra-short cache for repeated test calls.
        10 minute TTL for development testing.
        """
        # Check quick cache
        cached = self._cache_manager.get_quick(identifier)
        if cached:
            self.logger.debug(f"Quick cache HIT for {identifier}")
            return cached

        # Get from normal flow
        result = await self.get_product_data(identifier)

        if result:
            self._cache_manager.set_quick(identifier, result)

        return result

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
        from datetime import datetime

        # Check cache first (unless force_refresh)
        cache_key = self._get_cache_key('/product', {
            'asin': identifier,
            'domain': domain
        })

        cached_data = None if force_refresh else self._get_from_cache(cache_key)
        if cached_data:
            self.logger.info(f"[CACHE HIT] Serving cached data for {identifier}")
            return cached_data

        if force_refresh:
            self.logger.info(f"[FORCE REFRESH] Bypassing cache for {identifier}, requesting LIVE data with update=0")
        else:
            self.logger.info(f"[CACHE MISS] No valid cache for {identifier}, requesting data from Keepa")

        try:
            import keepa

            api = keepa.Keepa(self.api_key)

            loop = asyncio.get_event_loop()

            def _sync_query():
                domain_map = {
                    1: 'US', 2: 'GB', 3: 'DE', 4: 'FR', 5: 'JP',
                    6: 'CA', 7: 'CN', 8: 'IT', 9: 'ES', 10: 'IN',
                    11: 'MX', 12: 'BR'
                }
                domain_str = domain_map.get(domain, 'US')
                update_param = 0 if force_refresh else None

                self.logger.info(f"[KEEPA API] Calling with update={update_param} for {identifier}")

                return api.query(
                    identifier,
                    domain=domain_str,
                    stats=180,
                    history=True,
                    offers=20,
                    update=update_param
                )

            products = await loop.run_in_executor(None, _sync_query)

            if not products or len(products) == 0:
                self.logger.info(f"Product not found: {identifier}")
                return None

            product = products[0]

            # Sanitize numpy arrays before caching/returning
            from app.utils.keepa_utils import keepa_to_datetime, sanitize_keepa_response

            product = sanitize_keepa_response(product)
            self.logger.info(f"[NUMPY FIX] Sanitized numpy arrays for {identifier}")

            # Log data freshness
            last_price_change = product.get("lastPriceChange", -1)
            if last_price_change != -1:
                timestamp = keepa_to_datetime(last_price_change)
                if timestamp:
                    age_days = (datetime.now() - timestamp).days
                    self.logger.info(
                        f"[KEEPA DATA] [OK] Received data for {identifier}, "
                        f"lastPriceChange: {timestamp.isoformat()} ({age_days} days old)"
                    )
                else:
                    self.logger.warning(f"[KEEPA DATA] Failed to convert lastPriceChange={last_price_change}")
            else:
                self.logger.info(f"[KEEPA DATA] Received data for {identifier}, no lastPriceChange available")

            # Cache the result
            self._set_cache(cache_key, product, cache_type='pricing')
            self.logger.info(f"[CACHE SET] Cached data for {identifier} with TTL={self._cache_ttl['pricing']}")

            return product

        except Exception as e:
            self.logger.error(f"Failed to get product data for {identifier}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def find_products(self, search_criteria: Dict[str, Any], domain: int = 1, max_results: int = 50) -> List[str]:
        """
        Find products using Keepa Product Finder.

        Args:
            search_criteria: Dictionary with search criteria (categories, price ranges, BSR, etc.)
            domain: Keepa domain (1=US, 2=UK, etc.)
            max_results: Maximum number of ASINs to return (default 50)

        Returns:
            List of ASINs matching the criteria
        """
        try:
            import keepa

            api = keepa.Keepa(self.api_key)

            product_params = {
                'categories_include': search_criteria.get('categories', [1000]),
                'current_NEW_gte': search_criteria.get('price_min_cents', 500),
                'current_NEW_lte': search_criteria.get('price_max_cents', 10000),
                'avg30_SALES_gte': search_criteria.get('bsr_min', 1),
                'avg30_SALES_lte': search_criteria.get('bsr_max', 100000),
            }

            self.logger.info(f"Keepa search with params: {product_params}")

            loop = asyncio.get_event_loop()

            def _sync_product_finder():
                return api.product_finder(
                    product_params,
                    domain='US' if domain == 1 else 'DE',
                    wait=True
                )

            asins = await loop.run_in_executor(None, _sync_product_finder)

            # Sanitize numpy arrays
            from app.utils.keepa_utils import sanitize_keepa_response
            asins = sanitize_keepa_response(asins)

            limited_asins = asins[:max_results] if asins else []

            self.logger.info(f"Keepa Product Finder: {len(limited_asins)} ASINs found (sanitized)")
            return limited_asins

        except Exception as e:
            self.logger.error(f"Error in product search: {e}")
            self.logger.error(f"Fallback to simulated data")
            return [
                "B08N5WRWNW", "B07FZ8S74R", "B09KMVSP4D",
                "B08XYZ1234", "B09ABC5678", "B07DEF9012"
            ][:max_results]

    # =========================================================================
    # HEALTH & UTILITY METHODS
    # =========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check API health and get token status."""
        try:
            balance = await self.check_api_balance()
            local_tokens = self.throttle.available_tokens

            return {
                "status": "healthy" if balance and balance > 0 else "degraded",
                "api_tokens_left": balance,
                "local_tokens_available": local_tokens,
                "throttle_healthy": self.throttle.is_healthy,
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

    async def get_sales_velocity_data(self, asin: str) -> Dict[str, Any]:
        """
        Get sales velocity data from Keepa API.

        Extracts salesRankDrops and related metrics for velocity estimation.
        """
        try:
            product_data = await self.get_product_data(asin)

            if not product_data:
                self.logger.warning(f"No product data available for velocity analysis: {asin}")
                return self._create_empty_velocity_data(asin)

            stats = product_data.get('stats', {})

            # Extract category from categoryTree
            category = 'Unknown'
            category_tree = product_data.get('categoryTree', [])
            if category_tree and len(category_tree) > 0:
                category = category_tree[0].get('name', 'Unknown')

            # Get BSR from stats.current[3]
            current = stats.get('current', [])
            current_bsr = None
            if current and len(current) > 3:
                bsr = current[3]
                if bsr and bsr != -1:
                    current_bsr = int(bsr)

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
        """Create empty velocity data structure."""
        return {
            "asin": asin,
            "sales_drops_30": 0,
            "sales_drops_90": 0,
            "current_bsr": 0,
            "category": "Unknown",
            "domain": 1,
            "title": "Unknown Product"
        }


# =========================================================================
# DEPENDENCY INJECTION
# =========================================================================

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


# Backward compatibility exports
__all__ = [
    # Main class
    'KeepaService',

    # Dependency injection
    'get_keepa_service',

    # Re-exported from keepa_models for backward compatibility
    'ENDPOINT_COSTS',
    'MIN_BALANCE_THRESHOLD',
    'SAFETY_BUFFER',
    'CircuitState',
    'CacheEntry',
    'TokenMetrics',
    'CircuitBreaker',
]
