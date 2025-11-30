"""
Tests for pagination and sorting patterns (preparing for repositories).
Tests data preparation and patterns that will be used in repository layer.
"""
import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta

from app.models.user import User
from app.models.batch import Batch, BatchStatus
from app.models.analysis import Analysis


class TestDataPreparationForPagination:
    """Test data setup patterns for future pagination testing."""

    def test_create_multiple_batches_for_sorting(self, db_session, user_data):
        """Create multiple batches with different attributes for sorting tests."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()

        # Create batches with different characteristics
        batches_data = [
            {
                "name": "Alpha Batch",
                "items_total": 100,
                "status": BatchStatus.COMPLETED,
                "strategy_snapshot": {"profit_threshold": 20.0}
            },
            {
                "name": "Beta Batch",
                "items_total": 50,
                "status": BatchStatus.PROCESSING,
                "strategy_snapshot": {"profit_threshold": 15.0}
            },
            {
                "name": "Gamma Batch",
                "items_total": 200,
                "status": BatchStatus.PENDING,
                "strategy_snapshot": {"profit_threshold": 25.0}
            },
            {
                "name": "Delta Batch",
                "items_total": 75,
                "status": BatchStatus.FAILED,
                "strategy_snapshot": {"profit_threshold": 30.0}
            }
        ]

        created_batches = []
        for batch_data in batches_data:
            batch = Batch(
                user_id=user.id,
                **batch_data
            )
            db_session.add(batch)
            created_batches.append(batch)

        db_session.flush()
        
        # Verify all batches were created
        assert len(created_batches) == 4
        
        # Test basic sorting patterns (manual for now, will be in repository later)
        batches_by_name = sorted(created_batches, key=lambda b: b.name)
        assert batches_by_name[0].name == "Alpha Batch"
        assert batches_by_name[-1].name == "Gamma Batch"
        
        batches_by_total = sorted(created_batches, key=lambda b: b.items_total, reverse=True)
        assert batches_by_total[0].items_total == 200
        assert batches_by_total[-1].items_total == 50
        
        db_session.commit()

    def test_create_multiple_analyses_for_pagination(self, db_session, user_data):
        """Create multiple analyses with varying ROI for pagination tests."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()
        
        batch = Batch(
            user_id=user.id,
            name="Large Analysis Batch",
            items_total=25,
            strategy_snapshot={"profit_threshold": 20.0}
        )
        db_session.add(batch)
        db_session.flush()

        # Create 25 analyses with varying ROI percentages
        analyses_data = [
            {"roi": 45.5, "profit": 15.00, "isbn": f"978-{i:010d}"}
            for i in range(1, 26)
        ]
        
        created_analyses = []
        for i, analysis_data in enumerate(analyses_data):
            # Vary the ROI to create interesting sorting scenarios
            roi_modifier = (i * 2.5) % 100  # Creates variety from 0-97.5
            analysis = Analysis(
                batch_id=batch.id,
                isbn_or_asin=analysis_data["isbn"],
                buy_price=Decimal("20.00"),
                expected_sale_price=Decimal("35.00"),
                fees=Decimal("3.00"),
                profit=Decimal(str(analysis_data["profit"] + roi_modifier * 0.1)),
                roi_percent=Decimal(str(roi_modifier + 10.0)),  # ROI from 10-107.5
                velocity_score=Decimal(str(5.0 + (i % 10))),  # Velocity 5.0-14.0
                raw_keepa={"title": f"Book {i+1}", "category": "textbook"}
            )
            db_session.add(analysis)
            created_analyses.append(analysis)

        db_session.flush()
        
        # Verify all analyses were created
        assert len(created_analyses) == 25
        
        # Test sorting patterns for future pagination
        high_roi_analyses = [a for a in created_analyses if a.roi_percent >= Decimal("50.0")]
        assert len(high_roi_analyses) > 0
        
        sorted_by_roi = sorted(created_analyses, key=lambda a: a.roi_percent, reverse=True)
        assert sorted_by_roi[0].roi_percent >= sorted_by_roi[-1].roi_percent
        
        db_session.commit()


