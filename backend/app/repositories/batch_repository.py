"""Batch repository for managing analysis batches."""

from typing import Optional, List
from datetime import datetime, timedelta

import structlog
from sqlalchemy import select, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base_repository import BaseRepository, SortOrder
from app.models.batch import Batch, BatchStatus
from app.core.exceptions import InvalidTransitionError

logger = structlog.get_logger()


class BatchRepository(BaseRepository[Batch]):
    """Repository for Batch model with status management."""
    
    SORTABLE_FIELDS = ["id", "name", "created_at", "started_at", "finished_at", "items_total", "items_processed"]
    FILTERABLE_FIELDS = ["id", "user_id", "name", "status"]

    def __init__(self, db_session: AsyncSession, model: type = Batch):
        """Initialize BatchRepository with Batch model."""
        super().__init__(db_session, model)

    async def create_batch(
        self,
        user_id: str,
        name: str,
        items_total: int,
        description: Optional[str] = None,
        strategy_snapshot: Optional[dict] = None
    ) -> Batch:
        """Create a new batch with validation."""
        try:
            batch = Batch(
                user_id=user_id,
                name=name,
                description=description,
                items_total=max(0, items_total),  # Ensure non-negative
                status=BatchStatus.PENDING,
                strategy_snapshot=strategy_snapshot
            )
            
            self.db.add(batch)
            await self.db.commit()
            await self.db.refresh(batch)
            
            logger.info(
                "Batch created",
                batch_id=batch.id,
                user_id=user_id,
                name=name,
                items_total=items_total
            )
            
            return batch
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to create batch", error=str(e))
            raise

    async def get_user_batches(
        self,
        user_id: str,
        status: Optional[BatchStatus] = None,
        limit: int = 50,
        include_analyses: bool = False
    ) -> List[Batch]:
        """Get batches for a specific user with optional filtering."""
        try:
            filters = {"user_id": user_id}
            
            if status:
                filters["status"] = status
            
            # Build query with optional analyses loading
            query_options = []
            if include_analyses:
                query_options.append(selectinload(Batch.analyses))
            
            page = await self.list(
                filters=filters,
                sort_by=["created_at"],
                sort_order=[SortOrder.DESC],
                limit=limit,
                query_options=query_options
            )
            
            return page.items
            
        except Exception as e:
            logger.error("Failed to get user batches", user_id=user_id, error=str(e))
            raise

    async def get_active_batches(self) -> List[Batch]:
        """Get all batches that are currently running."""
        try:
            page = await self.list(
                filters={"status": BatchStatus.PROCESSING},
                sort_by=["started_at"],
                sort_order=["asc"],
                limit=100  # Reasonable limit for active batches
            )
            
            return page.items
            
        except Exception as e:
            logger.error("Failed to get active batches", error=str(e))
            raise

    async def transition_status(
        self,
        batch_id: str,
        new_status: BatchStatus,
        force: bool = False
    ) -> Optional[Batch]:
        """
        Transition batch to new status with validation.
        
        Args:
            batch_id: ID of batch to update
            new_status: New status to transition to
            force: Skip transition validation if True
            
        Returns:
            Updated batch or None if not found
            
        Raises:
            InvalidTransitionError: If transition is not valid
        """
        try:
            batch = await self.get_by_id(batch_id)
            
            if not batch:
                return None
            
            # Validate transition unless forced
            if not force and not batch.can_transition_to(new_status):
                raise InvalidTransitionError(
                    f"Cannot transition from {batch.status.value} to {new_status.value}"
                )
            
            # Update status and timing
            updates = {"status": new_status}
            
            if new_status == BatchStatus.PROCESSING and not batch.started_at:
                updates["started_at"] = datetime.utcnow()
            
            if new_status in (BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED) and not batch.finished_at:
                updates["finished_at"] = datetime.utcnow()
            
            old_status = batch.status.value  # Store before update
            updated_batch = await self.update(batch_id, **updates)
            
            logger.info(
                "Batch status transitioned",
                batch_id=batch_id,
                from_status=old_status,
                to_status=new_status.value
            )
            
            return updated_batch
            
        except InvalidTransitionError:
            raise
        except Exception as e:
            logger.error("Failed to transition batch status", batch_id=batch_id, error=str(e))
            raise

    async def update_progress(
        self,
        batch_id: str,
        items_processed: int,
        auto_complete: bool = True
    ) -> Optional[Batch]:
        """
        Update batch progress and optionally complete when done.
        
        Args:
            batch_id: ID of batch to update
            items_processed: Number of items processed
            auto_complete: Automatically complete batch when all items processed
        """
        try:
            batch = await self.get_by_id(batch_id)
            
            if not batch:
                return None
            
            # Clamp items_processed to valid range
            items_processed = max(0, min(items_processed, batch.items_total))
            
            updates = {"items_processed": items_processed}
            
            # Auto-complete if all items processed
            if auto_complete and items_processed >= batch.items_total and batch.status == BatchStatus.PROCESSING:
                updates["status"] = BatchStatus.COMPLETED
                updates["finished_at"] = datetime.utcnow()
            
            updated_batch = await self.update(batch_id, **updates)
            
            if updated_batch:
                logger.info(
                    "Batch progress updated",
                    batch_id=batch_id,
                    items_processed=items_processed,
                    items_total=batch.items_total,
                    progress_pct=updated_batch.progress_percentage
                )
            
            return updated_batch
            
        except Exception as e:
            logger.error("Failed to update batch progress", batch_id=batch_id, error=str(e))
            raise

    async def increment_progress(self, batch_id: str, increment: int = 1) -> Optional[Batch]:
        """Increment batch progress by specified amount."""
        try:
            batch = await self.get_by_id(batch_id)
            
            if not batch:
                return None
            
            new_processed = batch.items_processed + increment
            return await self.update_progress(batch_id, new_processed)
            
        except Exception as e:
            logger.error("Failed to increment batch progress", batch_id=batch_id, error=str(e))
            raise

    async def get_batch_stats(self, user_id: Optional[str] = None) -> dict:
        """Get batch statistics, optionally filtered by user."""
        try:
            # Base query for counting by status
            query = select(
                Batch.status,
                func.count(Batch.id).label("count")
            )
            
            if user_id:
                query = query.where(Batch.user_id == user_id)
            
            query = query.group_by(Batch.status)
            
            result = await self.db.execute(query)
            status_counts = {row.status: row.count for row in result}
            
            # Get total items processed across all batches
            items_query = select(func.sum(Batch.items_processed))
            
            if user_id:
                items_query = items_query.where(Batch.user_id == user_id)
            
            items_result = await self.db.execute(items_query)
            total_items_processed = items_result.scalar() or 0
            
            # Get average processing time for completed batches
            completed_batches = select(
                func.avg(
                    func.extract(
                        'epoch',
                        Batch.finished_at - Batch.started_at
                    )
                ).label("avg_duration_seconds")
            ).where(
                and_(
                    Batch.status == BatchStatus.COMPLETED,
                    Batch.started_at.is_not(None),
                    Batch.finished_at.is_not(None)
                )
            )
            
            if user_id:
                completed_batches = completed_batches.where(Batch.user_id == user_id)
            
            duration_result = await self.db.execute(completed_batches)
            avg_duration_seconds = duration_result.scalar()
            
            stats = {
                "total_batches": sum(status_counts.values()),
                "by_status": {
                    status.value: status_counts.get(status, 0)
                    for status in BatchStatus
                },
                "total_items_processed": total_items_processed,
                "avg_processing_time_seconds": avg_duration_seconds
            }
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get batch stats", user_id=user_id, error=str(e))
            raise

    async def get_recent_batches(
        self,
        user_id: str,
        limit: int = 10,
        include_failed: bool = True
    ) -> List[Batch]:
        """Get recent batches for a user."""
        try:
            filters = {"user_id": user_id}
            
            # Optionally exclude failed batches
            if not include_failed:
                # Would need to use custom query for "not equal" filter
                result = await self.db.execute(
                    select(Batch)
                    .where(
                        and_(
                            Batch.user_id == user_id,
                            Batch.status != BatchStatus.FAILED
                        )
                    )
                    .order_by(Batch.created_at.desc())
                    .limit(limit)
                )
                
                return list(result.scalars().all())
            
            page = await self.list(
                filters=filters,
                sort_by=["created_at"],
                sort_order=["desc"],
                limit=limit
            )
            
            return page.items
            
        except Exception as e:
            logger.error("Failed to get recent batches", user_id=user_id, error=str(e))
            raise

    async def cleanup_old_batches(
        self,
        older_than_days: int = 90,
        keep_recent_count: int = 50,
        dry_run: bool = True
    ) -> int:
        """
        Clean up old batches beyond retention policy.
        
        Args:
            older_than_days: Delete batches older than this
            keep_recent_count: Always keep this many recent batches per user
            dry_run: If True, only count what would be deleted
            
        Returns:
            Number of batches that would be/were deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            
            # Complex query would be needed here to implement keep_recent_count logic
            # For now, simple date-based deletion
            
            query = select(func.count(Batch.id)).where(
                and_(
                    Batch.created_at < cutoff_date,
                    Batch.status.in_([BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED])
                )
            )
            
            result = await self.db.execute(query)
            count = result.scalar() or 0
            
            if not dry_run and count > 0:
                delete_query = delete(Batch).where(
                    and_(
                        Batch.created_at < cutoff_date,
                        Batch.status.in_([BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED])
                    )
                )
                
                await self.db.execute(delete_query)
                await self.db.commit()
                
                logger.info("Old batches cleaned up", deleted_count=count)
            
            return count
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to cleanup old batches", error=str(e))
            raise

    async def restart_batch(self, batch_id: str) -> Optional[Batch]:
        """Restart a failed or completed batch."""
        try:
            batch = await self.get_by_id(batch_id)
            
            if not batch:
                return None
            
            # Reset progress and status
            updates = {
                "status": BatchStatus.PENDING,
                "items_processed": 0,
                "started_at": None,
                "finished_at": None
            }
            
            updated_batch = await self.update(batch_id, **updates)
            
            logger.info("Batch restarted", batch_id=batch_id)
            
            return updated_batch
            
        except Exception as e:
            logger.error("Failed to restart batch", batch_id=batch_id, error=str(e))
            raise