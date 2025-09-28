"""Analysis repository for managing book analysis results."""

from typing import Optional, List, Dict, Any
from decimal import Decimal

import structlog
from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base_repository import BaseRepository, SortOrder
from app.models.analysis import Analysis
from app.core.pagination import Page

logger = structlog.get_logger()


class AnalysisRepository(BaseRepository[Analysis]):
    """Repository for Analysis model with ROI/velocity filtering and sorting."""
    
    SORTABLE_FIELDS = [
        "id", "created_at", "roi_percent", "velocity_score", "profit", 
        "buy_price", "expected_sale_price", "isbn_or_asin"
    ]
    FILTERABLE_FIELDS = [
        "id", "batch_id", "isbn_or_asin", "roi_percent", "velocity_score", 
        "profit", "buy_price", "expected_sale_price"
    ]

    def __init__(self, db_session: AsyncSession, model: type = Analysis):
        """Initialize AnalysisRepository with Analysis model."""
        super().__init__(db_session, model)

    async def create_analysis(
        self,
        batch_id: str,
        isbn_or_asin: str,
        buy_price: Decimal,
        fees: Decimal,
        expected_sale_price: Decimal,
        profit: Decimal,
        roi_percent: Decimal,
        velocity_score: Decimal,
        rank_snapshot: Optional[int] = None,
        offers_count: Optional[int] = None,
        raw_keepa: Optional[dict] = None
    ) -> Analysis:
        """Create a new analysis with validation."""
        try:
            analysis = Analysis(
                batch_id=batch_id,
                isbn_or_asin=isbn_or_asin.strip().upper(),  # Normalize ISBN/ASIN
                buy_price=buy_price,
                fees=fees,
                expected_sale_price=expected_sale_price,
                profit=profit,
                roi_percent=roi_percent,
                velocity_score=max(Decimal("0"), min(velocity_score, Decimal("100"))),  # Clamp 0-100
                rank_snapshot=rank_snapshot,
                offers_count=offers_count,
                raw_keepa=raw_keepa
            )
            
            self.db.add(analysis)
            await self.db.commit()
            await self.db.refresh(analysis)
            
            logger.info(
                "Analysis created",
                analysis_id=analysis.id,
                batch_id=batch_id,
                isbn=isbn_or_asin,
                roi=float(roi_percent),
                velocity=float(velocity_score)
            )
            
            return analysis
            
        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to create analysis", 
                batch_id=batch_id, 
                isbn=isbn_or_asin, 
                error=str(e)
            )
            raise

    async def list_by_roi(
        self,
        batch_id: Optional[str] = None,
        roi_min: Optional[Decimal] = None,
        roi_max: Optional[Decimal] = None,
        offset: int = 0,
        limit: int = 100,
        sort_order: SortOrder = SortOrder.DESC
    ) -> Page[Analysis]:
        """
        List analyses filtered by ROI range, sorted by ROI.
        
        Args:
            batch_id: Optional batch filter
            roi_min: Minimum ROI threshold
            roi_max: Maximum ROI threshold  
            offset: Pagination offset
            limit: Items per page
            sort_order: Sort order for ROI
        """
        try:
            filters = {}
            
            if batch_id:
                filters["batch_id"] = batch_id
            
            # ROI range filters
            if roi_min is not None:
                filters["roi_percent"] = {"operator": "gte", "value": roi_min}
            
            if roi_max is not None and roi_min is not None:
                # For range filters, we'll use the custom list_filtered method
                return await self.list_filtered(
                    batch_id=batch_id,
                    roi_min=roi_min,
                    roi_max=roi_max,
                    sort_by=["roi_percent"],
                    sort_order=[sort_order],
                    offset=offset,
                    limit=limit
                )
            elif roi_max is not None:
                filters["roi_percent"] = {"operator": "lte", "value": roi_max}
            
            page = await self.list(
                filters=filters,
                sort_by=["roi_percent", "id"],  # Stable sort with tiebreak
                sort_order=[sort_order, SortOrder.ASC],
                offset=offset,
                limit=limit
            )
            
            logger.info(
                "Listed analyses by ROI",
                batch_id=batch_id,
                roi_min=roi_min,
                roi_max=roi_max,
                returned=len(page.items),
                total=page.total
            )
            
            return page
            
        except Exception as e:
            logger.error("Failed to list analyses by ROI", error=str(e))
            raise

    async def list_by_velocity(
        self,
        batch_id: Optional[str] = None,
        velocity_min: Optional[Decimal] = None,
        velocity_max: Optional[Decimal] = None,
        offset: int = 0,
        limit: int = 100,
        sort_order: SortOrder = SortOrder.DESC
    ) -> Page[Analysis]:
        """
        List analyses filtered by velocity range, sorted by velocity.
        
        Args:
            batch_id: Optional batch filter
            velocity_min: Minimum velocity threshold
            velocity_max: Maximum velocity threshold
            offset: Pagination offset
            limit: Items per page
            sort_order: Sort order for velocity
        """
        try:
            # Use list_filtered for range queries
            if velocity_min is not None and velocity_max is not None:
                return await self.list_filtered(
                    batch_id=batch_id,
                    velocity_min=velocity_min,
                    velocity_max=velocity_max,
                    sort_by=["velocity_score"],
                    sort_order=[sort_order],
                    offset=offset,
                    limit=limit
                )
            
            filters = {}
            
            if batch_id:
                filters["batch_id"] = batch_id
                
            # Single boundary filters
            if velocity_min is not None:
                filters["velocity_score"] = {"operator": "gte", "value": velocity_min}
            elif velocity_max is not None:
                filters["velocity_score"] = {"operator": "lte", "value": velocity_max}
            
            page = await self.list(
                filters=filters,
                sort_by=["velocity_score", "id"],
                sort_order=[sort_order, SortOrder.ASC],
                offset=offset,
                limit=limit
            )
            
            logger.info(
                "Listed analyses by velocity",
                batch_id=batch_id,
                velocity_min=velocity_min,
                velocity_max=velocity_max,
                returned=len(page.items),
                total=page.total
            )
            
            return page
            
        except Exception as e:
            logger.error("Failed to list analyses by velocity", error=str(e))
            raise

    async def list_filtered(
        self,
        batch_id: Optional[str] = None,
        roi_min: Optional[Decimal] = None,
        roi_max: Optional[Decimal] = None,
        velocity_min: Optional[Decimal] = None,
        velocity_max: Optional[Decimal] = None,
        profit_min: Optional[Decimal] = None,
        profit_max: Optional[Decimal] = None,
        sort_by: Optional[List[str]] = None,
        sort_order: Optional[List[SortOrder]] = None,
        offset: int = 0,
        limit: int = 100
    ) -> Page[Analysis]:
        """
        List analyses with combined ROI, velocity, and profit filters.
        
        This method handles complex filter combinations that the base repository
        can't handle with simple field filters.
        """
        try:
            # Build custom query for complex filtering
            query = select(Analysis)
            
            # Apply filters
            conditions = []
            
            if batch_id:
                conditions.append(Analysis.batch_id == batch_id)
            
            if roi_min is not None:
                conditions.append(Analysis.roi_percent >= roi_min)
            if roi_max is not None:
                conditions.append(Analysis.roi_percent <= roi_max)
                
            if velocity_min is not None:
                conditions.append(Analysis.velocity_score >= velocity_min)
            if velocity_max is not None:
                conditions.append(Analysis.velocity_score <= velocity_max)
                
            if profit_min is not None:
                conditions.append(Analysis.profit >= profit_min)
            if profit_max is not None:
                conditions.append(Analysis.profit <= profit_max)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            # Apply sorting
            sort_by = sort_by or ["roi_percent"]
            sort_order = sort_order or [SortOrder.DESC]
            
            # Ensure sort_order matches sort_by length
            while len(sort_order) < len(sort_by):
                sort_order.append(SortOrder.ASC)
            
            for field, order in zip(sort_by, sort_order):
                if hasattr(Analysis, field) and field in self.SORTABLE_FIELDS:
                    column = getattr(Analysis, field)
                    if order == SortOrder.DESC:
                        query = query.order_by(column.desc())
                    else:
                        query = query.order_by(column.asc())
            
            # Always add stable tiebreak
            if "id" not in sort_by:
                query = query.order_by(Analysis.id.asc())
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            items = list(result.scalars().all())
            
            logger.info(
                "Listed analyses with combined filters",
                batch_id=batch_id,
                roi_range=f"{roi_min}-{roi_max}" if roi_min or roi_max else None,
                velocity_range=f"{velocity_min}-{velocity_max}" if velocity_min or velocity_max else None,
                profit_range=f"{profit_min}-{profit_max}" if profit_min or profit_max else None,
                returned=len(items),
                total=total
            )
            
            return Page.create(items=items, total=total, offset=offset, limit=limit)
            
        except Exception as e:
            logger.error("Failed to list analyses with combined filters", error=str(e))
            raise

    async def top_n_for_batch(
        self,
        batch_id: str,
        n: int = 10,
        strategy: str = "roi"  # "roi", "velocity", "profit", "balanced"
    ) -> List[Analysis]:
        """
        Get top N analyses for a batch based on strategy.
        
        Args:
            batch_id: Batch to analyze
            n: Number of top analyses to return
            strategy: Ranking strategy ("roi", "velocity", "profit", "balanced")
        """
        try:
            query = select(Analysis).where(Analysis.batch_id == batch_id)
            
            if strategy == "roi":
                query = query.order_by(Analysis.roi_percent.desc(), Analysis.id.asc())
            elif strategy == "velocity":
                query = query.order_by(Analysis.velocity_score.desc(), Analysis.id.asc())
            elif strategy == "profit":
                query = query.order_by(Analysis.profit.desc(), Analysis.id.asc())
            elif strategy == "balanced":
                # Balanced score: weighted combination of ROI and velocity
                # ROI weight: 0.6, Velocity weight: 0.4
                query = query.order_by(
                    (Analysis.roi_percent * 0.6 + Analysis.velocity_score * 0.4).desc(),
                    Analysis.id.asc()
                )
            else:
                # Default to ROI
                query = query.order_by(Analysis.roi_percent.desc(), Analysis.id.asc())
            
            query = query.limit(n)
            
            result = await self.db.execute(query)
            items = list(result.scalars().all())
            
            logger.info(
                "Retrieved top analyses for batch",
                batch_id=batch_id,
                strategy=strategy,
                requested=n,
                returned=len(items)
            )
            
            return items
            
        except Exception as e:
            logger.error(
                "Failed to get top analyses for batch", 
                batch_id=batch_id, 
                strategy=strategy, 
                error=str(e)
            )
            raise

    async def count_by_thresholds(
        self,
        batch_id: Optional[str] = None,
        roi_thresholds: Optional[List[Decimal]] = None,
        velocity_thresholds: Optional[List[Decimal]] = None,
        profit_thresholds: Optional[List[Decimal]] = None
    ) -> Dict[str, int]:
        """
        Count analyses meeting various threshold criteria.
        
        Returns counts for different quality tiers (e.g., high ROI, medium velocity).
        """
        try:
            roi_thresholds = roi_thresholds or [Decimal("30"), Decimal("50"), Decimal("100")]
            velocity_thresholds = velocity_thresholds or [Decimal("50"), Decimal("70"), Decimal("85")]
            profit_thresholds = profit_thresholds or [Decimal("10"), Decimal("25"), Decimal("50")]
            
            base_query = select(func.count(Analysis.id))
            if batch_id:
                base_query = base_query.where(Analysis.batch_id == batch_id)
            
            counts = {}
            
            # ROI threshold counts
            for threshold in roi_thresholds:
                query = base_query.where(Analysis.roi_percent >= threshold)
                result = await self.db.execute(query)
                counts[f"roi_above_{threshold}"] = result.scalar() or 0
            
            # Velocity threshold counts  
            for threshold in velocity_thresholds:
                query = base_query.where(Analysis.velocity_score >= threshold)
                result = await self.db.execute(query)
                counts[f"velocity_above_{threshold}"] = result.scalar() or 0
            
            # Profit threshold counts
            for threshold in profit_thresholds:
                query = base_query.where(Analysis.profit >= threshold)
                result = await self.db.execute(query)
                counts[f"profit_above_{threshold}"] = result.scalar() or 0
            
            # Combined "golden opportunities" - high on multiple metrics
            golden_query = base_query.where(
                and_(
                    Analysis.roi_percent >= Decimal("40"),
                    Analysis.velocity_score >= Decimal("60"),
                    Analysis.profit >= Decimal("15")
                )
            )
            golden_result = await self.db.execute(golden_query)
            counts["golden_opportunities"] = golden_result.scalar() or 0
            
            # Total count
            total_result = await self.db.execute(base_query)
            counts["total"] = total_result.scalar() or 0
            
            logger.info("Calculated threshold counts", batch_id=batch_id, counts=counts)
            
            return counts
            
        except Exception as e:
            logger.error("Failed to count by thresholds", batch_id=batch_id, error=str(e))
            raise

    async def delete_by_batch(self, batch_id: str) -> int:
        """Delete all analyses for a specific batch."""
        try:
            # Count first
            count_result = await self.db.execute(
                select(func.count(Analysis.id)).where(Analysis.batch_id == batch_id)
            )
            count = count_result.scalar() or 0
            
            if count == 0:
                return 0
            
            # Delete
            delete_query = delete(Analysis).where(Analysis.batch_id == batch_id)
            await self.db.execute(delete_query)
            await self.db.commit()
            
            logger.info("Deleted analyses for batch", batch_id=batch_id, deleted_count=count)
            
            return count
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to delete analyses by batch", batch_id=batch_id, error=str(e))
            raise

    async def delete_by_ids(self, analysis_ids: List[str]) -> int:
        """Delete analyses by their IDs."""
        try:
            if not analysis_ids:
                return 0
            
            delete_query = delete(Analysis).where(Analysis.id.in_(analysis_ids))
            result = await self.db.execute(delete_query)
            await self.db.commit()
            
            deleted_count = result.rowcount
            
            logger.info("Deleted analyses by IDs", deleted_count=deleted_count)
            
            return deleted_count
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to delete analyses by IDs", error=str(e))
            raise

    async def get_batch_summary(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive summary statistics for a batch."""
        try:
            # Basic aggregations
            summary_query = select(
                func.count(Analysis.id).label("total_count"),
                func.avg(Analysis.roi_percent).label("avg_roi"),
                func.avg(Analysis.velocity_score).label("avg_velocity"),
                func.avg(Analysis.profit).label("avg_profit"),
                func.sum(Analysis.profit).label("total_profit"),
                func.max(Analysis.roi_percent).label("max_roi"),
                func.max(Analysis.velocity_score).label("max_velocity"),
                func.max(Analysis.profit).label("max_profit"),
                func.min(Analysis.roi_percent).label("min_roi"),
                func.min(Analysis.velocity_score).label("min_velocity"),
                func.min(Analysis.profit).label("min_profit")
            ).where(Analysis.batch_id == batch_id)
            
            result = await self.db.execute(summary_query)
            row = result.one_or_none()
            
            if not row or row.total_count == 0:
                return None
            
            # Get threshold counts
            threshold_counts = await self.count_by_thresholds(batch_id=batch_id)
            
            summary = {
                "batch_id": batch_id,
                "total_analyses": row.total_count,
                "averages": {
                    "roi_percent": float(row.avg_roi or 0),
                    "velocity_score": float(row.avg_velocity or 0),
                    "profit": float(row.avg_profit or 0)
                },
                "totals": {
                    "profit": float(row.total_profit or 0)
                },
                "maximums": {
                    "roi_percent": float(row.max_roi or 0),
                    "velocity_score": float(row.max_velocity or 0),
                    "profit": float(row.max_profit or 0)
                },
                "minimums": {
                    "roi_percent": float(row.min_roi or 0),
                    "velocity_score": float(row.min_velocity or 0),
                    "profit": float(row.min_profit or 0)
                },
                "threshold_counts": threshold_counts
            }
            
            logger.info("Generated batch summary", batch_id=batch_id)
            
            return summary
            
        except Exception as e:
            logger.error("Failed to generate batch summary", batch_id=batch_id, error=str(e))
            raise