class TestPaginationPatterns:
    """Test pagination patterns that will be implemented in repositories."""

    def test_manual_pagination_offset_limit(self, db_session, user_data):
        """Test manual pagination patterns using offset and limit."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()
        
        batch = Batch(
            user_id=user.id,
            name="Pagination Test Batch",
            items_total=15,
            strategy_snapshot={"profit_threshold": 20.0}
        )
        db_session.add(batch)
        db_session.flush()

        # Create 15 analyses for pagination testing
        for i in range(15):
            analysis = Analysis(
                batch_id=batch.id,
                isbn_or_asin=f"978-{i:010d}",
                buy_price=Decimal("20.00"),
                expected_sale_price=Decimal("30.00"),
                fees=Decimal("3.00"),
                profit=Decimal("7.00"),
                roi_percent=Decimal(str(25.0 + i * 2.0)),  # ROI from 25-53
                velocity_score=Decimal("7.5"),
                raw_keepa={"title": f"Paginated Book {i+1}"}
            )
            db_session.add(analysis)

        db_session.flush()
        
        # Test pagination patterns (simulating repository behavior)
        from sqlalchemy import desc
        
        # Page 1: First 5 items, sorted by ROI descending
        page_1 = db_session.query(Analysis)\
            .filter(Analysis.batch_id == batch.id)\
            .order_by(desc(Analysis.roi_percent))\
            .offset(0)\
            .limit(5)\
            .all()
            
        assert len(page_1) == 5
        assert page_1[0].roi_percent > page_1[-1].roi_percent  # Descending order
        
        # Page 2: Next 5 items
        page_2 = db_session.query(Analysis)\
            .filter(Analysis.batch_id == batch.id)\
            .order_by(desc(Analysis.roi_percent))\
            .offset(5)\
            .limit(5)\
            .all()
            
        assert len(page_2) == 5
        assert page_1[-1].roi_percent > page_2[0].roi_percent  # Continuous order
        
        # Page 3: Last 5 items
        page_3 = db_session.query(Analysis)\
            .filter(Analysis.batch_id == batch.id)\
            .order_by(desc(Analysis.roi_percent))\
            .offset(10)\
            .limit(5)\
            .all()
            
        assert len(page_3) == 5
        
        # Verify no overlaps between pages
        page_1_ids = {a.id for a in page_1}
        page_2_ids = {a.id for a in page_2}
        page_3_ids = {a.id for a in page_3}
        
        assert len(page_1_ids.intersection(page_2_ids)) == 0
        assert len(page_2_ids.intersection(page_3_ids)) == 0
        assert len(page_1_ids.intersection(page_3_ids)) == 0

    def test_filtering_with_pagination(self, db_session, user_data):
        """Test filtering combined with pagination patterns."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()
        
        batch = Batch(
            user_id=user.id,
            name="Filter + Pagination Batch",
            items_total=20,
            strategy_snapshot={"roi_threshold": 35.0}
        )
        db_session.add(batch)
        db_session.flush()

        # Create 20 analyses with specific ROI pattern for filtering
        for i in range(20):
            # Create some high ROI (>35%) and some low ROI (<35%)
            roi_value = 40.0 + i * 2.0 if i % 2 == 0 else 20.0 + i * 1.0
            
            analysis = Analysis(
                batch_id=batch.id,
                isbn_or_asin=f"978-FILTER{i:05d}",
                buy_price=Decimal("25.00"),
                expected_sale_price=Decimal("40.00"),
                fees=Decimal("4.00"),
                profit=Decimal("11.00"),
                roi_percent=Decimal(str(roi_value)),
                velocity_score=Decimal("6.0"),
                raw_keepa={"title": f"Filter Book {i+1}"}
            )
            db_session.add(analysis)

        db_session.flush()
        
        # Test filtering + pagination (simulating repository methods)
        from sqlalchemy import desc
        
        # Get high ROI analyses (>35%) with pagination
        high_roi_page_1 = db_session.query(Analysis)\
            .filter(Analysis.batch_id == batch.id)\
            .filter(Analysis.roi_percent > Decimal("35.0"))\
            .order_by(desc(Analysis.roi_percent))\
            .offset(0)\
            .limit(5)\
            .all()
            
        # Should have results since even indices create ROI > 35%
        assert len(high_roi_page_1) > 0
        for analysis in high_roi_page_1:
            assert analysis.roi_percent > Decimal("35.0")
            
        # Get total count for pagination metadata
        total_high_roi = db_session.query(Analysis)\
            .filter(Analysis.batch_id == batch.id)\
            .filter(Analysis.roi_percent > Decimal("35.0"))\
            .count()
            
        assert total_high_roi > 0
        
        # Test filtering by velocity + ROI combined
        high_value_analyses = db_session.query(Analysis)\
            .filter(Analysis.batch_id == batch.id)\
            .filter(Analysis.roi_percent > Decimal("30.0"))\
            .filter(Analysis.velocity_score >= Decimal("5.0"))\
            .order_by(desc(Analysis.roi_percent))\
            .limit(10)\
            .all()
            
        assert len(high_value_analyses) > 0
        for analysis in high_value_analyses:
            assert analysis.roi_percent > Decimal("30.0")
            assert analysis.velocity_score >= Decimal("5.0")


