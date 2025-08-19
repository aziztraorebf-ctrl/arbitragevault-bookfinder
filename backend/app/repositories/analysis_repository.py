"""Repository for Analysis model operations."""

from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc

from ..models import Analysis, Batch


class AnalysisRepository:
    """Repository for managing analysis operations."""

    def __init__(self, db: Session):
        self.db = db
        self.model = Analysis

    def create(self, analysis: Analysis) -> Analysis:
        """Create a new analysis."""
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get(self, analysis_id: str) -> Optional[Analysis]:
        """Get analysis by ID."""
        return self.db.query(Analysis).filter(Analysis.id == analysis_id).first()

    def update(self, analysis: Analysis) -> Analysis:
        """Update an existing analysis."""
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def delete(self, analysis_id: str) -> bool:
        """Delete analysis by ID."""
        analysis = self.get(analysis_id)
        if analysis:
            self.db.delete(analysis)
            self.db.commit()
            return True
        return False

    def get_by_batch_id(self, batch_id: str, skip: int = 0, limit: int = 100) -> List[Analysis]:
        """Get all analyses for a specific batch."""
        return (
            self.db.query(Analysis)
            .filter(Analysis.batch_id == batch_id)
            .order_by(desc(Analysis.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_isbn(self, isbn_or_asin: str) -> List[Analysis]:
        """Get all analyses for a specific ISBN/ASIN across all batches."""
        return (
            self.db.query(Analysis)
            .filter(Analysis.isbn_or_asin == isbn_or_asin)
            .order_by(desc(Analysis.created_at))
            .all()
        )

    def get_profit_leaders(self, batch_id: str, limit: int = 10) -> List[Analysis]:
        """Get top analyses by profit for a batch (Profit Hunter view)."""
        return (
            self.db.query(Analysis)
            .filter(Analysis.batch_id == batch_id)
            .order_by(desc(Analysis.profit))
            .limit(limit)
            .all()
        )

    def get_roi_leaders(self, batch_id: str, limit: int = 10) -> List[Analysis]:
        """Get top analyses by ROI percentage for a batch."""
        return (
            self.db.query(Analysis)
            .filter(Analysis.batch_id == batch_id)
            .order_by(desc(Analysis.roi_percent))
            .limit(limit)
            .all()
        )

    def get_velocity_leaders(self, batch_id: str, limit: int = 10) -> List[Analysis]:
        """Get top analyses by velocity score for a batch (Velocity view)."""
        return (
            self.db.query(Analysis)
            .filter(Analysis.batch_id == batch_id)
            .order_by(desc(Analysis.velocity_score))
            .limit(limit)
            .all()
        )

    def filter_by_profit_range(self, batch_id: str, min_profit: Decimal = None, max_profit: Decimal = None) -> List[Analysis]:
        """Filter analyses by profit range."""
        query = self.db.query(Analysis).filter(Analysis.batch_id == batch_id)
        
        if min_profit is not None:
            query = query.filter(Analysis.profit >= min_profit)
        
        if max_profit is not None:
            query = query.filter(Analysis.profit <= max_profit)
        
        return query.order_by(desc(Analysis.profit)).all()

    def filter_by_roi_range(self, batch_id: str, min_roi: Decimal = None, max_roi: Decimal = None) -> List[Analysis]:
        """Filter analyses by ROI percentage range."""
        query = self.db.query(Analysis).filter(Analysis.batch_id == batch_id)
        
        if min_roi is not None:
            query = query.filter(Analysis.roi_percent >= min_roi)
        
        if max_roi is not None:
            query = query.filter(Analysis.roi_percent <= max_roi)
        
        return query.order_by(desc(Analysis.roi_percent)).all()

    def filter_by_velocity_range(self, batch_id: str, min_velocity: Decimal = None, max_velocity: Decimal = None) -> List[Analysis]:
        """Filter analyses by velocity score range."""
        query = self.db.query(Analysis).filter(Analysis.batch_id == batch_id)
        
        if min_velocity is not None:
            query = query.filter(Analysis.velocity_score >= min_velocity)
        
        if max_velocity is not None:
            query = query.filter(Analysis.velocity_score <= max_velocity)
        
        return query.order_by(desc(Analysis.velocity_score)).all()

    def get_strategic_view(self, batch_id: str, view_type: str, filters: dict = None) -> List[Analysis]:
        """Get analyses formatted for strategic views (Profit Hunter or Velocity)."""
        query = self.db.query(Analysis).filter(Analysis.batch_id == batch_id)
        
        # Apply filters if provided
        if filters:
            if "min_roi" in filters:
                query = query.filter(Analysis.roi_percent >= Decimal(str(filters["min_roi"])))
            
            if "min_profit" in filters:
                query = query.filter(Analysis.profit >= Decimal(str(filters["min_profit"])))
            
            if "min_velocity" in filters:
                query = query.filter(Analysis.velocity_score >= Decimal(str(filters["min_velocity"])))
            
            if "max_buy_price" in filters:
                query = query.filter(Analysis.buy_price <= Decimal(str(filters["max_buy_price"])))
        
        # Sort by appropriate metric based on view
        if view_type.lower() == "profit":
            query = query.order_by(desc(Analysis.profit), desc(Analysis.roi_percent))
        elif view_type.lower() == "velocity":
            query = query.order_by(desc(Analysis.velocity_score), desc(Analysis.profit))
        else:
            # Balanced view - sort by combined score
            # This could be enhanced with a calculated field
            query = query.order_by(desc(Analysis.roi_percent * Analysis.velocity_score))
        
        return query.all()

    def get_batch_count(self, batch_id: str) -> int:
        """Get total count of analyses in a batch."""
        return self.db.query(Analysis).filter(Analysis.batch_id == batch_id).count()

    def bulk_create_analyses(self, analyses_data: List[dict]) -> List[Analysis]:
        """Create multiple analyses in a single transaction."""
        analyses = []
        
        for data in analyses_data:
            analysis = Analysis(**data)
            analyses.append(analysis)
        
        self.db.add_all(analyses)
        self.db.commit()
        
        # Refresh all objects to get their IDs
        for analysis in analyses:
            self.db.refresh(analysis)
        
        return analyses

    def get_comparison_data(self, batch_id: str) -> dict:
        """Get data formatted for profit vs velocity comparison."""
        analyses = self.get_by_batch_id(batch_id)
        
        if not analyses:
            return {"profit_view": [], "velocity_view": [], "comparison": {}}
        
        # Sort for profit view (by profit descending)
        profit_view = sorted(analyses, key=lambda x: x.profit, reverse=True)
        
        # Sort for velocity view (by velocity score descending)
        velocity_view = sorted(analyses, key=lambda x: x.velocity_score, reverse=True)
        
        # Calculate comparison metrics
        total_profit = sum(a.profit for a in analyses)
        avg_velocity = sum(a.velocity_score for a in analyses) / len(analyses)
        high_profit_low_velocity = len([a for a in analyses if a.profit > 20 and a.velocity_score < 50])
        high_velocity_low_profit = len([a for a in analyses if a.velocity_score > 70 and a.profit < 10])
        
        return {
            "profit_view": profit_view[:20],  # Top 20 by profit
            "velocity_view": velocity_view[:20],  # Top 20 by velocity
            "comparison": {
                "total_opportunities": len(analyses),
                "total_profit_potential": float(total_profit),
                "average_velocity": float(avg_velocity),
                "high_profit_slow_movers": high_profit_low_velocity,
                "fast_movers_low_profit": high_velocity_low_profit
            }
        }

    def search_analyses(self, batch_id: str, isbn_filter: str = None) -> List[Analysis]:
        """Search analyses within a batch by ISBN/ASIN."""
        query = self.db.query(Analysis).filter(Analysis.batch_id == batch_id)
        
        if isbn_filter:
            query = query.filter(Analysis.isbn_or_asin.ilike(f"%{isbn_filter}%"))
        
        return query.order_by(desc(Analysis.created_at)).all()

    def get_performance_summary(self, batch_id: str) -> dict:
        """Get performance summary for a batch."""
        analyses = self.get_by_batch_id(batch_id)
        
        if not analyses:
            return {}
        
        profits = [a.profit for a in analyses]
        rois = [a.roi_percent for a in analyses]
        velocities = [a.velocity_score for a in analyses]
        
        return {
            "total_analyses": len(analyses),
            "profit_metrics": {
                "total": float(sum(profits)),
                "average": float(sum(profits) / len(profits)),
                "max": float(max(profits)),
                "min": float(min(profits))
            },
            "roi_metrics": {
                "average": float(sum(rois) / len(rois)),
                "max": float(max(rois)),
                "min": float(min(rois))
            },
            "velocity_metrics": {
                "average": float(sum(velocities) / len(velocities)),
                "max": float(max(velocities)),
                "min": float(min(velocities))
            },
            "quality_indicators": {
                "profitable_count": len([p for p in profits if p > 0]),
                "high_roi_count": len([r for r in rois if r > 30]),
                "fast_movers_count": len([v for v in velocities if v > 60])
            }
        }