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
FILTERING_COST_PER_ASIN = 1  # tokens per ASIN in filtering


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
        max_fba_sellers: Optional[int] = None
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

        Returns:
            Liste d'ASINs découverts

        Strategy:
            1. Si category fournie → bestsellers endpoint
            2. Sinon → deals endpoint
            3. Filtrer par BSR/prix/competition
            4. Retourner top N ASINs
        """
        discovered_asins: List[str] = []

        try:
            if category:
                # Strategy 1: Bestsellers par catégorie
                logger.info(f"Discovering via bestsellers - Category {category}")
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
                # Strategy 2: Deals actifs
                logger.info("Discovering via current deals")
                discovered_asins = await self._discover_via_deals(
                    domain=domain,
                    price_min=price_min,
                    price_max=price_max,
                    max_results=max_results
                )

            logger.info(f"Discovered {len(discovered_asins)} ASINs")
            return discovered_asins[:max_results]

        except Exception as e:
            logger.error(f"Product discovery error: {e}")
            raise

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
        Découvrir via bestsellers endpoint.

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
        exclude_amazon_seller: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Découvre produits avec scoring complet.

        Applique Config Service filters et retourne produits scorés.

        Args:
            force_refresh: If True, bypasses cache for product data
            max_fba_sellers: Maximum FBA sellers allowed (competition filter)
            exclude_amazon_seller: If True, exclude products where Amazon is a seller.
                                   Default: True (recommended for arbitrage).

        Returns:
            Liste de produits avec métriques :
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
                max_fba_sellers=max_fba_sellers
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

        for product in products:
            try:
                asin = product.get("asin")
                if not asin:
                    continue

                # Try scoring cache first (skip if force_refresh)
                cached_scoring = None
                if self.cache_service and not force_refresh:
                    cached_scoring = await self.cache_service.get_scoring_cache(asin)

                if cached_scoring and not force_refresh:
                    # Cache HIT - use cached scoring
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

                    # Get recommendation
                    recommendation = self._get_recommendation(
                        roi_percent,
                        velocity_score,
                        effective_config
                    )

                    scoring_result = {
                        "asin": asin,
                        "title": title[:100],  # Truncate long titles
                        "price": float(price),
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


        # Sort by combined score (ROI + Velocity)
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
        config
    ) -> str:
        """
        Déterminer recommandation basée sur ROI et velocity.
        """
        roi_config = config.effective_roi

        # Combined score
        combined = roi_percent * 0.6 + velocity_score * 0.4

        if roi_percent >= float(roi_config.excellent_threshold) and velocity_score >= 80:
            return "STRONG_BUY"
        elif roi_percent >= float(roi_config.target) and velocity_score >= 60:
            return "BUY"
        elif roi_percent >= float(roi_config.min_acceptable) and velocity_score >= 40:
            return "CONSIDER"
        else:
            return "SKIP"