class TestSortingPatterns:
    """Test various sorting patterns for repository methods."""

    def test_multi_column_sorting(self, db_session, user_data):
        """Test sorting by multiple columns (ROI desc, then velocity desc)."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()
        
        batch = Batch(
            user_id=user.id,
            name="Multi-Sort Test Batch",
            items_total=12,
            strategy_snapshot={"profit_threshold": 20.0}
        )
        db_session.add(batch)
        db_session.flush()

        # Create analyses with same ROI but different velocities
        test_data = [
            {"roi": 35.0, "velocity": 9.0, "isbn": "978-1111111111"},
            {"roi": 35.0, "velocity": 7.0, "isbn": "978-2222222222"},
            {"roi": 45.0, "velocity": 6.0, "isbn": "978-3333333333"},
            {"roi": 45.0, "velocity": 8.0, "isbn": "978-4444444444"},
            {"roi": 25.0, "velocity": 9.5, "isbn": "978-5555555555"},
            {"roi": 25.0, "velocity": 5.0, "isbn": "978-6666666666"},
        ]
        
        for data in test_data:
            analysis = Analysis(
                batch_id=batch.id,
                isbn_or_asin=data["isbn"],
                buy_price=Decimal("20.00"),
                expected_sale_price=Decimal("30.00"),
                fees=Decimal("3.00"),
                profit=Decimal("7.00"),
                roi_percent=Decimal(str(data["roi"])),
                velocity_score=Decimal(str(data["velocity"])),
                raw_keepa={"title": f"Multi-sort Book"}
            )
            db_session.add(analysis)

        db_session.flush()
        
        # Test multi-column sorting: ROI desc, then velocity desc
        from sqlalchemy import desc
        
        sorted_analyses = db_session.query(Analysis)\
            .filter(Analysis.batch_id == batch.id)\
            .order_by(desc(Analysis.roi_percent), desc(Analysis.velocity_score))\
            .all()
            
        # Verify sorting: 45% ROI items first, higher velocity first within same ROI
        assert sorted_analyses[0].roi_percent == Decimal("45.0")
        assert sorted_analyses[0].velocity_score == Decimal("8.0")  # Higher velocity first
        
        assert sorted_analyses[1].roi_percent == Decimal("45.0")
        assert sorted_analyses[1].velocity_score == Decimal("6.0")  # Lower velocity second
        
        assert sorted_analyses[2].roi_percent == Decimal("35.0")
        assert sorted_analyses[2].velocity_score == Decimal("9.0")  # Higher velocity first

    def test_date_based_sorting(self, db_session, user_data):
        """Test sorting by created_at timestamps."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()
        
        # Create batches at different times to test date sorting
        batches = []
        for i in range(3):
            batch = Batch(
                user_id=user.id,
                name=f"Date Test Batch {i+1}",
                items_total=10,
                strategy_snapshot={"created_order": i}
            )
            db_session.add(batch)
            db_session.flush()  # This should set created_at
            batches.append(batch)

        db_session.commit()
        
        # Test sorting by creation date
        from sqlalchemy import asc, desc
        
        # Oldest first
        oldest_first = db_session.query(Batch)\
            .filter(Batch.user_id == user.id)\
            .order_by(asc(Batch.created_at))\
            .all()
            
        # Newest first  
        newest_first = db_session.query(Batch)\
            .filter(Batch.user_id == user.id)\
            .order_by(desc(Batch.created_at))\
            .all()
            
        # Verify ordering (assuming they were created in sequence)
        assert len(oldest_first) == 3
        assert len(newest_first) == 3
        
        # The order should be reversed between the two queries
        assert oldest_first[0].id == newest_first[-1].id
        assert oldest_first[-1].id == newest_first[0].id