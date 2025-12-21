"""
Keepa Product Finder Service - Phase 2 Jour 5

Utilise Keepa REST API directe (httpx) pour découvrir des produits selon critères :
- Catégorie
- BSR range
- Prix range
- Deals actifs

Architecture Production-Ready :
- httpx pour appels API directs
- KEEPA_API_KEY dans params
- Aucune dépendance serveur externe
"""

from typing import List, Dict, Any, Optional, Tuple, Union
from decimal import Decimal
from datetime import datetime
import logging
import json
import asyncio

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.config_service import ConfigService
from app.services.keepa_service import KeepaService, ENDPOINT_COSTS
from app.services.cache_service import CacheService
from app.schemas.config import CategoryConfig

logger = logging.getLogger(__name__)


# Phase 6: Budget Guard - Token Cost Constants
BESTSELLERS_COST = 50  # tokens per bestsellers call
PRODUCT_FINDER_COST = 10  # tokens per Product Finder /query call
FILTERING_COST_PER_ASIN = 1  # tokens per ASIN in filtering

# Phase 6.2: Root category mapping (Product Finder only supports root categories)
# Map subcategories to their root category for Product Finder queries
ROOT_CATEGORY_MAPPING = {
    # Books subcategories -> Books root (283155)
    10777: 283155,   # Law
    10927: 283155,   # Legal Education
    3508: 283155,    # Python/Programming
    3839: 283155,    # Programming Languages
    3654: 283155,    # CS Textbooks
    5: 283155,       # Computers & Technology
    4736: 283155,    # Self-Help
    11748: 283155,   # Success
    6: 283155,       # Cookbooks
    1000: 283155,    # Special Diet
    4: 283155,       # Children's Books
    17: 283155,      # Education & Reference
    18: 283155,      # Mystery
    10677: 283155,   # Thriller & Suspense
    23: 283155,      # Romance
    10188: 283155,   # Contemporary Romance
    5267: 283155,    # Exercise & Fitness
    2: 283155,       # Business & Money
    2766: 283155,    # Business Education
    2767: 283155,    # Business Textbooks
    75: 283155,      # Science & Math
    13912: 283155,   # Science Textbooks
    13884: 283155,   # Math Textbooks
    173514: 283155,  # Medical Books
    227613: 283155,  # Nursing
    13611: 283155,   # Engineering
    13887: 283155,   # Engineering Textbooks
    11232: 283155,   # Social Sciences
    15371: 283155,   # Psychology
}

# Books root category ID
BOOKS_ROOT_CATEGORY = 283155


def estimate_discovery_cost(
    count: int,
    max_asins_per_niche: int = 100,
    buffer_percent: int = 0
) -> int:
    """
    Estimate MAXIMUM token cost for niche discovery.

    Formula:
    - bestsellers: 50 tokens x count
    - filtering: 1 token x max_asins x count

    Args:
        count: Number of niches to discover
        max_asins_per_niche: Maximum ASINs to filter per niche (default 100)
        buffer_percent: Optional safety buffer percentage (default 0)

    Returns:
        Conservative (high) estimate of token cost
    """
    if count <= 0:
        return 0

    bestsellers_cost = BESTSELLERS_COST * count
    filtering_cost = max_asins_per_niche * FILTERING_COST_PER_ASIN * count
    base_cost = bestsellers_cost + filtering_cost

    if buffer_percent > 0:
        return int(base_cost * (1 + buffer_percent / 100))

    return base_cost


