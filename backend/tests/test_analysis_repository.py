"""Integration tests for AnalysisRepository."""

import pytest
from decimal import Decimal
from typing import List

from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.batch_repository import BatchRepository
from app.repositories.user_repository import UserRepository
from app.models.analysis import Analysis
from app.models.batch import Batch, BatchStatus
from app.models.user import User
from app.repositories.base_repository import SortOrder


class TestAnalysisRepository:
    """Integration tests for AnalysisRepository functionality."""

    @pytest.fixture(autouse=True)
    async def setup(self, async_db_session, user_data, batch_data):
        """Setup repositories and test data."""
        self.analysis_repo = AnalysisRepository(async_db_session, Analysis)
        
        # Create test user and batch
        user_repo = UserRepository(async_db_session, User)
        user_data_clean = {k: v for k, v in user_data.items() if k != "id"}
        self.test_user = await user_repo.create_user(**user_data_clean)
        
        batch_repo = BatchRepository(async_db_session, Batch)
        self.test_batch = await batch_repo.create_batch(
            user_id=self.test_user.id,
            name="Test Analysis Batch",
            items_total=20
        )

    async def test_create_analysis_success(self):
        """Test successful analysis creation."""
        analysis = await self.analysis_repo.create_analysis(
            batch_id=self.test_batch.id,
            isbn_or_asin="978-0123456789",
            buy_price=Decimal("15.00"),
            fees=Decimal("3.50"),
            expected_sale_price=Decimal("25.00"),
            profit=Decimal("6.50"),
            roi_percent=Decimal("43.33"),
            velocity_score=Decimal("75.0"),
            rank_snapshot=12500,
            offers_count=8,
            raw_keepa={"test": "data"}
        )
        
        assert analysis.id is not None
        assert analysis.batch_id == self.test_batch.id
        assert analysis.isbn_or_asin == "978-0123456789"
        assert analysis.buy_price == Decimal("15.00")
        assert analysis.roi_percent == Decimal("43.33")
        assert analysis.velocity_score == Decimal("75.0")
        assert analysis.rank_snapshot == 12500
        assert analysis.raw_keepa == {"test": "data"}

    async def test_create_analysis_normalizes_isbn(self):
        """Test that ISBN/ASIN is normalized to uppercase."""
        analysis = await self.analysis_repo.create_analysis(
            batch_id=self.test_batch.id,
            isbn_or_asin=" 978-0123456789 ",  # With spaces
            buy_price=Decimal("10.00"),
            fees=Decimal("2.00"),
            expected_sale_price=Decimal("15.00"),
            profit=Decimal("3.00"),
            roi_percent=Decimal("30.00"),
            velocity_score=Decimal("60.0")
        )
        
        assert analysis.isbn_or_asin == "978-0123456789"  # Trimmed and uppercase

    async def test_create_analysis_clamps_velocity_score(self):
        """Test that velocity score is clamped to 0-100 range."""
        # Test negative velocity
        analysis_neg = await self.analysis_repo.create_analysis(
            batch_id=self.test_batch.id,
            isbn_or_asin="978-0111111111",
            buy_price=Decimal("10.00"),
            fees=Decimal("2.00"),
            expected_sale_price=Decimal("15.00"),
            profit=Decimal("3.00"),
            roi_percent=Decimal("30.00"),
            velocity_score=Decimal("-10.0")  # Should be clamped to 0
        )
        assert analysis_neg.velocity_score == Decimal("0.0")
        
        # Test velocity > 100
        analysis_high = await self.analysis_repo.create_analysis(
            batch_id=self.test_batch.id,
            isbn_or_asin="978-0222222222",
            buy_price=Decimal("10.00"),
            fees=Decimal("2.00"),
            expected_sale_price=Decimal("15.00"),
            profit=Decimal("3.00"),
            roi_percent=Decimal("30.00"),
            velocity_score=Decimal("150.0")  # Should be clamped to 100
        )
        assert analysis_high.velocity_score == Decimal("100.0")

    async def create_sample_analyses(self) -> List[Analysis]:
        """Create a diverse set of sample analyses for testing."""
        analyses = []
        
        # High ROI, High Velocity (Golden opportunity)
        analyses.append(await self.analysis_repo.create_analysis(
            batch_id=self.test_batch.id,
            isbn_or_asin="978-GOLDEN001",
            buy_price=Decimal("10.00"),
            fees=Decimal("2.00"),
            expected_sale_price=Decimal("35.00"),
            profit=Decimal("23.00"),
            roi_percent=Decimal("130.00"),
            velocity_score=Decimal("85.0")
        ))
        
        # High ROI, Low Velocity
        analyses.append(await self.analysis_repo.create_analysis(
            batch_id=self.test_batch.id,
            isbn_or_asin="978-HROILVEL001",
            buy_price=Decimal("15.00"),
            fees=Decimal("3.00"),
            expected_sale_price=Decimal("45.00"),
            profit=Decimal("27.00"),
            roi_percent=Decimal("80.00"),
            velocity_score=Decimal("30.0")
        ))
        
        # Low ROI, High Velocity
        analyses.append(await self.analysis_repo.create_analysis(
            batch_id=self.test_batch.id,
            isbn_or_asin="978-LROIHVEL001",
            buy_price=Decimal("20.00"),
            fees=Decimal("4.00"),
            expected_sale_price=Decimal("28.00"),
            profit=Decimal("4.00"),
            roi_percent=Decimal("20.00"),
            velocity_score=Decimal("90.0")
        ))
        
        # Medium ROI, Medium Velocity
        analyses.append(await self.analysis_repo.create_analysis(
            batch_id=self.test_batch.id,
            isbn_or_asin="978-MEDIUM001",
            buy_price=Decimal("12.00"),
            fees=Decimal("3.00"),
            expected_sale_price=Decimal("22.00"),
            profit=Decimal("7.00"),
            roi_percent=Decimal("58.33"),
            velocity_score=Decimal("65.0")
        ))
        
        # Low ROI, Low Velocity (Poor opportunity)
        analyses.append(await self.analysis_repo.create_analysis(
            batch_id=self.test_batch.id,
            isbn_or_asin="978-POOR001",
            buy_price=Decimal("25.00"),
            fees=Decimal("5.00"),
            expected_sale_price=Decimal("28.00"),
            profit=Decimal("-2.00"),
            roi_percent=Decimal("-8.00"),
            velocity_score=Decimal("15.0")
        ))
        
        return analyses

    async def test_list_by_roi_descending(self):
        """Test listing analyses sorted by ROI descending."""
        await self.create_sample_analyses()
        
        page = await self.analysis_repo.list_by_roi(
            batch_id=self.test_batch.id,
            sort_order=SortOrder.DESC
        )
        
        assert len(page.items) == 5
        assert page.total == 5
        
        # Verify descending ROI order
        for i in range(len(page.items) - 1):
            assert page.items[i].roi_percent >= page.items[i + 1].roi_percent

    async def test_list_by_roi_with_min_threshold(self):
        """Test listing analyses with minimum ROI filter."""
        await self.create_sample_analyses()
        
        page = await self.analysis_repo.list_by_roi(
            batch_id=self.test_batch.id,
            roi_min=Decimal("50.0")
        )
        
        # Should return 3 analyses with ROI >= 50%
        assert len(page.items) == 3
        
        for analysis in page.items:
            assert analysis.roi_percent >= Decimal("50.0")

    async def test_list_by_roi_with_range(self):
        """Test listing analyses with ROI range filter."""
        await self.create_sample_analyses()
        
        page = await self.analysis_repo.list_by_roi(
            batch_id=self.test_batch.id,
            roi_min=Decimal("20.0"),
            roi_max=Decimal("80.0")
        )
        
        # Should return analyses in 20-80% ROI range
        for analysis in page.items:
            assert Decimal("20.0") <= analysis.roi_percent <= Decimal("80.0")

    async def test_list_by_velocity_descending(self):
        """Test listing analyses sorted by velocity descending."""
        await self.create_sample_analyses()
        
        page = await self.analysis_repo.list_by_velocity(
            batch_id=self.test_batch.id,
            sort_order=SortOrder.DESC
        )
        
        assert len(page.items) == 5
        
        # Verify descending velocity order
        for i in range(len(page.items) - 1):
            assert page.items[i].velocity_score >= page.items[i + 1].velocity_score

    async def test_list_by_velocity_with_min_threshold(self):
        """Test listing analyses with minimum velocity filter."""
        await self.create_sample_analyses()
        
        page = await self.analysis_repo.list_by_velocity(
            batch_id=self.test_batch.id,
            velocity_min=Decimal("60.0")
        )
        
        # Should return analyses with velocity >= 60
        for analysis in page.items:
            assert analysis.velocity_score >= Decimal("60.0")

    async def test_list_filtered_combinations(self):
        """Test complex filtering with multiple criteria."""
        await self.create_sample_analyses()
        
        # High-quality opportunities: ROI >= 40%, Velocity >= 60%, Profit >= 5
        page = await self.analysis_repo.list_filtered(
            batch_id=self.test_batch.id,
            roi_min=Decimal("40.0"),
            velocity_min=Decimal("60.0"),
            profit_min=Decimal("5.0")
        )
        
        # Should match specific analyses
        for analysis in page.items:
            assert analysis.roi_percent >= Decimal("40.0")
            assert analysis.velocity_score >= Decimal("60.0")
            assert analysis.profit >= Decimal("5.0")

    async def test_list_filtered_with_sorting(self):
        """Test filtered list with custom sorting."""
        await self.create_sample_analyses()
        
        # Sort by profit descending
        page = await self.analysis_repo.list_filtered(
            batch_id=self.test_batch.id,
            sort_by=["profit"],
            sort_order=[SortOrder.DESC]
        )
        
        # Verify profit descending order
        for i in range(len(page.items) - 1):
            assert page.items[i].profit >= page.items[i + 1].profit

    async def test_list_filtered_pagination(self):
        """Test pagination with filtered results."""
        await self.create_sample_analyses()
        
        # Get first 2 items
        page1 = await self.analysis_repo.list_filtered(
            batch_id=self.test_batch.id,
            offset=0,
            limit=2
        )
        
        assert len(page1.items) == 2
        assert page1.total == 5
        assert page1.has_next is True
        assert page1.has_prev is False
        
        # Get next 2 items
        page2 = await self.analysis_repo.list_filtered(
            batch_id=self.test_batch.id,
            offset=2,
            limit=2
        )
        
        assert len(page2.items) == 2
        assert page2.has_next is True
        assert page2.has_prev is True
        
        # Verify no overlap
        page1_ids = {item.id for item in page1.items}
        page2_ids = {item.id for item in page2.items}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_top_n_for_batch_roi_strategy(self):
        """Test getting top N analyses by ROI strategy."""
        await self.create_sample_analyses()
        
        top_3 = await self.analysis_repo.top_n_for_batch(
            batch_id=self.test_batch.id,
            n=3,
            strategy="roi"
        )
        
        assert len(top_3) == 3
        
        # Should be sorted by ROI descending
        for i in range(len(top_3) - 1):
            assert top_3[i].roi_percent >= top_3[i + 1].roi_percent

    async def test_top_n_for_batch_velocity_strategy(self):
        """Test getting top N analyses by velocity strategy."""
        await self.create_sample_analyses()
        
        top_3 = await self.analysis_repo.top_n_for_batch(
            batch_id=self.test_batch.id,
            n=3,
            strategy="velocity"
        )
        
        assert len(top_3) == 3
        
        # Should be sorted by velocity descending
        for i in range(len(top_3) - 1):
            assert top_3[i].velocity_score >= top_3[i + 1].velocity_score

    async def test_top_n_for_batch_balanced_strategy(self):
        """Test getting top N analyses by balanced strategy."""
        await self.create_sample_analyses()
        
        top_3 = await self.analysis_repo.top_n_for_batch(
            batch_id=self.test_batch.id,
            n=3,
            strategy="balanced"
        )
        
        assert len(top_3) == 3
        
        # Calculate balanced scores and verify order
        scores = []
        for analysis in top_3:
            balanced_score = float(analysis.roi_percent) * 0.6 + float(analysis.velocity_score) * 0.4
            scores.append(balanced_score)
        
        # Should be descending
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

    async def test_count_by_thresholds(self):
        """Test counting analyses by various thresholds."""
        await self.create_sample_analyses()
        
        counts = await self.analysis_repo.count_by_thresholds(
            batch_id=self.test_batch.id
        )
        
        assert counts["total"] == 5
        assert "roi_above_30" in counts
        assert "velocity_above_50" in counts
        assert "profit_above_10" in counts
        assert "golden_opportunities" in counts
        
        # Verify specific counts
        assert counts["roi_above_30"] >= 0
        assert counts["velocity_above_50"] >= 0

    async def test_delete_by_batch(self):
        """Test deleting all analyses for a batch."""
        analyses = await self.create_sample_analyses()
        
        # Verify analyses exist
        page_before = await self.analysis_repo.list_filtered(batch_id=self.test_batch.id)
        assert len(page_before.items) == 5
        
        # Delete all analyses for the batch
        deleted_count = await self.analysis_repo.delete_by_batch(self.test_batch.id)
        
        assert deleted_count == 5
        
        # Verify analyses are gone
        page_after = await self.analysis_repo.list_filtered(batch_id=self.test_batch.id)
        assert len(page_after.items) == 0

    async def test_delete_by_ids(self):
        """Test deleting specific analyses by their IDs."""
        analyses = await self.create_sample_analyses()
        
        # Delete first 2 analyses
        ids_to_delete = [analyses[0].id, analyses[1].id]
        deleted_count = await self.analysis_repo.delete_by_ids(ids_to_delete)
        
        assert deleted_count == 2
        
        # Verify remaining analyses
        page_after = await self.analysis_repo.list_filtered(batch_id=self.test_batch.id)
        assert len(page_after.items) == 3
        
        # Verify deleted analyses are not in results
        remaining_ids = {item.id for item in page_after.items}
        for deleted_id in ids_to_delete:
            assert deleted_id not in remaining_ids

    async def test_get_batch_summary(self):
        """Test getting comprehensive batch summary statistics."""
        await self.create_sample_analyses()
        
        summary = await self.analysis_repo.get_batch_summary(self.test_batch.id)
        
        assert summary is not None
        assert summary["batch_id"] == self.test_batch.id
        assert summary["total_analyses"] == 5
        
        # Verify structure
        assert "averages" in summary
        assert "totals" in summary
        assert "maximums" in summary
        assert "minimums" in summary
        assert "threshold_counts" in summary
        
        # Verify averages are reasonable
        assert isinstance(summary["averages"]["roi_percent"], float)
        assert isinstance(summary["averages"]["velocity_score"], float)
        assert isinstance(summary["averages"]["profit"], float)

    async def test_get_batch_summary_empty_batch(self):
        """Test getting summary for empty batch returns None."""
        summary = await self.analysis_repo.get_batch_summary(self.test_batch.id)
        assert summary is None

    async def test_stable_sorting_with_pagination(self):
        """Test that sorting is stable across paginated results."""
        # Create analyses with same ROI values to test stable sorting
        for i in range(5):
            await self.analysis_repo.create_analysis(
                batch_id=self.test_batch.id,
                isbn_or_asin=f"978-STABLE{i:03d}",
                buy_price=Decimal("10.00"),
                fees=Decimal("2.00"),
                expected_sale_price=Decimal("20.00"),
                profit=Decimal("8.00"),
                roi_percent=Decimal("80.00"),  # Same ROI for all
                velocity_score=Decimal("70.0")
            )
        
        # Get results in two pages
        page1 = await self.analysis_repo.list_by_roi(
            batch_id=self.test_batch.id,
            offset=0,
            limit=3
        )
        
        page2 = await self.analysis_repo.list_by_roi(
            batch_id=self.test_batch.id,
            offset=3,
            limit=3
        )
        
        # Verify stable sort - results should be consistent
        all_ids_first_call = [item.id for item in page1.items] + [item.id for item in page2.items]
        
        # Call again and verify same order
        page1_second = await self.analysis_repo.list_by_roi(
            batch_id=self.test_batch.id,
            offset=0,
            limit=3
        )
        
        page2_second = await self.analysis_repo.list_by_roi(
            batch_id=self.test_batch.id,
            offset=3,
            limit=3
        )
        
        all_ids_second_call = [item.id for item in page1_second.items] + [item.id for item in page2_second.items]
        
        assert all_ids_first_call == all_ids_second_call