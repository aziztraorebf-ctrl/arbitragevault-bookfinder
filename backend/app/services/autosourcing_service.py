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

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload

from app.models.autosourcing import (
    AutoSourcingJob, AutoSourcingPick, SavedProfile,
    JobStatus, ActionStatus
)
from app.services.keepa_service import KeepaService
from app.services.business_config_service import BusinessConfigService
from app.core.calculations import (
    calculate_roi_metrics,
    compute_advanced_velocity_score,
    compute_advanced_stability_score, 
    compute_advanced_confidence_score,
    compute_overall_rating
)
from app.core.exceptions import AppException, InsufficientTokensError
from app.schemas.autosourcing_safeguards import TIMEOUT_PER_JOB

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

                logger.info(f"Discovered {len(discovered_asins)} products (may include duplicates)")

                # Phase 1.5: Deduplicate ASINs to prevent analyzing same product multiple times
                logger.info("Phase 1.5: ASIN deduplication")
                unique_asins = await self.process_asins_with_deduplication(
                    discovered_asins,
                    max_to_analyze=discovery_config.get("max_results", 50)
                )

                job.total_tested = len(unique_asins)
                logger.info(f"After deduplication: {len(unique_asins)} unique products to analyze")

                # Phase 2: Score and filter products
                logger.info("Phase 2: Advanced scoring and filtering")
                scored_picks = await self._score_and_filter_products(
                    unique_asins, scoring_config, job.id
                )

                job.total_selected = len(scored_picks)
                logger.info(f"Selected {len(scored_picks)} top opportunities")

                # Phase 3: Remove duplicates from recent jobs
                logger.info("Phase 3: Duplicate detection")
                unique_picks = await self._remove_recent_duplicates(scored_picks)

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
                return job

        except asyncio.TimeoutError:
            # Update job status BEFORE raising exception
            job.status = JobStatus.FAILED
            job.error_message = f"Job exceeded timeout limit ({TIMEOUT_PER_JOB} seconds)"
            job.completed_at = datetime.now(timezone.utc)
            job.duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            await self.db.commit()

            logger.warning(f"Job {job.id} exceeded timeout ({TIMEOUT_PER_JOB}s)")

            # Re-raise for router to handle HTTP 408
            raise HTTPException(
                status_code=408,
                detail=f"Job exceeded timeout limit ({TIMEOUT_PER_JOB} seconds)"
            )

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
        Discover products using Keepa Product Finder API.

        Args:
            discovery_config: Search criteria for Keepa

        Returns:
            List of ASINs discovered

        Raises:
            Exception: If Keepa Product Finder API fails (no silent fallback)
        """
        # Convert discovery config to Keepa Product Finder parameters
        keepa_params = await self._build_keepa_search_params(discovery_config)
        max_results = discovery_config.get("max_results", 50)

        # Call Keepa Product Finder API - NO fallback, fail explicitly
        logger.info("Calling Keepa Product Finder API...")
        discovered_asins = await self.keepa_service.find_products(
            search_criteria=keepa_params,
            domain=1,  # US domain
            max_results=max_results
        )

        logger.info(f"Keepa Product Finder returned {len(discovered_asins)} ASINs")
        return discovered_asins

    async def _build_keepa_search_params(self, discovery_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert user discovery config to Keepa Product Finder parameters.
        
        Args:
            discovery_config: User-defined search criteria
            
        Returns:
            Dictionary with Keepa API parameters
        """
        keepa_params = {}
        
        # Handle categories
        categories = discovery_config.get("categories", [])
        if categories:
            # Map common category names to Keepa category IDs
            category_mapping = {
                "Books": 1000,
                "Electronics": 172282,  
                "Textbooks": 465600,
                "Home & Kitchen": 1055398,
                "Sports & Outdoors": 3375251
            }
            
            category_ids = []
            for cat in categories:
                if cat in category_mapping:
                    category_ids.append(category_mapping[cat])
            
            if category_ids:
                keepa_params["categories_include"] = category_ids[0]  # Use first category
        
        # Handle BSR range
        bsr_range = discovery_config.get("bsr_range", {})
        if bsr_range:
            if "min" in bsr_range:
                keepa_params["avg30_SALES_gte"] = bsr_range["min"]
            if "max" in bsr_range:  
                keepa_params["avg30_SALES_lte"] = bsr_range["max"]
        
        # Handle price range
        price_range = discovery_config.get("price_range", {})
        if price_range:
            if "min" in price_range:
                keepa_params["current_NEW_gte"] = int(price_range["min"] * 100)  # Keepa uses cents
            if "max" in price_range:
                keepa_params["current_NEW_lte"] = int(price_range["max"] * 100)  # Keepa uses cents
        
        # Default sorting by current sales rank
        keepa_params["sort"] = ["current_SALES", "asc"]
        
        logger.info(f"Built Keepa search params: {keepa_params}")
        return keepa_params

    async def process_asins_with_deduplication(
        self,
        asins: List[str],
        max_to_analyze: int = None
    ) -> List[str]:
        """
        Deduplicate ASINs to prevent analyzing the same product multiple times.

        Args:
            asins: List of ASINs (may contain duplicates)
            max_to_analyze: Optional limit on unique products

        Returns:
            List of unique ASINs preserving first occurrence order
        """
        # Track seen ASINs to preserve order of first occurrences
        seen = set()
        unique_asins = []

        # Use max_to_analyze from safeguards if not specified
        if max_to_analyze is None:
            from app.schemas.autosourcing_safeguards import MAX_PRODUCTS_PER_SEARCH
            max_to_analyze = MAX_PRODUCTS_PER_SEARCH

        for asin in asins:
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

    async def _score_and_filter_products(
        self, 
        asins: List[str], 
        scoring_config: Dict[str, Any],
        job_id: UUID
    ) -> List[AutoSourcingPick]:
        """
        Score products using advanced scoring system and filter by thresholds.
        
        Args:
            asins: List of ASINs to score
            scoring_config: Scoring thresholds
            job_id: Parent job ID
            
        Returns:
            List of AutoSourcingPick objects meeting criteria
        """
        config = await self.business_config.get_effective_config(domain_id=1, category="books")
        picks = []
        
        for asin in asins:
            try:
                # Get product data from Keepa
                logger.debug(f"Scoring product: {asin}")
                
                # For simulation, we'll use the existing analyze_product logic
                # TODO: Integrate with real Keepa data
                pick = await self._analyze_single_product(asin, scoring_config, job_id, config)
                
                if pick and self._meets_criteria(pick, scoring_config):
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

            # Calculate estimated buy cost using unified source_price_factor
            # Default 0.50 = buy at 50% of sell price (FBM->FBA arbitrage, aligned with guide)
            source_price_factor = business_config.get("source_price_factor", 0.50)
            estimated_cost = current_price * source_price_factor

            # Calculate ROI metrics
            fba_fee_percentage = business_config.get("fba_fee_percentage", 0.15)
            amazon_fees = current_price * fba_fee_percentage
            profit_net = current_price - estimated_cost - amazon_fees
            roi_percentage = (profit_net / estimated_cost) * 100 if estimated_cost > 0 else 0

            # Calculate advanced scores from REAL Keepa data
            velocity_score = self._calculate_velocity_from_keepa(raw_keepa, bsr)
            stability_score = self._calculate_stability_from_keepa(raw_keepa)
            confidence_score = self._calculate_confidence_from_keepa(raw_keepa)

            # Overall rating based on scoring config
            overall_rating = self._compute_rating(
                roi_percentage, velocity_score, stability_score,
                confidence_score, scoring_config
            )

            # Create readable summary
            readable_summary = f"{overall_rating}: {roi_percentage:.1f}% ROI, BSR {bsr:,}, {velocity_score:.0f} velocity"

            # Classify product tier (v1.7.0 AutoScheduler)
            tier, tier_reason = self._classify_product_tier({
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
                is_featured=(tier == "HOT")
            )

            logger.info(f"Analyzed {asin}: {overall_rating}, ROI={roi_percentage:.1f}%, BSR={bsr}")
            return pick

        except Exception as e:
            logger.error(f"Error analyzing {asin}: {str(e)}")
            return None

    def _extract_product_data_from_keepa(self, raw_keepa: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured product data from raw Keepa response.

        Uses the same extraction logic as unified_analysis.py for consistency.
        """
        result = {}

        # Title
        result["title"] = raw_keepa.get("title", "")

        # Extract current price from stats.current[1] (NEW price in cents)
        stats = raw_keepa.get("stats", {})
        current_stats = stats.get("current", [])

        if current_stats and len(current_stats) > 1 and current_stats[1] is not None:
            # Keepa stores prices in cents, convert to dollars
            result["current_price"] = current_stats[1] / 100.0
        else:
            # Fallback: try csv data
            csv_data = raw_keepa.get("csv", [])
            if csv_data and len(csv_data) > 1:
                new_price_history = csv_data[1] if len(csv_data) > 1 else None
                if new_price_history and len(new_price_history) >= 2:
                    # Get last valid price
                    for i in range(len(new_price_history) - 1, -1, -2):
                        if new_price_history[i] is not None and new_price_history[i] > 0:
                            result["current_price"] = new_price_history[i] / 100.0
                            break

        # Extract BSR from salesRanks or stats
        sales_ranks = raw_keepa.get("salesRanks", {})
        root_category = raw_keepa.get("rootCategory")

        if sales_ranks and root_category:
            rank_history = sales_ranks.get(str(root_category), sales_ranks.get(root_category, []))
            if rank_history and len(rank_history) >= 2:
                # Get last BSR value (odd indices are values, even are timestamps)
                for i in range(len(rank_history) - 1, 0, -2):
                    if rank_history[i] is not None and rank_history[i] > 0:
                        result["bsr"] = rank_history[i]
                        break

        # Fallback: stats.current[18] for BSR
        if not result.get("bsr") and current_stats and len(current_stats) > 18:
            if current_stats[18] is not None and current_stats[18] > 0:
                result["bsr"] = current_stats[18]

        # Category name
        category_tree = raw_keepa.get("categoryTree", [])
        if category_tree and len(category_tree) > 0:
            result["category"] = category_tree[0].get("name", "Unknown")
        else:
            result["category"] = "Unknown"

        return result

    def _calculate_velocity_from_keepa(self, raw_keepa: Dict[str, Any], bsr: int) -> float:
        """Calculate velocity score from real Keepa data."""
        # Base velocity from BSR (lower BSR = higher velocity)
        if bsr <= 0:
            return 50.0

        # Logarithmic scale: BSR 1K = 100, BSR 100K = 50, BSR 1M = 10
        import math
        velocity = max(10, min(100, 130 - (math.log10(bsr) * 20)))

        # Boost from sales drops (stats.current[18] or salesRanks history)
        stats = raw_keepa.get("stats", {})
        current_stats = stats.get("current", [])

        # Check for recent sales activity
        if current_stats and len(current_stats) > 18 and current_stats[18]:
            # Sales drops indicate recent sales
            velocity = min(100, velocity + 10)

        return velocity

    def _calculate_stability_from_keepa(self, raw_keepa: Dict[str, Any]) -> float:
        """Calculate price stability score from real Keepa data."""
        stats = raw_keepa.get("stats", {})

        # Compare current vs avg30 prices
        current_stats = stats.get("current", [])
        avg30_stats = stats.get("avg30", [])

        if not current_stats or not avg30_stats:
            return 70.0  # Default

        # Check price stability (index 1 = NEW price)
        if len(current_stats) > 1 and len(avg30_stats) > 1:
            current_price = current_stats[1]
            avg30_price = avg30_stats[1]

            if current_price and avg30_price and avg30_price > 0:
                # Calculate price variance ratio
                variance = abs(current_price - avg30_price) / avg30_price
                # Lower variance = higher stability (0% variance = 100, 50% variance = 50)
                stability = max(30, min(100, 100 - (variance * 100)))
                return stability

        return 70.0

    def _calculate_confidence_from_keepa(self, raw_keepa: Dict[str, Any]) -> float:
        """Calculate confidence score from real Keepa data completeness."""
        confidence = 50.0  # Base confidence

        # Check data completeness
        if raw_keepa.get("title"):
            confidence += 10

        stats = raw_keepa.get("stats", {})
        if stats.get("current"):
            confidence += 15
        if stats.get("avg30"):
            confidence += 10

        if raw_keepa.get("salesRanks"):
            confidence += 10

        # Last update freshness
        last_update = raw_keepa.get("lastUpdate", 0)
        if last_update > 0:
            confidence += 5

        return min(100, confidence)

    def _compute_rating(
        self, roi: float, velocity: float, stability: float, 
        confidence: float, config: Dict[str, Any]
    ) -> str:
        """Compute overall rating based on thresholds."""
        
        roi_min = config.get("roi_min", 30)
        velocity_min = config.get("velocity_min", 70)
        stability_min = config.get("stability_min", 70)
        confidence_min = config.get("confidence_min", 70)
        
        if (roi >= roi_min and velocity >= velocity_min and 
            stability >= stability_min and confidence >= confidence_min):
            return "EXCELLENT"
        elif (roi >= roi_min * 0.8 and velocity >= velocity_min * 0.85 and
              stability >= stability_min * 0.85 and confidence >= confidence_min * 0.85):
            return "GOOD"  
        elif roi >= roi_min * 0.7:
            return "FAIR"
        else:
            return "PASS"

    def _meets_criteria(self, pick: AutoSourcingPick, scoring_config: Dict[str, Any]) -> bool:
        """Check if pick meets minimum criteria."""
        
        rating_required = scoring_config.get("rating_required", "FAIR")  # Changed from GOOD to FAIR
        roi_min = scoring_config.get("roi_min", 20)
        
        rating_hierarchy = {"PASS": 0, "FAIR": 1, "GOOD": 2, "EXCELLENT": 3}
        
        pick_rating_level = rating_hierarchy.get(pick.overall_rating, 0)
        required_rating_level = rating_hierarchy.get(rating_required, 1)  # FAIR=1
        
        return (pick_rating_level >= required_rating_level and 
                pick.roi_percentage >= roi_min)

    def _classify_product_tier(self, product_data: Dict[str, Any]) -> tuple[str, str]:
        """
        Classifie automatiquement un produit selon score/ROI pour AutoScheduler.
        
        Args:
            product_data: Données du produit (ROI, profit, scores, etc.)
            
        Returns:
            Tuple (tier, reason) - tier: HOT/TOP/WATCH/OTHER, reason: explication
        """
        roi = product_data.get('roi_percentage', 0)
        profit = product_data.get('profit_net', 0)
        velocity = product_data.get('velocity_score', 0)
        confidence = product_data.get('confidence_score', 0)
        rating = product_data.get('overall_rating', 'PASS')
        
        # [HOT] HOT DEALS - Critères stricts pour action immédiate
        if (roi >= 50 and profit >= 15 and velocity >= 80 and
            confidence >= 85 and rating in ["EXCELLENT"]):
            return "HOT", f"[HOT] {roi:.0f}% ROI, ${profit:.0f} profit, {velocity:.0f} velocity - Action immédiate!"

        # [TOP] TOP PICKS - Équilibrés et solides
        elif (roi >= 35 and profit >= 10 and velocity >= 70 and
              confidence >= 75 and rating in ["EXCELLENT", "GOOD"]):
            return "TOP", f"[TOP] {roi:.0f}% ROI, ${profit:.0f} profit - Opportunité solide"

        # [WATCH] WATCH LIST - Potentiel à surveiller
        elif (roi >= 25 and profit >= 5 and velocity >= 60 and
              confidence >= 65 and rating in ["EXCELLENT", "GOOD", "FAIR"]):
            return "WATCH", f"[WATCH] {roi:.0f}% ROI, potentiel à surveiller"

        # [INFO] OTHER - Analyse approfondie nécessaire
        else:
            return "OTHER", f"[INFO] {roi:.0f}% ROI - Analyse détaillée recommandée"

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
        
        # Update flags
        pick.is_purchased = (action == ActionStatus.TO_BUY)
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