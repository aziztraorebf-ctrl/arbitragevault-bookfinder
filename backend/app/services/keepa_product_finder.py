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

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import logging
import json

import httpx

from app.services.config_service import ConfigService
from app.services.keepa_service import KeepaService
from app.schemas.config import CategoryConfig

logger = logging.getLogger(__name__)


class KeepaProductFinderService:
    """
    Service pour découvrir produits via Keepa REST API.

    Utilise l'API directe Keepa pour production.
    """

    def __init__(self, keepa_service: KeepaService, config_service: ConfigService):
        """
        Initialize Product Finder.

        Args:
            keepa_service: Service Keepa existant (avec httpx client)
            config_service: Service Config pour filtres business
        """
        self.keepa_service = keepa_service
        self.config_service = config_service

    async def discover_products(
        self,
        domain: int,
        category: Optional[int] = None,
        bsr_min: Optional[int] = None,
        bsr_max: Optional[int] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        max_results: int = 100
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

        Returns:
            Liste d'ASINs découverts

        Strategy:
            1. Si category fournie → bestsellers endpoint
            2. Sinon → deals endpoint
            3. Filtrer par BSR/prix
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
                    max_results=max_results
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
        max_results: int
    ) -> List[str]:
        """
        Découvrir via bestsellers endpoint.

        Keepa API: /bestsellers
        Returns: Array of ASINs (up to 100,000)
        Cost: 50 tokens per request
        """
        try:
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

            # Si on a des filtres BSR/prix, on doit récupérer les détails
            if bsr_min or bsr_max or price_min or price_max:
                # Batch retrieve pour filtrer
                filtered_asins = await self._filter_asins_by_criteria(
                    domain=domain,
                    asins=asins[:500],  # Limite pour éviter trop de tokens
                    bsr_min=bsr_min,
                    bsr_max=bsr_max,
                    price_min=price_min,
                    price_max=price_max
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
        price_max: Optional[float]
    ) -> List[str]:
        """
        Filtrer ASINs par critères BSR/prix.

        Récupère les détails produits et filtre.
        """
        if not asins:
            return []

        filtered_asins = []

        # Batch retrieve (max 100 per request)
        for i in range(0, len(asins), 100):
            batch = asins[i:i+100]

            try:
                # Get product details
                products = await self.keepa_service.get_products(
                    asin_list=batch,
                    domain=domain,
                    stats=1,  # Include stats for BSR
                    history=0  # No history needed
                )

                # Filter by criteria
                for product in products:
                    # Extract BSR and price
                    stats = product.get("stats", {})
                    current = stats.get("current", [None, None, None, None])

                    price_cents = current[0] if len(current) > 0 else None
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

                    # Product passes filters
                    asin = product.get("asin")
                    if asin:
                        filtered_asins.append(asin)

            except Exception as e:
                logger.error(f"Error filtering batch: {e}")
                continue

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
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Découvre produits avec scoring complet.

        Applique Config Service filters et retourne produits scorés.

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
        # Step 1: Discover ASINs
        asins = await self.discover_products(
            domain=domain,
            category=category,
            bsr_min=bsr_min,
            bsr_max=bsr_max,
            price_min=price_min,
            price_max=price_max,
            max_results=max_results * 2  # Get more for filtering
        )

        if not asins:
            logger.warning("No ASINs discovered")
            return []

        # Step 2: Get product details
        products = await self.keepa_service.get_products(
            asin_list=asins,
            domain=domain,
            stats=1,
            history=1  # Need history for velocity
        )

        # Step 3: Apply scoring and filters
        scored_products = []

        # Get effective config
        effective_config = self.config_service.get_effective_config(category_id=category)

        for product in products:
            try:
                # Extract metrics
                asin = product.get("asin")
                title = product.get("title", "Unknown")

                stats = product.get("stats", {})
                current = stats.get("current", [None, None, None, None])

                price_cents = current[0] if len(current) > 0 else None
                bsr = current[3] if len(current) > 3 else None

                if not price_cents or not bsr:
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

                scored_products.append({
                    "asin": asin,
                    "title": title[:100],  # Truncate long titles
                    "price": float(price),
                    "bsr": bsr,
                    "roi_percent": roi_percent,
                    "velocity_score": velocity_score,
                    "recommendation": recommendation
                })

            except Exception as e:
                logger.error(f"Error scoring product {asin}: {e}")
                continue

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
        Calculer velocity score basé sur BSR et tiers.

        Returns score 0-100.
        """
        for tier in tiers:
            if bsr <= tier.bsr_threshold:
                # Return midpoint of tier range
                return (tier.min_score + tier.max_score) / 2

        # BSR trop élevé
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