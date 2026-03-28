"""
AutoSourcing Service - Core business logic for intelligent product discovery.
Integrates Keepa Product Finder with advanced scoring system v1.5.0.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from fastapi import HTTPException
from app.services.autosourcing_scoring import (
    calculate_product_roi,
    evaluate_condition_signal,
    calculate_velocity_from_keepa,
    calculate_stability_from_keepa,
    calculate_confidence_from_keepa,
    compute_rating,
    meets_criteria,
    classify_product_tier,
    should_reject_by_competition,
    should_reject_by_profit_floor,
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload

from app.models.autosourcing import (
    AutoSourcingJob, AutoSourcingPick, SavedProfile,
    JobStatus, ActionStatus
)
from app.services.keepa_service import KeepaService
from app.services.webhook_service import dispatch_webhook
from app.services.business_config_service import BusinessConfigService
from app.services.keepa_product_finder import KeepaProductFinderService
from app.services.config_adapter import get_config_adapter
from app.core.calculations import (
    calculate_roi_metrics,
    compute_advanced_velocity_score,
    compute_advanced_stability_score,
    compute_advanced_confidence_score,
    compute_overall_rating
)
from app.core.exceptions import AppException, InsufficientTokensError
from app.schemas.autosourcing_safeguards import TIMEOUT_PER_JOB
from app.config.keepa_categories import (
    get_category_id,
    get_category_config,
    KEEPA_CATEGORIES,
    LEGACY_CATEGORY_MAPPING
)

logger = logging.getLogger(__name__)


class AutoSourcingService:
    """
    Service for intelligent product discovery and management.
    Orchestrates Keepa discovery, advanced scoring, and user actions.
    """

    def __init__(self, db_session: AsyncSession, keepa_service: KeepaService):
        self.db = db_session
        self.keepa_service = keepa_service
        self.business_config = BusinessConfigService()
        # Phase 7: Use KeepaProductFinderService (REST API) instead of keepa lib
        config_adapter = get_config_adapter()
        self.product_finder = KeepaProductFinderService(
            keepa_service=keepa_service,
            config_service=config_adapter,
            db=db_session
        )

    async def run_custom_search(
        self,
        discovery_config: Dict[str, Any],
        scoring_config: Dict[str, Any],
        profile_name: str,
        profile_id: Optional[UUID] = None
    ) -> AutoSourcingJob:
        """
        Run a custom AutoSourcing search with user-defined criteria.

        Args:
            discovery_config: Keepa search parameters
            scoring_config: Advanced scoring thresholds
            profile_name: Name for this search job
            profile_id: Optional saved profile ID

        Returns:
            AutoSourcingJob with results populated

        Raises:
            InsufficientTokensError: If tokens insufficient for job
        """
        # Explicit token check for batch job
        check = await self.keepa_service.can_perform_action("auto_sourcing_job")

        if not check["can_proceed"]:
            logger.warning(
                f"Insufficient tokens for AutoSourcing job: "
                f"balance={check['current_balance']}, required={check['required_tokens']}"
            )
            raise InsufficientTokensError(
                current_balance=check["current_balance"],
                required_tokens=check["required_tokens"],
                endpoint="auto_sourcing_job"
            )

        logger.info(
            f"AutoSourcing job starting with sufficient tokens: "
            f"balance={check['current_balance']}, required={check['required_tokens']}"
        )

        logger.info(f"Starting AutoSourcing job: {profile_name}")

        # Create job record
        job = AutoSourcingJob(
            profile_name=profile_name,
            profile_id=profile_id,
            discovery_config=discovery_config,
            scoring_config=scoring_config,
            status=JobStatus.RUNNING,
            launched_at=datetime.utcnow()
        )

        logger.debug(f"Adding job to session: {profile_name}")
        self.db.add(job)
        logger.debug(f"Committing job creation...")
        await self.db.commit()
        logger.debug(f"Refreshing job from DB...")
        await self.db.refresh(job)
        logger.debug(f"Job created with ID: {job.id}")

        start_time = datetime.utcnow()

        try:
            # Timeout protection INSIDE service to guarantee DB update
            async with asyncio.timeout(TIMEOUT_PER_JOB):
                # Phase 1: Discover products via Keepa
                logger.info("Phase 1: Product discovery via Keepa")
                discovered_asins = await self._discover_products(discovery_config)
                logger.info("pipeline discover: %d ASINs found", len(discovered_asins))

                logger.info(f"Discovered {len(discovered_asins)} products (may include duplicates)")

                # Phase 1.5: Deduplicate ASINs to prevent analyzing same product multiple times
                logger.info("Phase 1.5: ASIN deduplication")
                unique_asins = await self.process_asins_with_deduplication(
                    discovered_asins,
                    max_to_analyze=discovery_config.get("max_results", 50)
                )
                logger.info("pipeline dedup: %d ASINs after deduplication", len(unique_asins))

                job.total_tested = len(unique_asins)
                logger.info(f"After deduplication: {len(unique_asins)} unique products to analyze")

                # Phase 2: Score and filter products
                logger.info("Phase 2: Advanced scoring and filtering")
                scored_picks = await self._score_and_filter_products(
                    unique_asins, scoring_config, job.id
                )
                logger.info("pipeline score: %d products scored", len(scored_picks))

                job.total_selected = len(scored_picks)
                logger.info(f"Selected {len(scored_picks)} top opportunities")

                # Phase 3: Remove duplicates from recent jobs
                logger.info("Phase 3: Duplicate detection")
                unique_picks = await self._remove_recent_duplicates(scored_picks)
                logger.info("pipeline final: %d picks selected (roi_min=%.1f)", len(unique_picks), scoring_config.get("roi_min", 0))

                final_count = len(unique_picks)
                logger.info(f"Final results: {final_count} unique opportunities")

                # Save results
                self.db.add_all(unique_picks)

                # Update job status
                end_time = datetime.utcnow()
                job.duration_ms = int((end_time - start_time).total_seconds() * 1000)
                job.completed_at = end_time
                job.status = JobStatus.SUCCESS
                job.total_selected = final_count

                logger.debug(f"Final commit before return...")
                await self.db.commit()

                # Reload job with picks relationship eagerly loaded to prevent MissingGreenlet
                # when FastAPI serializes the response
                logger.debug(f"Reloading job {job.id} with picks relationship...")
                from sqlalchemy import select
                from sqlalchemy.orm import selectinload

                result = await self.db.execute(
                    select(AutoSourcingJob)
                    .where(AutoSourcingJob.id == job.id)
                    .options(selectinload(AutoSourcingJob.picks))
                )
                job = result.scalar_one()

                logger.info(f"AutoSourcing job completed successfully: {job.id}")

                asyncio.create_task(dispatch_webhook(job=job))

                return job

        except asyncio.TimeoutError:
            # Update job status BEFORE raising exception
            job.status = JobStatus.ERROR
            job.error_message = f"Job exceeded timeout limit ({TIMEOUT_PER_JOB} seconds)"
            job.completed_at = datetime.utcnow()
            job.duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self.db.commit()

            logger.warning(f"Job {job.id} exceeded timeout ({TIMEOUT_PER_JOB}s)")

            raise HTTPException(
                status_code=408,
                detail=f"Job exceeded timeout limit ({TIMEOUT_PER_JOB} seconds)"
            )

        except HTTPException:
            # Re-raise HTTP exceptions (e.g. from timeout above) without wrapping
            raise

        except Exception as e:
            logger.error(f"AutoSourcing job failed: {str(e)}")

            # Update job with error
            job.status = JobStatus.ERROR
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            job.duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            await self.db.commit()
            raise AppException(f"AutoSourcing job failed: {str(e)}")

    async def _discover_products(self, discovery_config: Dict[str, Any]) -> List[str]:
        """
        Discover products using KeepaProductFinderService (REST API).

        Phase 7 Fix: Uses REST API directly instead of keepa Python library.
        This is MUCH faster and more reliable.

        Args:
            discovery_config: Search criteria for Keepa

        Returns:
            List of ASINs discovered

        Raises:
            Exception: If Keepa Product Finder API fails (no silent fallback)
        """
        # Extract parameters from discovery_config
        max_results = discovery_config.get("max_results", 50)

        # Map category name to Keepa category ID using CENTRALIZED CONFIG
        # All IDs validated via Keepa /category API on 2025-12-07
        # Source of truth: app/config/keepa_categories.py
        categories = discovery_config.get("categories", [])

        # Default to Books root (validated ID from centralized config)
        default_category_id = KEEPA_CATEGORIES["books"]["id"]  # 283155
        category_id = default_category_id

        if categories:
            first_cat = categories[0] if isinstance(categories, list) else categories
            try:
                # Use centralized config with validation
                category_id = get_category_id(first_cat)
                logger.info(f"Category '{first_cat}' resolved to ID {category_id} from centralized config")
            except KeyError as e:
                logger.warning(f"Unknown category '{first_cat}', using default Books: {e}")
                category_id = default_category_id

        # Extract BSR range
        bsr_range = discovery_config.get("bsr_range", {})
        bsr_min = bsr_range.get("min") if isinstance(bsr_range, dict) else None
        bsr_max = bsr_range.get("max") if isinstance(bsr_range, dict) else None
        # Handle list format [min, max]
        if isinstance(bsr_range, list) and len(bsr_range) >= 2:
            bsr_min, bsr_max = bsr_range[0], bsr_range[1]

        # Extract price range
        price_range = discovery_config.get("price_range", {})
        price_min = price_range.get("min") if isinstance(price_range, dict) else None
        price_max = price_range.get("max") if isinstance(price_range, dict) else None
        # Handle list format [min, max]
        if isinstance(price_range, list) and len(price_range) >= 2:
            price_min, price_max = price_range[0], price_range[1]

        # Extract competition filters
        # max_fba_sellers intentionally None at discovery stage — let scoring handle competition filtering.
        # Applying a strict FBA cap (e.g. 5) here reduces the candidate pool to near-zero on bestsellers.
        max_fba_sellers = discovery_config.get("max_fba_sellers", None)
        exclude_amazon = discovery_config.get("exclude_amazon_seller", True)  # Default: exclude Amazon

        logger.info(
            f"Calling KeepaProductFinderService (REST API): "
            f"category={category_id}, bsr=[{bsr_min}-{bsr_max}], price=[{price_min}-{price_max}], "
            f"max_fba={max_fba_sellers}, exclude_amazon={exclude_amazon}"
        )

        # Call ProductFinder REST API - FAST and reliable
        # Phase 7 Fix: Pass competition filters to avoid Phase 6 issue
        discovered_asins = await self.product_finder.discover_products(
            domain=1,  # US
            category=category_id,
            bsr_min=bsr_min,
            bsr_max=bsr_max,
            price_min=price_min,
            price_max=price_max,
            max_results=max_results,
            max_fba_sellers=max_fba_sellers,
            exclude_amazon_seller=exclude_amazon
        )

        logger.info(f"ProductFinder REST API returned {len(discovered_asins)} ASINs")
        return discovered_asins

    async def process_asins_with_deduplication(
        self,
        asins: List[str],
        max_to_analyze: int = None
    ) -> List[str]:
        """
        Deduplicate ASINs to prevent analyzing the same product multiple times.

        Args:
            asins: List of ASINs (may contain duplicates, None, or empty strings)
            max_to_analyze: Optional limit on unique products (<=0 returns empty)

        Returns:
            List of unique ASINs preserving first occurrence order
        """
        # Handle None/empty input
        if not asins:
            return []

        # Use max_to_analyze from safeguards if not specified
        if max_to_analyze is None:
            from app.schemas.autosourcing_safeguards import MAX_PRODUCTS_PER_SEARCH
            max_to_analyze = MAX_PRODUCTS_PER_SEARCH

        # Handle invalid max_to_analyze (<=0 returns empty)
        if max_to_analyze <= 0:
            logger.warning(f"Invalid max_to_analyze={max_to_analyze}, returning empty")
            return []

        # Track seen ASINs to preserve order of first occurrences
        seen = set()
        unique_asins = []

        for asin in asins:
            # Skip None and empty strings (hostile input protection)
            if not asin or not isinstance(asin, str):
                logger.debug(f"Skipping invalid ASIN: {asin}")
                continue

            # Skip if already seen (duplicate)
            if asin in seen:
                logger.debug(f"Skipping duplicate ASIN: {asin}")
                continue

            # Stop if reached max limit
            if len(unique_asins) >= max_to_analyze:
                logger.info(f"Reached max unique ASINs limit: {max_to_analyze}")
                break

            # Add to results
            seen.add(asin)
            unique_asins.append(asin)

        duplicates_removed = len(asins) - len(unique_asins)
        logger.info(
            f"Deduplication: {len(unique_asins)} unique ASINs from {len(asins)} input "
            f"({duplicates_removed} duplicates removed)"
        )

        return unique_asins

    async def _fetch_products_batch(
        self,
        asins: List[str],
        domain: int = 1,
        batch_size: int = 50
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch product data for multiple ASINs using batch REST API.

        This uses the same approach as KeepaProductFinderService for efficiency.
        Instead of individual api.query() calls, we use /product endpoint with comma-separated ASINs.

        Args:
            asins: List of ASINs to fetch
            domain: Keepa domain ID (1=US)
            batch_size: Max ASINs per batch request (Keepa limit is 100)

        Returns:
            Dict mapping ASIN to raw Keepa product data
        """
        results = {}

        # Process in batches
        for i in range(0, len(asins), batch_size):
            batch = asins[i:i + batch_size]

            try:
                # Pre-check budget for batch product request
                batch_cost = len(batch)  # 1 token per ASIN
                await self.keepa_service._ensure_sufficient_balance(
                    estimated_cost=batch_cost,
                    endpoint_name=f"autosourcing_product_batch_{len(batch)}"
                )

                # Use REST API batch request (same as keepa_product_finder.py)
                endpoint = "/product"
                params = {
                    "domain": domain,
                    "asin": ",".join(batch),  # Comma-separated ASINs for batch
                    "stats": 1,  # Include stats for BSR, prices
                    "history": 0  # No history needed for scoring
                }

                response = await self.keepa_service._make_request(endpoint, params)
                products = response.get("products", []) if response else []

                # Map results by ASIN
                for product in products:
                    asin = product.get("asin")
                    if asin:
                        results[asin] = product

                logger.info(f"Batch fetched {len(products)}/{len(batch)} products")

            except InsufficientTokensError as e:
                logger.error(f"Insufficient tokens for batch: {e}")
                raise
            except Exception as e:
                logger.error(f"Error fetching batch: {e}")
                continue

        return results

    async def _score_and_filter_products(
        self,
        asins: List[str],
        scoring_config: Dict[str, Any],
        job_id: UUID
    ) -> List[AutoSourcingPick]:
        """
        Score products using advanced scoring system and filter by thresholds.

        Uses batch REST API for efficiency (same approach as NicheDiscovery).

        Args:
            asins: List of ASINs to score
            scoring_config: Scoring thresholds
            job_id: Parent job ID

        Returns:
            List of AutoSourcingPick objects meeting criteria
        """
        config = await self.business_config.get_effective_config(domain_id=1, category="books")
        picks = []

        # Enrich scoring_config with strategy thresholds so compute_rating()
        # and meets_criteria() use calibrated values instead of hardcoded defaults.
        strategy_name = config.get("active_strategy", "balanced")
        strategy = config.get("strategies", {}).get(strategy_name, {})
        enriched_scoring = {**scoring_config}
        enriched_scoring.setdefault("velocity_min", strategy.get("velocity_min", 40))
        enriched_scoring.setdefault("stability_min", strategy.get("stability_min", 50))
        enriched_scoring.setdefault("confidence_min", 50)
        enriched_scoring.setdefault("rating_required", "FAIR")

        # BATCH FETCH: Get all product data in one API call instead of individual queries
        logger.info(f"Fetching {len(asins)} products via batch REST API...")
        products_data = await self._fetch_products_batch(asins)
        logger.info(f"Batch fetch returned data for {len(products_data)} ASINs")

        for asin in asins:
            try:
                # Get product data from batch results
                raw_keepa = products_data.get(asin)

                if not raw_keepa:
                    logger.debug(f"No data for {asin} in batch results, skipping")
                    continue

                # Score product using batch data
                pick = await self._analyze_product_from_batch(
                    asin, raw_keepa, enriched_scoring, job_id, config
                )

                if pick and meets_criteria(pick, enriched_scoring):
                    picks.append(pick)
                    logger.debug(f"PASS {asin}: {pick.overall_rating} (ROI: {pick.roi_percentage}%)")
                else:
                    logger.debug(f"REJECT {asin}: Does not meet criteria")

            except Exception as e:
                logger.warning(f"Error scoring {asin}: {str(e)}")
                continue

        # Sort by ROI descending and limit results
        picks.sort(key=lambda x: x.roi_percentage, reverse=True)
        max_picks = scoring_config.get("max_results", 20)

        return picks[:max_picks]

    async def _analyze_product_from_batch(
        self,
        asin: str,
        raw_keepa: Dict[str, Any],
        scoring_config: Dict[str, Any],
        job_id: UUID,
        business_config: Dict[str, Any]
    ) -> Optional[AutoSourcingPick]:
        """
        Analyze a product using pre-fetched batch data.

        This is similar to _analyze_single_product but uses data already fetched
        via batch REST API instead of making individual Keepa queries.
        """
        try:
            # Extract REAL data from Keepa response
            product_data = self._extract_product_data_from_keepa(raw_keepa)

            # Debug: Log extraction results
            logger.info(f"Extracted {asin}: price={product_data.get('current_price')}, bsr={product_data.get('bsr')}")

            if not product_data.get("current_price"):
                logger.warning(f"No valid price for {asin}, skipping (raw stats: {raw_keepa.get('stats', {}).get('current', [])[:5]})")
                return None

            title = product_data.get("title", f"Product {asin}")
            current_price = product_data["current_price"]
            bsr = product_data.get("bsr", 0)
            category = product_data.get("category", "Unknown")

            # Phase 7: Extract competition data
            fba_seller_count = product_data.get("fba_seller_count")
            amazon_on_listing = product_data.get("amazon_on_listing", False)

            # Unified source_price_factor: 0.40 = buy at 40% of sell price
            # (online arbitrage model 2026, calibrated from market data).
            # Override via business_config or DB seed.
            source_price_factor = business_config.get("source_price_factor", 0.40)
            fba_fee_percentage = business_config.get("fba_fee_percentage", 0.22)
            estimated_cost, profit_net, roi_percentage = calculate_product_roi(
                current_price, source_price_factor, fba_fee_percentage
            )

            # --- Strategy filters (BSR, competition, profit floor) ---
            strategy_config = business_config.get("strategies", {}).get(
                business_config.get("active_strategy", "balanced"), {}
            )

            max_bsr = strategy_config.get("max_bsr")
            if max_bsr and bsr > max_bsr:
                logger.info(
                    "Skipping %s: BSR %d > max %d",
                    asin, bsr, max_bsr,
                )
                return None

            max_fba_sellers = strategy_config.get("max_fba_sellers")
            if should_reject_by_competition(fba_seller_count, max_fba_sellers):
                logger.info(
                    "Skipping %s: too many FBA sellers (%s > %s)",
                    asin, fba_seller_count, max_fba_sellers,
                )
                return None

            min_profit_dollars = strategy_config.get("min_profit_dollars")
            if should_reject_by_profit_floor(profit_net, min_profit_dollars):
                logger.info(
                    "Skipping %s: profit $%.2f below floor $%.2f",
                    asin, profit_net, min_profit_dollars,
                )
                return None

            used_roi_percentage, condition_signal = evaluate_condition_signal(
                product_data, estimated_cost, fba_fee_percentage,
                business_config.get("condition_signals", {}),
            )

            # Calculate advanced scores from REAL Keepa data
            velocity_score = calculate_velocity_from_keepa(raw_keepa, bsr)
            stability_score = calculate_stability_from_keepa(raw_keepa)
            confidence_score = calculate_confidence_from_keepa(
                raw_keepa,
                condition_signal=condition_signal,
                business_config=business_config.get("condition_signals", {})
            )

            # Overall rating based on scoring config
            overall_rating = compute_rating(
                roi_percentage, velocity_score, stability_score,
                confidence_score, scoring_config
            )

            # Create readable summary
            readable_summary = f"{overall_rating}: {roi_percentage:.1f}% ROI, BSR {bsr:,}, {velocity_score:.0f} velocity"

            # Classify product tier (v1.7.0 AutoScheduler)
            tier, tier_reason = classify_product_tier({
                'roi_percentage': roi_percentage,
                'profit_net': profit_net,
                'velocity_score': velocity_score,
                'confidence_score': confidence_score,
                'overall_rating': overall_rating
            })

            # Create AutoSourcingPick with REAL data
            pick = AutoSourcingPick(
                job_id=job_id,
                asin=asin,
                title=title,
                current_price=current_price,
                estimated_buy_cost=estimated_cost,
                profit_net=profit_net,
                roi_percentage=roi_percentage,
                velocity_score=int(velocity_score),
                stability_score=int(stability_score),
                confidence_score=int(confidence_score),
                overall_rating=overall_rating,
                bsr=bsr,
                category=category,
                readable_summary=readable_summary,
                # AutoScheduler tier classification
                priority_tier=tier,
                tier_reason=tier_reason,
                is_featured=(tier == "HOT"),
                # Phase 7: Competition data
                fba_seller_count=fba_seller_count,
                amazon_on_listing=amazon_on_listing,
                # Condition-based scoring signals
                used_price=product_data.get("used_price"),
                used_offer_count=product_data.get("used_offer_count"),
                used_roi_percentage=used_roi_percentage,
                condition_signal=condition_signal
            )

            logger.info(
                f"Analyzed {asin}: {overall_rating}, ROI={roi_percentage:.1f}%, BSR={bsr}, "
                f"FBA={fba_seller_count}, Amazon={amazon_on_listing}, "
                f"used_roi={used_roi_percentage}, condition={condition_signal}"
            )
            return pick

        except Exception as e:
            logger.error(f"Error analyzing {asin} from batch: {str(e)}")
            return None

    async def _analyze_single_product(
        self,
        asin: str,
        scoring_config: Dict[str, Any],
        job_id: UUID,
        business_config: Dict[str, Any]
    ) -> Optional[AutoSourcingPick]:
        """
        Analyze a single product with advanced scoring using REAL Keepa data.

        Args:
            asin: Product ASIN to analyze
            scoring_config: Scoring thresholds and weights
            job_id: Parent job UUID
            business_config: Business parameters (fees, costs)

        Returns:
            AutoSourcingPick with real Keepa data, or None if unavailable
        """
        try:
            # REAL KEEPA INTEGRATION - Get actual product data
            raw_keepa = await self.keepa_service.get_product_data(asin)

            if not raw_keepa:
                logger.warning(f"No Keepa data available for {asin}")
                return None

            # Extract REAL data from Keepa response
            product_data = self._extract_product_data_from_keepa(raw_keepa)

            if not product_data.get("current_price"):
                logger.warning(f"No valid price for {asin}, skipping")
                return None

            title = product_data.get("title", f"Product {asin}")
            current_price = product_data["current_price"]
            bsr = product_data.get("bsr", 0)
            category = product_data.get("category", "Unknown")

            # Phase 7: Extract competition data
            fba_seller_count = product_data.get("fba_seller_count")
            amazon_on_listing = product_data.get("amazon_on_listing", False)

            # Unified source_price_factor: 0.40 = buy at 40% of sell price
            # (online arbitrage model 2026, calibrated from market data).
            source_price_factor = business_config.get("source_price_factor", 0.40)
            fba_fee_percentage = business_config.get("fba_fee_percentage", 0.22)
            estimated_cost, profit_net, roi_percentage = calculate_product_roi(
                current_price, source_price_factor, fba_fee_percentage
            )

            # --- Strategy filters (BSR, competition, profit floor) ---
            strategy_config = business_config.get("strategies", {}).get(
                business_config.get("active_strategy", "balanced"), {}
            )

            max_bsr = strategy_config.get("max_bsr")
            if max_bsr and bsr > max_bsr:
                logger.info(
                    "Skipping %s: BSR %d > max %d",
                    asin, bsr, max_bsr,
                )
                return None

            max_fba_sellers = strategy_config.get("max_fba_sellers")
            if should_reject_by_competition(fba_seller_count, max_fba_sellers):
                logger.info(
                    "Skipping %s: too many FBA sellers (%s > %s)",
                    asin, fba_seller_count, max_fba_sellers,
                )
                return None

            min_profit_dollars = strategy_config.get("min_profit_dollars")
            if should_reject_by_profit_floor(profit_net, min_profit_dollars):
                logger.info(
                    "Skipping %s: profit $%.2f below floor $%.2f",
                    asin, profit_net, min_profit_dollars,
                )
                return None

            used_roi_percentage, condition_signal = evaluate_condition_signal(
                product_data, estimated_cost, fba_fee_percentage,
                business_config.get("condition_signals", {}),
            )

            # Calculate advanced scores from REAL Keepa data
            velocity_score = calculate_velocity_from_keepa(raw_keepa, bsr)
            stability_score = calculate_stability_from_keepa(raw_keepa)
            confidence_score = calculate_confidence_from_keepa(
                raw_keepa,
                condition_signal=condition_signal,
                business_config=business_config.get("condition_signals", {})
            )

            # Overall rating based on scoring config
            overall_rating = compute_rating(
                roi_percentage, velocity_score, stability_score,
                confidence_score, scoring_config
            )

            # Create readable summary
            readable_summary = f"{overall_rating}: {roi_percentage:.1f}% ROI, BSR {bsr:,}, {velocity_score:.0f} velocity"

            # Classify product tier (v1.7.0 AutoScheduler)
            tier, tier_reason = classify_product_tier({
                'roi_percentage': roi_percentage,
                'profit_net': profit_net,
                'velocity_score': velocity_score,
                'confidence_score': confidence_score,
                'overall_rating': overall_rating
            })

            # Create AutoSourcingPick with REAL data
            pick = AutoSourcingPick(
                job_id=job_id,
                asin=asin,
                title=title,
                current_price=current_price,
                estimated_buy_cost=estimated_cost,
                profit_net=profit_net,
                roi_percentage=roi_percentage,
                velocity_score=int(velocity_score),
                stability_score=int(stability_score),
                confidence_score=int(confidence_score),
                overall_rating=overall_rating,
                bsr=bsr,
                category=category,
                readable_summary=readable_summary,
                # AutoScheduler tier classification
                priority_tier=tier,
                tier_reason=tier_reason,
                is_featured=(tier == "HOT"),
                # Phase 7: Competition data
                fba_seller_count=fba_seller_count,
                amazon_on_listing=amazon_on_listing,
                # Condition-based scoring signals
                used_price=product_data.get("used_price"),
                used_offer_count=product_data.get("used_offer_count"),
                used_roi_percentage=used_roi_percentage,
                condition_signal=condition_signal
            )

            logger.info(
                f"Analyzed {asin}: {overall_rating}, ROI={roi_percentage:.1f}%, BSR={bsr}, "
                f"FBA={fba_seller_count}, Amazon={amazon_on_listing}, "
                f"used_roi={used_roi_percentage}, condition={condition_signal}"
            )
            return pick

        except Exception as e:
            logger.error(f"Error analyzing {asin}: {str(e)}")
            return None

    def _extract_product_data_from_keepa(self, raw_keepa: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured product data from raw Keepa response.

        Aligned with keepa_product_finder.py for REST API batch responses.
        stats.current[] indices:
          [0] = AMAZON price
          [1] = NEW price (3rd party - preferred)
          [2] = USED price
          [3] = Sales Rank (BSR)
          [11] = COUNT_NEW (FBA offers count)
        """
        result = {}

        # Title
        result["title"] = raw_keepa.get("title", "")

        # Extract from stats.current[] (REST API batch format)
        stats = raw_keepa.get("stats", {})
        current = stats.get("current", [])

        # Price: NEW price (index 1), fallback to AMAZON price (index 0)
        if len(current) > 1 and current[1] is not None and current[1] > 0:
            result["current_price"] = current[1] / 100.0  # NEW price in cents
        elif len(current) > 0 and current[0] is not None and current[0] > 0:
            result["current_price"] = current[0] / 100.0  # AMAZON price fallback

        # BSR: stats.current[3] (REST API format)
        if len(current) > 3 and current[3] is not None and current[3] > 0:
            result["bsr"] = current[3]

        # Category name: use the most specific (last) category in the tree
        category_tree = raw_keepa.get("categoryTree", [])
        if category_tree and len(category_tree) > 0:
            result["category"] = category_tree[-1].get("name", "Unknown")
        else:
            result["category"] = "Unknown"

        # Phase 7: Extract competition data
        # Amazon presence: availabilityAmazon = -1 means NOT selling, >=0 means selling
        availability_amazon = raw_keepa.get("availabilityAmazon", -1)
        result["amazon_on_listing"] = availability_amazon >= 0

        # FBA seller count: stats.offerCountFBA or current[11]
        fba_count = stats.get("offerCountFBA", -2)
        if fba_count is None or fba_count < 0:
            # Try current[11] = COUNT_NEW as fallback
            if len(current) > 11 and current[11] is not None and current[11] >= 0:
                fba_count = current[11]
            else:
                fba_count = None
        result["fba_seller_count"] = fba_count if fba_count is not None and fba_count >= 0 else None

        # Used price: stats.current[2] (USED price in cents)
        if len(current) > 2 and current[2] is not None and current[2] not in (-1, 0):
            result["used_price"] = current[2] / 100.0
        else:
            result["used_price"] = None

        # Used offer count: stats.offerCountUsed
        used_offer_count = stats.get("offerCountUsed", -2)
        if used_offer_count is None or used_offer_count == -2:
            result["used_offer_count"] = None
        else:
            result["used_offer_count"] = used_offer_count

        return result

    def get_diversified_search_criteria(self, hour: int) -> Dict[str, Any]:
        """
        Génère des critères de recherche diversifiés selon l'heure pour AutoScheduler.
        
        Args:
            hour: Heure actuelle (0-23)
            
        Returns:
            Critères de recherche adaptés à l'heure
        """
        # Profils de diversification par heure
        diversification_profiles = {
            8: {  # Matin: Conservateur, livres populaires
                "categories": ["Books"],
                "price_range": {"min": 10, "max": 35},
                "bsr_range": {"min": 1000, "max": 75000},
                "description": "Matin - Profil conservateur, livres populaires"
            },
            15: {  # Midi: Équilibré, opportunités moyennes  
                "categories": ["Books"],
                "price_range": {"min": 15, "max": 50},
                "bsr_range": {"min": 1000, "max": 150000},
                "description": "Midi - Profil équilibré, diversité moyenne"
            },
            20: {  # Soir: Agressif, large spectre BSR
                "categories": ["Books"], 
                "price_range": {"min": 20, "max": 60},
                "bsr_range": {"min": 1000, "max": 250000},  # BSR élargi pour + d'opportunités
                "description": "Soir - Profil agressif, large spectre BSR"
            }
        }
        
        # Retourne le profil correspondant à l'heure, ou profil par défaut
        profile = diversification_profiles.get(hour, diversification_profiles[15])
        
        logger.info(f"Profil diversifié pour {hour}h: {profile['description']}")
        return profile

    async def _remove_recent_duplicates(
        self, picks: List[AutoSourcingPick], days: int = 7
    ) -> List[AutoSourcingPick]:
        """Remove ASINs that were found in recent jobs."""
        
        if not picks:
            return picks
            
        # Get ASINs from recent jobs
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(AutoSourcingPick.asin)
            .join(AutoSourcingJob)
            .where(AutoSourcingJob.launched_at >= cutoff_date)
        )
        
        recent_asins = {row.asin for row in result}
        
        # Filter out duplicates
        unique_picks = [pick for pick in picks if pick.asin not in recent_asins]
        
        duplicates_count = len(picks) - len(unique_picks)
        if duplicates_count > 0:
            logger.info(f"Filtered {duplicates_count} recent duplicates")
            
        return unique_picks

    # ========================================================================
    # PROFILE MANAGEMENT
    # ========================================================================

    async def get_saved_profiles(self, active_only: bool = True) -> List[SavedProfile]:
        """Get all saved profiles."""
        
        query = select(SavedProfile)
        if active_only:
            query = query.where(SavedProfile.active == True)
            
        query = query.order_by(desc(SavedProfile.last_used_at), SavedProfile.name)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_profile(self, profile_data: Dict[str, Any]) -> SavedProfile:
        """Create a new saved profile."""
        
        profile = SavedProfile(
            name=profile_data["name"],
            description=profile_data.get("description"),
            discovery_config=profile_data["discovery_config"],
            scoring_config=profile_data["scoring_config"],
            max_results=profile_data.get("max_results", 20)
        )
        
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        
        logger.info(f"Created profile: {profile.name}")
        return profile

    async def update_profile_usage(self, profile_id: UUID) -> None:
        """Update profile usage statistics."""
        
        result = await self.db.execute(
            select(SavedProfile).where(SavedProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()
        
        if profile:
            profile.last_used_at = datetime.utcnow()
            profile.usage_count += 1
            await self.db.commit()

    # ========================================================================
    # QUICK ACTIONS
    # ========================================================================

    async def update_pick_action(
        self, 
        pick_id: UUID, 
        action: ActionStatus, 
        notes: Optional[str] = None
    ) -> AutoSourcingPick:
        """Update user action on a pick."""
        
        result = await self.db.execute(
            select(AutoSourcingPick).where(AutoSourcingPick.id == pick_id)
        )
        pick = result.scalar_one_or_none()
        
        if not pick:
            raise AppException(f"Pick {pick_id} not found")
        
        # Update action
        pick.action_status = action
        pick.action_taken_at = datetime.utcnow()
        pick.action_notes = notes
        
        # Update flags (is_purchased only set when explicitly purchased, not just "to_buy")
        pick.is_favorite = (action == ActionStatus.FAVORITE)
        pick.is_ignored = (action == ActionStatus.IGNORED)
        pick.analysis_requested = (action == ActionStatus.ANALYZING)
        
        await self.db.commit()
        await self.db.refresh(pick)
        
        logger.info(f"Updated pick {pick_id} action to {action.value}")
        return pick

    async def get_picks_by_action(self, action: ActionStatus) -> List[AutoSourcingPick]:
        """Get picks filtered by action status."""
        
        result = await self.db.execute(
            select(AutoSourcingPick)
            .where(AutoSourcingPick.action_status == action)
            .order_by(desc(AutoSourcingPick.action_taken_at))
            .options(selectinload(AutoSourcingPick.job))
        )
        
        return result.scalars().all()

    # ========================================================================
    # OPPORTUNITY OF THE DAY
    # ========================================================================

    async def get_opportunity_of_day(self) -> Optional[AutoSourcingPick]:
        """Get the best opportunity found today."""
        
        today = datetime.utcnow().date()
        
        result = await self.db.execute(
            select(AutoSourcingPick)
            .join(AutoSourcingJob)
            .where(
                and_(
                    func.date(AutoSourcingJob.launched_at) == today,
                    AutoSourcingJob.status == JobStatus.SUCCESS
                )
            )
            .order_by(desc(AutoSourcingPick.roi_percentage))
            .limit(1)
            .options(selectinload(AutoSourcingPick.job))
        )
        
        return result.scalar_one_or_none()

    # ========================================================================
    # JOB MANAGEMENT  
    # ========================================================================

    async def get_recent_jobs(self, limit: int = 10) -> List[AutoSourcingJob]:
        """Get recent AutoSourcing jobs."""
        
        result = await self.db.execute(
            select(AutoSourcingJob)
            .order_by(desc(AutoSourcingJob.launched_at))
            .limit(limit)
            .options(selectinload(AutoSourcingJob.picks))
        )
        
        return result.scalars().all()

    async def get_job_by_id(self, job_id: UUID) -> Optional[AutoSourcingJob]:
        """Get job with all picks."""
        
        result = await self.db.execute(
            select(AutoSourcingJob)
            .where(AutoSourcingJob.id == job_id)
            .options(selectinload(AutoSourcingJob.picks))
        )
        
        return result.scalar_one_or_none()

    async def get_latest_job(self) -> Optional[AutoSourcingJob]:
        """Get the most recent successful job."""
        
        result = await self.db.execute(
            select(AutoSourcingJob)
            .where(AutoSourcingJob.status == JobStatus.SUCCESS)
            .order_by(desc(AutoSourcingJob.completed_at))
            .limit(1)
            .options(selectinload(AutoSourcingJob.picks))
        )
        
        return result.scalar_one_or_none()