class KeepaProductFinderService:
    """
    Service pour découvrir produits via Keepa REST API.

    Utilise l'API directe Keepa pour production.
    """

    def __init__(
        self,
        keepa_service: KeepaService,
        config_service: ConfigService,
        db: Optional[Union[Session, AsyncSession]] = None
    ):
        """
        Initialize Product Finder.

        Args:
            keepa_service: Service Keepa existant (avec httpx client)
            config_service: Service Config pour filtres business
            db: Optional SQLAlchemy session (sync or async) for cache operations
        """
        self.keepa_service = keepa_service
        self.config_service = config_service
        self.db = db
        self.cache_service = CacheService(db) if db else None

        if self.cache_service:
            logger.info("[CACHE] CacheService initialized - cache enabled")
        else:
            logger.debug("[CACHE] No db session - cache disabled")

    async def discover_products(
        self,
        domain: int,
        category: Optional[int] = None,
        bsr_min: Optional[int] = None,
        bsr_max: Optional[int] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        max_results: int = 100,
        max_fba_sellers: Optional[int] = None,
        exclude_amazon_seller: bool = True,
        use_product_finder: bool = True
    ) -> List[str]:
        """
        Découvre produits selon critères.

        Args:
            domain: Amazon domain ID (1=US, 2=UK, etc.)
            category: Category ID Keepa (ex: 283155 pour Books)
            bsr_min: BSR minimum
            bsr_max: BSR maximum
            price_min: Prix minimum (dollars)
            price_max: Prix maximum (dollars)
            max_results: Nombre max de résultats
            max_fba_sellers: Maximum FBA sellers (competition filter)
            exclude_amazon_seller: Exclude products where Amazon sells (default True)
            use_product_finder: Use Product Finder API (default True, Phase 6.2)

        Returns:
            Liste d'ASINs découverts

        Strategy (Phase 6.2):
            1. Si category fournie + use_product_finder → Product Finder /query (preferred)
            2. Fallback → bestsellers endpoint
            3. Sinon → deals endpoint
            4. Post-filtrer par Amazon/FBA
            5. Retourner top N ASINs
        """
        discovered_asins: List[str] = []

        try:
            if category:
                if use_product_finder and (bsr_min or bsr_max or price_min or price_max):
                    # Strategy 1 (Phase 6.2): Product Finder with post-filtering
                    # More efficient: pre-filters BSR/price, post-filters Amazon/FBA
                    logger.info(
                        f"[DISCOVERY] Using Product Finder - Category {category} "
                        f"(BSR: {bsr_min}-{bsr_max}, Price: ${price_min}-${price_max})"
                    )
                    discovered_asins = await self._discover_via_product_finder(
                        domain=domain,
                        category=category,
                        bsr_min=bsr_min,
                        bsr_max=bsr_max,
                        price_min=price_min,
                        price_max=price_max,
                        max_results=max_results,
                        max_fba_sellers=max_fba_sellers,
                        exclude_amazon_seller=exclude_amazon_seller
                    )
                else:
                    # Strategy 2: Bestsellers par catégorie (fallback)
                    logger.info(f"[DISCOVERY] Using Bestsellers - Category {category}")
                    discovered_asins = await self._discover_via_bestsellers(
                        domain=domain,
                        category=category,
                        bsr_min=bsr_min,
                        bsr_max=bsr_max,
                        price_min=price_min,
                        price_max=price_max,
                        max_results=max_results,
                        max_fba_sellers=max_fba_sellers
                    )
            else:
                # Strategy 3: Deals actifs
                logger.info("[DISCOVERY] Using Deals endpoint")
                discovered_asins = await self._discover_via_deals(
                    domain=domain,
                    price_min=price_min,
                    price_max=price_max,
                    max_results=max_results
                )

            logger.info(f"[DISCOVERY] Found {len(discovered_asins)} ASINs")
            return discovered_asins[:max_results]

        except Exception as e:
            logger.error(f"[DISCOVERY] Error: {e}")
            raise

    async def _discover_via_product_finder(
        self,
        domain: int,
        category: int,
        bsr_min: Optional[int],
        bsr_max: Optional[int],
        price_min: Optional[float],
        price_max: Optional[float],
        max_results: int,
        max_fba_sellers: Optional[int] = None,
        exclude_amazon_seller: bool = True,
        use_subsegments: bool = True
    ) -> List[str]:
        """
        Discover via Product Finder /query endpoint with post-filtering.

        Phase 6.2: Product Finder Strategy
        - Pre-filter: rootCategory + BSR + Price (API supports these)
        - Post-filter: Amazon exclusion + FBA count (API doesn't support combo)

        Phase 9: Option B - BSR Sub-Segments
        - Divides BSR range into 3 sub-segments for better coverage
        - Each sub-segment queried separately, results merged
        - Provides products across full BSR range instead of clustering at bottom

        Keepa API: /query
        Returns: Array of ASINs matching pre-filters
        Cost: ~10 tokens per query (x3 for sub-segments = ~30 tokens)

        Why post-filtering:
        - API returns 0 results when combining current_AMAZON_lte:-1 with offerCountFBA_lte
        - Test results: Without Amazon exclusion -> 100K+ products
        - We query with BSR/price filters, then filter Amazon/FBA via /product details
        """
        try:
            # Map subcategory to root category (Product Finder requirement)
            root_category = ROOT_CATEGORY_MAPPING.get(category, category)
            if root_category != category:
                logger.info(
                    f"[PRODUCT_FINDER] Mapped category {category} -> root {root_category}"
                )

            # Phase 9: Option B - BSR Sub-Segments for better coverage
            # Only use sub-segments if both bsr_min and bsr_max are specified
            if use_subsegments and bsr_min is not None and bsr_max is not None:
                return await self._discover_with_subsegments(
                    domain=domain,
                    root_category=root_category,
                    bsr_min=bsr_min,
                    bsr_max=bsr_max,
                    price_min=price_min,
                    price_max=price_max,
                    max_results=max_results,
                    max_fba_sellers=max_fba_sellers,
                    exclude_amazon_seller=exclude_amazon_seller
                )

            # Standard single query (fallback or when sub-segments not applicable)
            return await self._single_product_finder_query(
                domain=domain,
                root_category=root_category,
                bsr_min=bsr_min,
                bsr_max=bsr_max,
                price_min=price_min,
                price_max=price_max,
                max_results=max_results,
                max_fba_sellers=max_fba_sellers,
                exclude_amazon_seller=exclude_amazon_seller
            )

        except Exception as e:
            logger.error(f"[PRODUCT_FINDER] Error: {e}")
            # Fallback to bestsellers if Product Finder fails
            logger.info("[PRODUCT_FINDER] Falling back to bestsellers endpoint")
            return await self._discover_via_bestsellers(
                domain=domain,
                category=category,
                bsr_min=bsr_min,
                bsr_max=bsr_max,
                price_min=price_min,
                price_max=price_max,
                max_results=max_results,
                max_fba_sellers=max_fba_sellers
            )

    async def _discover_with_subsegments(
        self,
        domain: int,
        root_category: int,
        bsr_min: int,
        bsr_max: int,
        price_min: Optional[float],
        price_max: Optional[float],
        max_results: int,
        max_fba_sellers: Optional[int] = None,
        exclude_amazon_seller: bool = True
    ) -> List[str]:
        """
        Phase 9: Option B - Discover products using BSR sub-segments.

        Divides BSR range into 3 equal sub-segments and queries each separately.
        This provides better coverage across the full BSR range instead of
        clustering results at the lower BSR end.

        Example for BSR 100K-250K:
        - Segment 1: 100K-150K (lower third)
        - Segment 2: 150K-200K (middle third)
        - Segment 3: 200K-250K (upper third)

        Args:
            domain: Amazon domain ID
            root_category: Root category for Product Finder
            bsr_min: Minimum BSR for full range
            bsr_max: Maximum BSR for full range
            price_min: Minimum price filter
            price_max: Maximum price filter
            max_results: Maximum total results to return
            max_fba_sellers: Maximum FBA sellers (competition filter)
            exclude_amazon_seller: Exclude products where Amazon sells

        Returns:
            Merged list of ASINs from all sub-segments, deduplicated

        Token cost: ~30 tokens (3 queries x 10 tokens each)
        """
        # Calculate sub-segment boundaries
        bsr_range = bsr_max - bsr_min
        segment_size = bsr_range // 3

        segments = [
            (bsr_min, bsr_min + segment_size),                    # Lower third
            (bsr_min + segment_size, bsr_min + 2 * segment_size), # Middle third
            (bsr_min + 2 * segment_size, bsr_max)                 # Upper third
        ]

        logger.info(
            f"[PRODUCT_FINDER] Sub-segments strategy: "
            f"[{segments[0][0]:,}-{segments[0][1]:,}], "
            f"[{segments[1][0]:,}-{segments[1][1]:,}], "
            f"[{segments[2][0]:,}-{segments[2][1]:,}]"
        )

        # Query each segment (sequentially to avoid rate limits)
        all_asins = []
        results_per_segment = max(20, max_results // 3)  # Distribute results across segments

        for i, (seg_min, seg_max) in enumerate(segments):
            try:
                segment_asins = await self._single_product_finder_query(
                    domain=domain,
                    root_category=root_category,
                    bsr_min=seg_min,
                    bsr_max=seg_max,
                    price_min=price_min,
                    price_max=price_max,
                    max_results=results_per_segment,
                    max_fba_sellers=max_fba_sellers,
                    exclude_amazon_seller=exclude_amazon_seller
                )

                logger.info(
                    f"[PRODUCT_FINDER] Segment {i+1}/3 (BSR {seg_min:,}-{seg_max:,}): "
                    f"{len(segment_asins)} ASINs"
                )

                all_asins.extend(segment_asins)

                # Small delay between segments to avoid rate limiting
                if i < len(segments) - 1:
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.warning(f"[PRODUCT_FINDER] Segment {i+1} failed: {e}")
                continue

        # Deduplicate while preserving order
        seen = set()
        unique_asins = []
        for asin in all_asins:
            if asin not in seen:
                seen.add(asin)
                unique_asins.append(asin)

        logger.info(
            f"[PRODUCT_FINDER] Sub-segments total: {len(unique_asins)} unique ASINs "
            f"(from {len(all_asins)} total)"
        )

        return unique_asins[:max_results]

    async def _single_product_finder_query(
        self,
        domain: int,
        root_category: int,
        bsr_min: Optional[int],
        bsr_max: Optional[int],
        price_min: Optional[float],
        price_max: Optional[float],
        max_results: int,
        max_fba_sellers: Optional[int] = None,
        exclude_amazon_seller: bool = True
    ) -> List[str]:
        """
        Execute a single Product Finder /query request.

        Extracted from _discover_via_product_finder for reuse in sub-segments.

        Args:
            domain: Amazon domain ID
            root_category: Root category (already mapped)
            bsr_min: Minimum BSR filter
            bsr_max: Maximum BSR filter
            price_min: Minimum price in dollars
            price_max: Maximum price in dollars
            max_results: Maximum ASINs to return
            max_fba_sellers: Maximum FBA sellers (post-filter)
            exclude_amazon_seller: Exclude Amazon as seller (post-filter)

        Returns:
            List of ASINs matching filters
        """
        # Build selection object for Product Finder
        # CRITICAL: Keepa API requires perPage >= 50, otherwise returns 400 error
        selection = {
            "rootCategory": root_category,
            "perPage": max(50, min(100, max_results))
        }

        # Add BSR range if specified
        if bsr_min is not None:
            selection["current_SALES_gte"] = bsr_min
        if bsr_max is not None:
            selection["current_SALES_lte"] = bsr_max

        # Add price range if specified (convert dollars to cents)
        if price_min is not None:
            selection["current_NEW_gte"] = int(price_min * 100)
        if price_max is not None:
            selection["current_NEW_lte"] = int(price_max * 100)

        logger.debug(
            f"[PRODUCT_FINDER] Query: rootCategory={root_category}, "
            f"BSR={bsr_min}-{bsr_max}, Price=${price_min}-${price_max}"
        )

        # Call Product Finder /query endpoint
        endpoint = "/query"
        params = {
            "domain": domain,
            "selection": json.dumps(selection)
        }

        response = await self.keepa_service._make_request(endpoint, params)

        if not response:
            logger.warning("[PRODUCT_FINDER] No response from /query endpoint")
            return []

        asins = response.get("asinList", [])
        total = response.get("totalResults", 0)
        tokens = response.get("tokensConsumed", 0)

        logger.debug(
            f"[PRODUCT_FINDER] Found {total} total, returned {len(asins)} ASINs "
            f"(cost: {tokens} tokens)"
        )

        if not asins:
            return []

        # Post-filter via /product endpoint if Amazon/FBA filters needed
        if exclude_amazon_seller or max_fba_sellers is not None:
            filtered_asins = await self._post_filter_asins(
                domain=domain,
                asins=asins[:100],
                max_fba_sellers=max_fba_sellers,
                exclude_amazon_seller=exclude_amazon_seller
            )
            return filtered_asins[:max_results]

        return asins[:max_results]

    async def _post_filter_asins(
        self,
        domain: int,
        asins: List[str],
        max_fba_sellers: Optional[int] = None,
        exclude_amazon_seller: bool = True
    ) -> List[str]:
        """
        Post-filter ASINs by Amazon/FBA criteria via /product endpoint.

        Phase 6.2: This handles filters that don't work in Product Finder API.

        Args:
            asins: ASINs to filter
            max_fba_sellers: Maximum FBA sellers allowed
            exclude_amazon_seller: Exclude products where Amazon is selling

        Returns:
            Filtered ASINs meeting all criteria
        """
        if not asins:
            return []

        filtered_asins = []

        try:
            # Get product details
            endpoint = "/product"
            params = {
                "domain": domain,
                "asin": ",".join(asins),
                "stats": 1,
                "history": 0
            }

            response = await self.keepa_service._make_request(endpoint, params)
            products = response.get("products", []) if response else []

            for product in products:
                asin = product.get("asin")
                if not asin:
                    continue

                stats = product.get("stats", {})
                current = stats.get("current", [])

                # Check Amazon seller exclusion
                # current[0] = AMAZON price - if > 0, Amazon is selling
                if exclude_amazon_seller:
                    amazon_price = current[0] if len(current) > 0 else None
                    if amazon_price is not None and amazon_price > 0:
                        logger.debug(
                            f"[POST_FILTER] Excluding {asin}: Amazon selling at ${amazon_price/100:.2f}"
                        )
                        continue

                # Check FBA seller count
                # current[11] = COUNT_NEW (FBA/new offers count)
                if max_fba_sellers is not None:
                    fba_count = current[11] if len(current) > 11 else None
                    if fba_count is not None and fba_count > max_fba_sellers:
                        logger.debug(
                            f"[POST_FILTER] Excluding {asin}: {fba_count} FBA sellers > {max_fba_sellers}"
                        )
                        continue

                # Passed all filters
                filtered_asins.append(asin)

            logger.info(
                f"[POST_FILTER] {len(filtered_asins)}/{len(asins)} ASINs passed "
                f"(exclude_amazon={exclude_amazon_seller}, max_fba={max_fba_sellers})"
            )

            return filtered_asins

        except Exception as e:
            logger.error(f"[POST_FILTER] Error: {e}")
            return []

    async def _discover_via_bestsellers(
        self,
        domain: int,
        category: int,
        bsr_min: Optional[int],
        bsr_max: Optional[int],
        price_min: Optional[float],
        price_max: Optional[float],
        max_results: int,
        max_fba_sellers: Optional[int] = None
    ) -> List[str]:
        """
        Découvrir via bestsellers endpoint (fallback method).

        Keepa API: /bestsellers
        Returns: Array of ASINs (up to 100,000)
        Cost: 50 tokens per request
        """
        try:
            # [OK] PHASE 4.5: Pre-check budget for expensive bestsellers call (50 tokens)
            # Note: _make_request() also checks, but this gives clearer error message
            await self.keepa_service._ensure_sufficient_balance(
                estimated_cost=ENDPOINT_COSTS.get("bestsellers", 50),
                endpoint_name="bestsellers"
            )

            # Call Keepa bestsellers endpoint
            endpoint = "/bestsellers"
            params = {
                "domain": domain,
                "category": category
            }

            response = await self.keepa_service._make_request(endpoint, params)

            if not response or "bestSellersList" not in response:
                logger.warning(f"No bestsellers found for category {category}")
                return []

            # Extract ASINs from response
            asins = response.get("bestSellersList", {}).get("asinList", [])

            # Si on a des filtres BSR/prix/competition, on doit récupérer les détails
            if bsr_min or bsr_max or price_min or price_max or max_fba_sellers:
                # Batch retrieve pour filtrer
                # Phase 6 fix: Reduced from 500 to 100 ASINs to save ~400 tokens per niche
                # Cost: 1 token per ASIN, so 100 ASINs = 100 tokens vs 500 = 500 tokens
                filtered_asins = await self._filter_asins_by_criteria(
                    domain=domain,
                    asins=asins[:100],  # Limite 100 ASINs pour economiser tokens
                    bsr_min=bsr_min,
                    bsr_max=bsr_max,
                    price_min=price_min,
                    price_max=price_max,
                    max_fba_sellers=max_fba_sellers
                )
                return filtered_asins[:max_results]

            # Sinon retourner directement les ASINs
            return asins[:max_results]

        except Exception as e:
            logger.error(f"Bestsellers discovery error: {e}")
            return []

    async def _discover_via_deals(
        self,
        domain: int,
        price_min: Optional[float],
        price_max: Optional[float],
        max_results: int
    ) -> List[str]:
        """
        Découvrir via deals endpoint.

        Keepa API: /deals
        Returns: Array of deals
        Cost: 5 tokens per 150 deals
        """
        try:
            # Call Keepa deals endpoint
            endpoint = "/deals"
            params = {
                "domain": domain,
                "page": 0,
                "count": min(150, max_results)
            }

            response = await self.keepa_service._make_request(endpoint, params)

            if not response or "deals" not in response:
                logger.warning("No deals found")
                return []

            # Extract ASINs from deals
            asins = []
            for deal in response.get("deals", []):
                asin = deal.get("asin")
                if asin:
                    # Check price range if specified
                    current_price = deal.get("currentPrice", 0) / 100  # cents to dollars

                    if price_min and current_price < price_min:
                        continue
                    if price_max and current_price > price_max:
                        continue

                    asins.append(asin)

            return asins[:max_results]

        except Exception as e:
            logger.error(f"Deals discovery error: {e}")
            return []

    async def _filter_asins_by_criteria(
        self,
        domain: int,
        asins: List[str],
        bsr_min: Optional[int],
        bsr_max: Optional[int],
        price_min: Optional[float],
        price_max: Optional[float],
        max_fba_sellers: Optional[int] = None,
        exclude_amazon_seller: bool = True
    ) -> List[str]:
        """
        Filtrer ASINs par criteres BSR/prix.

        Recupere les details produits et filtre.
        Includes rate limit protection with delays between batches.

        Args:
            exclude_amazon_seller: If True, exclude products where Amazon is a seller.
                                   Amazon always wins Buy Box and crushes FBA margins.
                                   Default: True (recommended for arbitrage beginners).
        """
        if not asins:
            return []

        filtered_asins = []
        batch_delay_seconds = 1.5  # Delay between batches to avoid rate limiting
        rate_limit_retries = 0
        max_rate_limit_retries = 2

        # Batch retrieve (max 100 per request)
        batch_count = (len(asins) + 99) // 100  # Total batches
        for batch_idx, i in enumerate(range(0, len(asins), 100)):
            batch = asins[i:i+100]

            try:
                # [OK] PHASE 4.5: Pre-check budget for batch product request
                batch_cost = len(batch)  # 1 token per ASIN
                await self.keepa_service._ensure_sufficient_balance(
                    estimated_cost=batch_cost,
                    endpoint_name=f"product_batch_{len(batch)}"
                )

                # Get product details via Keepa API
                endpoint = "/product"
                params = {
                    "domain": domain,
                    "asin": ",".join(batch),
                    "stats": 1,  # Include stats for BSR
                    "history": 0  # No history needed
                }

                response = await self.keepa_service._make_request(endpoint, params)
                products = response.get("products", []) if response else []

                # Filter by criteria
                for product in products:
                    # Extract BSR and price from stats.current[]
                    # Keepa current[] array indices:
                    #   [0] = AMAZON price (often -1 if unavailable)
                    #   [1] = NEW price (3rd party sellers - this is what we want!)
                    #   [2] = USED price
                    #   [3] = Sales Rank (BSR)
                    stats = product.get("stats", {})
                    current = stats.get("current", [None, None, None, None])

                    # Use NEW price (index 1), fallback to AMAZON price (index 0) if unavailable
                    price_cents = None
                    if len(current) > 1 and current[1] is not None and current[1] > 0:
                        price_cents = current[1]  # NEW price (preferred)
                    elif len(current) > 0 and current[0] is not None and current[0] > 0:
                        price_cents = current[0]  # AMAZON price (fallback)

                    bsr = current[3] if len(current) > 3 else None

                    # Apply BSR filter
                    if bsr is not None:
                        if bsr_min and bsr < bsr_min:
                            continue
                        if bsr_max and bsr > bsr_max:
                            continue

                    # Apply price filter
                    if price_cents is not None:
                        price = price_cents / 100
                        if price_min and price < price_min:
                            continue
                        if price_max and price > price_max:
                            continue

                    # Apply "Exclude Amazon as seller" filter (Phase 6.1)
                    # stats.current[0] = AMAZON price - if > 0, Amazon is selling this product
                    # Amazon always wins Buy Box, making FBA arbitrage unprofitable
                    if exclude_amazon_seller:
                        amazon_price = current[0] if len(current) > 0 else None
                        if amazon_price is not None and amazon_price > 0:
                            logger.debug(
                                f"Skipping ASIN {product.get('asin')}: "
                                f"Amazon is a seller (price: ${amazon_price/100:.2f})"
                            )
                            continue

                    # Apply FBA seller count filter (competition filter)
                    # stats.current[11] = COUNT_NEW (number of new/FBA offers)
                    if max_fba_sellers is not None:
                        new_offer_count = current[11] if len(current) > 11 else None
                        if new_offer_count is not None and new_offer_count > max_fba_sellers:
                            # Too much competition - skip this product
                            logger.debug(
                                f"Skipping ASIN {product.get('asin')}: "
                                f"{new_offer_count} FBA sellers > max {max_fba_sellers}"
                            )
                            continue

                    # Product passes filters
                    asin = product.get("asin")
                    if asin:
                        filtered_asins.append(asin)

                # Reset rate limit retry counter on success
                rate_limit_retries = 0

                # Add delay between batches to prevent rate limiting (except last batch)
                if batch_idx < batch_count - 1:
                    logger.debug(f"Batch {batch_idx + 1}/{batch_count} complete. Waiting {batch_delay_seconds}s before next batch.")
                    await asyncio.sleep(batch_delay_seconds)

            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "rate limit" in error_str:
                    rate_limit_retries += 1
                    if rate_limit_retries <= max_rate_limit_retries:
                        wait_time = 5 * rate_limit_retries  # 5s, 10s for retries
                        logger.warning(
                            f"Rate limit hit on batch {batch_idx + 1}/{batch_count}. "
                            f"Waiting {wait_time}s before retry ({rate_limit_retries}/{max_rate_limit_retries})"
                        )
                        await asyncio.sleep(wait_time)
                        # Note: _make_request already has retry, this is extra safety
                        continue
                    else:
                        logger.warning(
                            f"Rate limit persists after {max_rate_limit_retries} retries. "
                            f"Returning {len(filtered_asins)} ASINs collected so far."
                        )
                        break
                else:
                    logger.error(f"Error filtering batch {batch_idx + 1}: {e}")
                    continue

        logger.info(f"Filtering complete: {len(filtered_asins)} ASINs passed criteria")
        return filtered_asins

    async def discover_with_scoring(
        self,
        domain: int,
        category: Optional[int] = None,
        bsr_min: Optional[int] = None,
        bsr_max: Optional[int] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        min_roi: Optional[float] = None,
        min_velocity: Optional[float] = None,
        max_results: int = 50,
        force_refresh: bool = False,
        max_fba_sellers: Optional[int] = None,
        exclude_amazon_seller: bool = True,
        strategy: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover products with complete scoring.

        Applies Config Service filters and returns scored products.

        Args:
            domain: Amazon domain ID (1=US, 2=UK, etc.)
            category: Category ID to search
            bsr_min: Minimum BSR filter
            bsr_max: Maximum BSR filter
            price_min: Minimum price filter
            price_max: Maximum price filter
            min_roi: Minimum ROI filter
            min_velocity: Minimum velocity score filter
            max_results: Maximum products to return
            force_refresh: If True, bypasses cache for product data
            max_fba_sellers: Maximum FBA sellers allowed (competition filter)
            exclude_amazon_seller: If True, exclude products where Amazon is a seller.
                                   Default: True (recommended for arbitrage).
            strategy: Strategy type for velocity/recommendation adjustments.
                      Options: textbooks_standard, textbooks_patience, smart_velocity.
                      Affects velocity scoring tiers and recommendation thresholds.

        Returns:
            List of products with metrics:
            - asin
            - title
            - price
            - bsr
            - roi_percent
            - velocity_score
            - recommendation
        """
        # Step 1: Discover ASINs (with cache, unless force_refresh)
        asins = []
        discovery_cache_hit = False

        if self.cache_service and not force_refresh:
            # Try cache first
            cached_asins = await self.cache_service.get_discovery_cache(
                domain=domain,
                category=category,
                bsr_min=bsr_min,
                bsr_max=bsr_max,
                price_min=price_min,
                price_max=price_max
            )

            if cached_asins:
                asins = cached_asins
                discovery_cache_hit = True
                logger.info(f"[DISCOVERY] Cache HIT: {len(asins)} ASINs")
            else:
                logger.debug(f"[DISCOVERY] Cache MISS - calling Keepa API")
        elif force_refresh:
            logger.info(f"[DISCOVERY] FORCE REFRESH - bypassing cache")

        # If no cache or cache miss, call Keepa API
        if not asins:
            asins = await self.discover_products(
                domain=domain,
                category=category,
                bsr_min=bsr_min,
                bsr_max=bsr_max,
                price_min=price_min,
                price_max=price_max,
                max_results=max_results * 2,  # Get more for filtering
                max_fba_sellers=max_fba_sellers,
                exclude_amazon_seller=exclude_amazon_seller,  # Phase 6.2
                use_product_finder=True  # Phase 6.2: Use Product Finder by default
            )

            if self.cache_service and asins:
                # Store in cache
                cache_key = await self.cache_service.set_discovery_cache(
                    domain=domain,
                    category=category,
                    bsr_min=bsr_min,
                    bsr_max=bsr_max,
                    price_min=price_min,
                    price_max=price_max,
                    asins=asins
                )
                logger.debug(f"[DISCOVERY] Cached {len(asins)} ASINs (key: {cache_key[:8]}...)")

        if not asins:
            logger.warning("No ASINs discovered")
            return []

        # Step 2: Get product details
        endpoint = "/product"
        params = {
            "domain": domain,
            "asin": ",".join(asins),
            "stats": 1,
            "history": 1  # Need history for velocity
        }

        response = await self.keepa_service._make_request(endpoint, params)
        products = response.get("products", []) if response else []

        # Step 3: Apply scoring and filters (with cache per product)
        scored_products = []
        scoring_cache_hits = 0
        scoring_cache_misses = 0

        # Get effective config - use default if config service fails
        try:
            effective_config = await self.config_service.get_effective_config(category_id=category)
        except Exception as e:
            logger.warning(f"Config service failed, using defaults: {e}")
            # Configuration par defaut avec structure attendue par le code
            # Doit matcher l'interface EffectiveConfig avec effective_roi, effective_fees, effective_velocity
            from types import SimpleNamespace
            effective_config = SimpleNamespace(
                effective_roi=SimpleNamespace(
                    source_price_factor=Decimal("0.4"),
                    excellent_threshold=Decimal("50"),
                    target=Decimal("30"),
                    min_acceptable=Decimal("15")
                ),
                effective_fees=SimpleNamespace(
                    referral_fee_percent=Decimal("15"),
                    fba_base_fee=Decimal("2.50"),
                    fba_per_pound=Decimal("0.40"),
                    closing_fee=Decimal("1.80"),
                    prep_fee=Decimal("0.20"),
                    shipping_cost=Decimal("0.40")
                ),
                effective_velocity=SimpleNamespace(
                    tiers=[
                        SimpleNamespace(bsr_threshold=10000, min_score=80, max_score=100),
                        SimpleNamespace(bsr_threshold=50000, min_score=60, max_score=80),
                        SimpleNamespace(bsr_threshold=100000, min_score=40, max_score=60),
                        SimpleNamespace(bsr_threshold=500000, min_score=20, max_score=40),
                    ]
                )
            )

        # Phase 8: Strategy-specific velocity tiers
        # Override velocity tiers based on strategy for appropriate BSR ranges
        from types import SimpleNamespace
        strategy_velocity_tiers = {
            # Smart Velocity: BSR 10K-80K - Fast rotation books
            # These books sell quickly, so velocity expectations are high
            # BSR 10K = very fast seller, BSR 80K = still good seller
            "smart_velocity": [
                SimpleNamespace(bsr_threshold=10000, min_score=85, max_score=95),    # BSR <= 10K: exceptional
                SimpleNamespace(bsr_threshold=25000, min_score=75, max_score=85),    # BSR 10K-25K: excellent
                SimpleNamespace(bsr_threshold=40000, min_score=65, max_score=75),    # BSR 25K-40K: very good
                SimpleNamespace(bsr_threshold=60000, min_score=55, max_score=65),    # BSR 40K-60K: good
                SimpleNamespace(bsr_threshold=80000, min_score=45, max_score=55),    # BSR 60K-80K: acceptable
                SimpleNamespace(bsr_threshold=150000, min_score=30, max_score=45),   # BSR > 80K: lower
            ],
            # Textbook Standard: BSR 100K-250K should map to good velocity scores
            # BSR 100K = top of range = higher velocity
            # BSR 250K = bottom of range = lower velocity
            "textbooks_standard": [
                SimpleNamespace(bsr_threshold=100000, min_score=70, max_score=85),   # BSR <= 100K: excellent
                SimpleNamespace(bsr_threshold=150000, min_score=55, max_score=70),   # BSR 100K-150K: good
                SimpleNamespace(bsr_threshold=200000, min_score=40, max_score=55),   # BSR 150K-200K: moderate
                SimpleNamespace(bsr_threshold=250000, min_score=30, max_score=40),   # BSR 200K-250K: acceptable
                SimpleNamespace(bsr_threshold=500000, min_score=15, max_score=30),   # BSR > 250K: low
            ],
            # Textbook Patience: BSR 250K-400K should map to reasonable velocity scores
            # These books rotate slower, so velocity expectations are lower
            "textbooks_patience": [
                SimpleNamespace(bsr_threshold=200000, min_score=60, max_score=75),   # BSR <= 200K: excellent
                SimpleNamespace(bsr_threshold=250000, min_score=50, max_score=60),   # BSR 200K-250K: very good
                SimpleNamespace(bsr_threshold=300000, min_score=40, max_score=50),   # BSR 250K-300K: good
                SimpleNamespace(bsr_threshold=350000, min_score=30, max_score=40),   # BSR 300K-350K: moderate
                SimpleNamespace(bsr_threshold=400000, min_score=25, max_score=30),   # BSR 350K-400K: acceptable
                SimpleNamespace(bsr_threshold=500000, min_score=15, max_score=25),   # BSR > 400K: low
            ],
            # Legacy textbooks (backward compat)
            "textbooks": [
                SimpleNamespace(bsr_threshold=100000, min_score=65, max_score=80),
                SimpleNamespace(bsr_threshold=200000, min_score=45, max_score=65),
                SimpleNamespace(bsr_threshold=300000, min_score=30, max_score=45),
                SimpleNamespace(bsr_threshold=500000, min_score=15, max_score=30),
            ]
        }

        # Apply strategy-specific velocity tiers if applicable
        if strategy and strategy in strategy_velocity_tiers:
            logger.info(f"[SCORING] Applying {strategy} velocity tiers")
            effective_config = SimpleNamespace(
                effective_roi=effective_config.effective_roi,
                effective_fees=effective_config.effective_fees,
                effective_velocity=SimpleNamespace(
                    tiers=strategy_velocity_tiers[strategy]
                )
            )

        for product in products:
            try:
                asin = product.get("asin")
                if not asin:
                    continue

                # Try scoring cache first (skip if force_refresh or strategy-specific)
                # Phase 8: Bypass cache when strategy is specified because velocity/recommendation
                # scoring depends on strategy type. Cache stores default scoring only.
                cached_scoring = None
                use_cache = self.cache_service and not force_refresh and not strategy
                if use_cache:
                    cached_scoring = await self.cache_service.get_scoring_cache(asin)

                if cached_scoring and use_cache:
                    # Cache HIT - use cached scoring (only for default strategy)
                    logger.debug(f"[SCORING] Cache HIT for ASIN {asin}")
                    scoring_cache_hits += 1

                    # Apply filters on cached data
                    if min_roi and cached_scoring.get("roi_percent", 0) < min_roi:
                        continue
                    if min_velocity and cached_scoring.get("velocity_score", 0) < min_velocity:
                        continue

                    scored_products.append(cached_scoring)
                else:
                    # Cache MISS - calculate scoring
                    logger.debug(f"[SCORING] Cache MISS for ASIN {asin} - calculating")
                    scoring_cache_misses += 1

                    # Extract metrics
                    title = product.get("title", "Unknown")
                    stats = product.get("stats", {})
                    current = stats.get("current", [None, None, None, None])

                    # Use NEW price (index 1), fallback to AMAZON price (index 0)
                    # Keepa current[] array indices:
                    #   [0] = AMAZON price (often -1 if unavailable)
                    #   [1] = NEW price (3rd party sellers - preferred!)
                    #   [3] = Sales Rank (BSR)
                    price_cents = None
                    if len(current) > 1 and current[1] is not None and current[1] > 0:
                        price_cents = current[1]  # NEW price (preferred)
                    elif len(current) > 0 and current[0] is not None and current[0] > 0:
                        price_cents = current[0]  # AMAZON price (fallback)

                    bsr = current[3] if len(current) > 3 else None

                    if not price_cents or not bsr:
                        continue

                    # Apply "Exclude Amazon as seller" filter (Phase 6.1)
                    # stats.current[0] = AMAZON price - if > 0, Amazon is selling
                    if exclude_amazon_seller:
                        amazon_price = current[0] if len(current) > 0 else None
                        if amazon_price is not None and amazon_price > 0:
                            logger.debug(
                                f"[SCORING] Skipping ASIN {asin}: "
                                f"Amazon is a seller (price: ${amazon_price/100:.2f})"
                            )
                            continue

                    price = Decimal(str(price_cents / 100))

                    # Calculate ROI
                    source_price = price * effective_config.effective_roi.source_price_factor
                    fees = self._calculate_fees(price, effective_config.effective_fees)
                    profit = price - source_price - fees
                    roi_percent = float((profit / source_price) * Decimal("100"))

                    # Apply ROI filter
                    if min_roi and roi_percent < min_roi:
                        continue

                    # Calculate velocity score
                    velocity_score = self._calculate_velocity_score(
                        bsr,
                        effective_config.effective_velocity.tiers
                    )

                    # Apply velocity filter
                    if min_velocity and velocity_score < min_velocity:
                        continue

                    # Get recommendation (Phase 8: strategy-aware thresholds)
                    recommendation = self._get_recommendation(
                        roi_percent,
                        velocity_score,
                        effective_config,
                        strategy=strategy
                    )

                    scoring_result = {
                        "asin": asin,
                        "title": title[:100],  # Truncate long titles
                        "price": float(price),
                        "current_price": float(price),  # Alias for frontend compatibility
                        "bsr": bsr,
                        "roi_percent": roi_percent,
                        "velocity_score": velocity_score,
                        "recommendation": recommendation
                    }

                    # Store in cache (Phase 6: removed keepa_data param per production schema)
                    if self.cache_service:
                        await self.cache_service.set_scoring_cache(
                            asin=asin,
                            title=title,
                            price=float(price),
                            bsr=bsr,
                            roi_percent=roi_percent,
                            velocity_score=velocity_score,
                            recommendation=recommendation
                        )
                        logger.debug(f"[SCORING] Cached ASIN {asin} (ROI: {roi_percent:.1f}%)")

                    scored_products.append(scoring_result)

            except Exception as e:
                logger.error(f"Error scoring product {asin}: {e}")
                continue

        # Log cache metrics
        total_products = scoring_cache_hits + scoring_cache_misses
        if total_products > 0:
            cache_hit_rate = (scoring_cache_hits / total_products) * 100
            logger.info(
                f"[METRICS] Scoring cache hit rate: {cache_hit_rate:.1f}% "
                f"({scoring_cache_hits}/{total_products})"
            )


        # Phase 9: Balanced selection across BSR range
        # Instead of pure score sorting (which clusters at low BSR),
        # we ensure representation from all BSR segments
        if bsr_min is not None and bsr_max is not None and len(scored_products) > max_results:
            # Calculate BSR segments (same logic as sub-segments discovery)
            bsr_range = bsr_max - bsr_min
            segment_size = bsr_range // 3
            segments_bounds = [
                (bsr_min, bsr_min + segment_size),                    # Lower third
                (bsr_min + segment_size, bsr_min + 2 * segment_size), # Middle third
                (bsr_min + 2 * segment_size, bsr_max + 1)             # Upper third (+1 for inclusive)
            ]

            # Group products by BSR segment
            segment_products = [[], [], []]
            for p in scored_products:
                product_bsr = p.get("bsr", 0)
                for i, (seg_min, seg_max) in enumerate(segments_bounds):
                    if seg_min <= product_bsr < seg_max:
                        segment_products[i].append(p)
                        break
                else:
                    # Product outside expected range - add to closest segment
                    if product_bsr < bsr_min:
                        segment_products[0].append(p)
                    else:
                        segment_products[2].append(p)

            # Sort each segment by score internally
            for segment in segment_products:
                segment.sort(
                    key=lambda p: p["roi_percent"] * 0.6 + p["velocity_score"] * 0.4,
                    reverse=True
                )

            # Take balanced representation from each segment
            results_per_segment = max(1, max_results // 3)
            balanced_results = []

            for i, segment in enumerate(segment_products):
                # Take up to results_per_segment from each segment
                segment_take = segment[:results_per_segment]
                balanced_results.extend(segment_take)
                logger.debug(
                    f"[SCORING] Segment {i+1}: {len(segment)} total, taking {len(segment_take)}"
                )

            # If we need more products, take remaining from any segment
            remaining_needed = max_results - len(balanced_results)
            if remaining_needed > 0:
                all_remaining = []
                for i, segment in enumerate(segment_products):
                    all_remaining.extend(segment[results_per_segment:])
                all_remaining.sort(
                    key=lambda p: p["roi_percent"] * 0.6 + p["velocity_score"] * 0.4,
                    reverse=True
                )
                balanced_results.extend(all_remaining[:remaining_needed])

            # Final sort by score for display order
            balanced_results.sort(
                key=lambda p: p["roi_percent"] * 0.6 + p["velocity_score"] * 0.4,
                reverse=True
            )

            logger.info(
                f"[SCORING] Balanced selection: {len(balanced_results)} products "
                f"from segments [{len(segment_products[0])}, {len(segment_products[1])}, {len(segment_products[2])}]"
            )

            return balanced_results[:max_results]
        else:
            # Fallback to simple score sorting if no BSR range specified
            scored_products.sort(
                key=lambda p: p["roi_percent"] * 0.6 + p["velocity_score"] * 0.4,
                reverse=True
            )
            return scored_products[:max_results]

    def _calculate_fees(self, price: Decimal, fees_config) -> Decimal:
        """Calculer fees totaux."""
        referral_fee = price * (fees_config.referral_fee_percent / Decimal("100"))
        fba_fee = fees_config.fba_base_fee + fees_config.fba_per_pound
        total = (
            referral_fee +
            fba_fee +
            fees_config.closing_fee +
            fees_config.prep_fee +
            fees_config.shipping_cost
        )
        return total

    def _calculate_velocity_score(self, bsr: int, tiers: list) -> float:
        """
        Calculer velocity score base sur BSR et tiers.

        Returns score 0-100.

        Args:
            bsr: Best Seller Rank (must be > 0 for valid products)
            tiers: List of velocity tiers with bsr_threshold, min_score, max_score

        Note:
            BSR = 0 is invalid (no sales data) and returns 0 score.
            BSR = 1 is the #1 bestseller in category.
        """
        # BSR 0 ou negatif est invalide - pas de donnees de vente
        if bsr is None or bsr <= 0:
            logger.debug(f"Invalid BSR value: {bsr} - returning 0 velocity score")
            return 0

        for tier in tiers:
            if bsr <= tier.bsr_threshold:
                # Return midpoint of tier range
                return (tier.min_score + tier.max_score) / 2

        # BSR trop eleve (hors de tous les tiers)
        return 0

    def _get_recommendation(
        self,
        roi_percent: float,
        velocity_score: float,
        config,
        strategy: Optional[str] = None
    ) -> str:
        """
        Determine recommendation based on ROI and velocity.

        Phase 8: Strategy-aware thresholds.
        - Default (smart_velocity): High velocity requirements (80/60/40)
        - textbooks_standard: Balanced velocity requirements (50/40/30)
        - textbooks_patience: Lower velocity requirements (40/30/20)

        Args:
            roi_percent: ROI percentage
            velocity_score: Velocity score (0-100)
            config: Effective config with ROI thresholds
            strategy: Strategy type for adjusted thresholds

        Returns:
            Recommendation: STRONG_BUY, BUY, CONSIDER, or SKIP
        """
        roi_config = config.effective_roi

        # Phase 8: Strategy-specific velocity thresholds
        # Default thresholds (Smart Velocity - BSR 10K-80K, fast rotation)
        velocity_thresholds = {
            "strong_buy": 80,
            "buy": 60,
            "consider": 40
        }

        # Textbook Standard: Balanced thresholds (BSR 100K-250K)
        # Rotation 7-14 days, moderate velocity expectations
        if strategy == "textbooks_standard":
            velocity_thresholds = {
                "strong_buy": 50,
                "buy": 40,
                "consider": 30
            }
        # Textbook Patience: Lower thresholds (BSR 250K-400K)
        # Rotation 4-6 weeks, slower velocity is acceptable
        elif strategy == "textbooks_patience":
            velocity_thresholds = {
                "strong_buy": 40,
                "buy": 30,
                "consider": 20
            }
        # Legacy textbooks
        elif strategy == "textbooks":
            velocity_thresholds = {
                "strong_buy": 50,
                "buy": 40,
                "consider": 30
            }

        if roi_percent >= float(roi_config.excellent_threshold) and velocity_score >= velocity_thresholds["strong_buy"]:
            return "STRONG_BUY"
        elif roi_percent >= float(roi_config.target) and velocity_score >= velocity_thresholds["buy"]:
            return "BUY"
        elif roi_percent >= float(roi_config.min_acceptable) and velocity_score >= velocity_thresholds["consider"]:
            return "CONSIDER"
        else:
            return "SKIP"