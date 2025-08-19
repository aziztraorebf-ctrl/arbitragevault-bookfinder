"""Repository for Batch model operations."""

from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, desc

from ..models import Batch, Analysis, BatchStatus


class BatchRepository:
    """Repository for managing batch operations."""

    def __init__(self, db: Session):
        self.db = db
        self.model = Batch

    def create(self, batch: Batch) -> Batch:
        """Create a new batch."""
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def get(self, batch_id: str) -> Optional[Batch]:
        """Get batch by ID."""
        return self.db.query(Batch).filter(Batch.id == batch_id).first()

    def update(self, batch: Batch) -> Batch:
        """Update an existing batch."""
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def delete(self, batch_id: str) -> bool:
        """Delete batch by ID."""
        batch = self.get(batch_id)
        if batch:
            self.db.delete(batch)
            self.db.commit()
            return True
        return False

    def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Batch]:
        """Get batches for a specific user."""
        return (
            self.db.query(Batch)
            .filter(Batch.user_id == user_id)
            .order_by(desc(Batch.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_with_analyses(self, batch_id: str) -> Optional[Batch]:
        """Get batch with all related analyses loaded."""
        return (
            self.db.query(Batch)
            .options(selectinload(Batch.analyses))
            .filter(Batch.id == batch_id)
            .first()
        )

    def get_running_batches(self) -> List[Batch]:
        """Get all currently running batches."""
        return (
            self.db.query(Batch)
            .filter(Batch.status == BatchStatus.RUNNING)
            .all()
        )

    def get_batch_stats(self, batch_id: str) -> Optional[dict]:
        """Get statistics for a specific batch."""
        batch = self.get_with_analyses(batch_id)
        if not batch or not batch.analyses:
            return None

        analyses = batch.analyses
        
        # Calculate basic stats
        total_analyses = len(analyses)
        total_profit = sum(analysis.profit for analysis in analyses)
        avg_roi = sum(analysis.roi_percent for analysis in analyses) / total_analyses
        avg_velocity = sum(analysis.velocity_score for analysis in analyses) / total_analyses

        # Find best opportunities
        best_roi_analysis = max(analyses, key=lambda x: x.roi_percent)
        best_profit_analysis = max(analyses, key=lambda x: x.profit)
        fastest_velocity_analysis = max(analyses, key=lambda x: x.velocity_score)

        # Count high-value opportunities
        high_roi_count = len([a for a in analyses if a.roi_percent > 50])
        high_profit_count = len([a for a in analyses if a.profit > 20])
        high_velocity_count = len([a for a in analyses if a.velocity_score > 70])

        return {
            "batch_id": batch_id,
            "batch_name": batch.name,
            "status": batch.status.value,
            "total_items": batch.items_total,
            "processed_items": batch.items_processed,
            "completion_rate": (batch.items_processed / batch.items_total) * 100 if batch.items_total > 0 else 0,
            "total_analyses": total_analyses,
            "total_profit_potential": float(total_profit),
            "average_roi": float(avg_roi),
            "average_velocity": float(avg_velocity),
            "best_opportunities": {
                "highest_roi": {
                    "isbn": best_roi_analysis.isbn_or_asin,
                    "roi": float(best_roi_analysis.roi_percent),
                    "profit": float(best_roi_analysis.profit)
                },
                "highest_profit": {
                    "isbn": best_profit_analysis.isbn_or_asin,
                    "profit": float(best_profit_analysis.profit),
                    "roi": float(best_profit_analysis.roi_percent)
                },
                "fastest_velocity": {
                    "isbn": fastest_velocity_analysis.isbn_or_asin,
                    "velocity": float(fastest_velocity_analysis.velocity_score),
                    "profit": float(fastest_velocity_analysis.profit)
                }
            },
            "opportunity_counts": {
                "high_roi_over_50": high_roi_count,
                "high_profit_over_20": high_profit_count,
                "high_velocity_over_70": high_velocity_count
            },
            "strategy_used": batch.strategy_snapshot
        }

    def update_progress(self, batch_id: str, items_processed: int) -> Optional[Batch]:
        """Update batch progress."""
        batch = self.get(batch_id)
        if not batch:
            return None

        batch.items_processed = min(items_processed, batch.items_total)
        
        # Auto-complete if all items processed
        if batch.items_processed >= batch.items_total and batch.status == BatchStatus.RUNNING:
            batch.status = BatchStatus.DONE
            from datetime import datetime
            batch.finished_at = datetime.now()

        self.db.commit()
        self.db.refresh(batch)
        return batch

    def mark_as_failed(self, batch_id: str, error_message: str = None) -> Optional[Batch]:
        """Mark batch as failed."""
        batch = self.get(batch_id)
        if not batch:
            return None

        batch.status = BatchStatus.FAILED
        from datetime import datetime
        batch.finished_at = datetime.now()
        
        # Store error in strategy_snapshot for debugging
        if error_message and batch.strategy_snapshot:
            batch.strategy_snapshot["error"] = error_message
        
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def get_user_batch_count(self, user_id: str) -> int:
        """Get total number of batches for a user."""
        return self.db.query(Batch).filter(Batch.user_id == user_id).count()

    def search_batches(self, user_id: str, name_filter: str = None, status_filter: BatchStatus = None) -> List[Batch]:
        """Search batches with optional filters."""
        query = self.db.query(Batch).filter(Batch.user_id == user_id)
        
        if name_filter:
            query = query.filter(Batch.name.ilike(f"%{name_filter}%"))
        
        if status_filter:
            query = query.filter(Batch.status == status_filter)
        
        return query.order_by(desc(Batch.created_at)).all()