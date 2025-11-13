"""Performance tests for BaseRepository with larger datasets."""

import pytest
import asyncio
import time
from decimal import Decimal
import uuid

from app.repositories.base_repository import BaseRepository, SortOrder
from app.models.analysis import Analysis


class AnalysisRepositoryPerf(BaseRepository[Analysis]):
    """Performance test repository for Analysis model."""
    SORTABLE_FIELDS = ["id", "roi_percent", "velocity_score", "profit", "created_at"]
    FILTERABLE_FIELDS = ["id", "batch_id", "roi_percent", "velocity_score", "profit"]


class TestBaseRepositoryPerformance:
    """Performance tests for BaseRepository with realistic data volumes."""

    @pytest.fixture
    async def large_analysis_dataset(self, async_db_session, sample_batches):
        """Create a larger dataset for performance testing."""
        batch = sample_batches[0]
        analyses = []
        
        # Create 1000 analyses for performance testing
        for i in range(1000):
            analysis = Analysis(
                id=str(uuid.uuid4()),
                batch_id=batch.id,
                isbn_or_asin=f"978-{i:010d}",
                buy_price=Decimal(f"{10 + (i % 50)}.00"),
                fees=Decimal(f"{2 + (i % 10)}.50"),
                expected_sale_price=Decimal(f"{20 + (i % 100)}.00"),
                profit=Decimal(f"{5 + (i % 25)}.00"),
                roi_percent=Decimal(f"{10 + (i % 90)}.00"),
                velocity_score=Decimal(f"{1 + (i % 9)}.5"),
                raw_keepa={"test_id": i}
            )
            analyses.append(analysis)
        
        # Batch insert for performance
        async_db_session.add_all(analyses)
        await async_db_session.commit()
        
        return analyses

    @pytest.fixture(autouse=True)
    async def setup_perf_repo(self, async_db_session, large_analysis_dataset):
        """Setup performance test repository."""
        self.analysis_repo = AnalysisRepositoryPerf(async_db_session, Analysis)
        self.analyses = large_analysis_dataset

    async def test_large_dataset_list_performance(self):
        """Test list performance with 1000 records."""
        start_time = time.time()
        
        page = await self.analysis_repo.list(
            offset=0,
            limit=100,
            sort_by=["roi_percent"],
            sort_order=[SortOrder.DESC]
        )
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Validate results
        assert len(page.items) == 100
        assert page.total == 1000
        assert page.has_next is True
        
        # Performance assertion - should be under 100ms for 1000 records
        assert duration_ms < 100, f"Query took {duration_ms:.2f}ms, expected <100ms"
        
        print(f"\n✅ Large dataset query: {duration_ms:.2f}ms")

    async def test_deep_pagination_performance(self):
        """Test performance with deep pagination (page 50)."""
        start_time = time.time()
        
        page = await self.analysis_repo.list(
            offset=490,  # Page 50 with limit=10
            limit=10,
            sort_by=["roi_percent", "id"],
            sort_order=[SortOrder.DESC, SortOrder.ASC]
        )
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Validate results
        assert len(page.items) == 10
        assert page.total == 1000
        assert page.offset == 490
        
        # Performance target: <250ms for deep pagination
        assert duration_ms < 250, f"Deep pagination took {duration_ms:.2f}ms, expected <250ms"
        
        print(f"✅ Deep pagination (page 50): {duration_ms:.2f}ms")

    async def test_filtered_query_performance(self):
        """Test performance with range filters."""
        start_time = time.time()
        
        page = await self.analysis_repo.list(
            filters={
                "roi_percent": {"operator": "gte", "value": 50.0},
                "velocity_score": {"operator": "lte", "value": 8.0}
            },
            sort_by=["profit"],
            sort_order=[SortOrder.DESC],
            limit=50
        )
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Validate filtering worked
        for analysis in page.items:
            assert analysis.roi_percent >= 50.0
            assert analysis.velocity_score <= 8.0
        
        # Performance assertion
        assert duration_ms < 150, f"Filtered query took {duration_ms:.2f}ms, expected <150ms"
        
        print(f"✅ Filtered query: {duration_ms:.2f}ms")

    async def test_count_performance(self):
        """Test count performance with filters."""
        start_time = time.time()
        
        count = await self.analysis_repo.count(
            filters={"roi_percent": {"operator": "gte", "value": 30.0}}
        )
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Validate count
        assert count > 0
        assert count <= 1000
        
        # Performance assertion
        assert duration_ms < 50, f"Count query took {duration_ms:.2f}ms, expected <50ms"
        
        print(f"✅ Count with filter: {duration_ms:.2f}ms (count: {count})")

    async def test_multiple_concurrent_queries(self):
        """Test concurrent query performance."""
        async def query_task(offset: int) -> float:
            start = time.time()
            page = await self.analysis_repo.list(
                offset=offset,
                limit=20,
                sort_by=["roi_percent"],
                sort_order=[SortOrder.DESC]
            )
            duration = (time.time() - start) * 1000
            assert len(page.items) == 20
            return duration
        
        # Run 5 concurrent queries
        start_total = time.time()
        tasks = [query_task(i * 20) for i in range(5)]
        durations = await asyncio.gather(*tasks)
        total_duration = (time.time() - start_total) * 1000
        
        # All individual queries should be fast
        for duration in durations:
            assert duration < 100, f"Individual query took {duration:.2f}ms"
        
        # Total time should show concurrency benefit
        assert total_duration < 300, f"5 concurrent queries took {total_duration:.2f}ms"
        
        avg_duration = sum(durations) / len(durations)
        print(f"✅ 5 concurrent queries: avg {avg_duration:.2f}ms, total {total_duration:.2f}ms")