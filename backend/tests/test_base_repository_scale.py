"""Large scale performance tests for BaseRepository (10k-50k records)."""

import pytest
import time
from decimal import Decimal
import uuid

from app.repositories.base_repository import BaseRepository, SortOrder
from app.models.analysis import Analysis


class AnalysisRepositoryScale(BaseRepository[Analysis]):
    """Scale test repository for Analysis model."""
    SORTABLE_FIELDS = ["id", "roi_percent", "velocity_score", "profit", "created_at"]
    FILTERABLE_FIELDS = ["id", "batch_id", "roi_percent", "velocity_score", "profit"]


class TestBaseRepositoryScale:
    """Large scale performance tests (10k-50k records)."""

    @pytest.fixture
    async def dataset_10k(self, async_db_session, sample_batches):
        """Create 10k analyses for scale testing."""
        batch = sample_batches[0]
        analyses = []
        
        print(f"\n🏗️  Creating 10k analysis records...")
        start_time = time.time()
        
        for i in range(10_000):
            analysis = Analysis(
                id=str(uuid.uuid4()),
                batch_id=batch.id,
                isbn_or_asin=f"978-{i:010d}",
                buy_price=Decimal(f"{10 + (i % 100)}.{i % 100:02d}"),
                fees=Decimal(f"{2 + (i % 20)}.{(i * 7) % 100:02d}"),
                expected_sale_price=Decimal(f"{20 + (i % 200)}.{(i * 13) % 100:02d}"),
                profit=Decimal(f"{5 + (i % 50)}.{(i * 17) % 100:02d}"),
                roi_percent=Decimal(f"{10 + (i % 150)}.{(i * 23) % 100:02d}"),
                velocity_score=Decimal(f"{1 + (i % 9)}.{(i * 11) % 10}"),
                raw_keepa={"scale_test_id": i, "batch": "10k"}
            )
            analyses.append(analysis)
        
        # Batch insert
        async_db_session.add_all(analyses)
        await async_db_session.commit()
        
        setup_time = time.time() - start_time
        print(f"✅ 10k records created in {setup_time:.2f}s")
        
        return analyses

    @pytest.fixture
    async def dataset_50k(self, async_db_session, sample_batches):
        """Create 50k analyses for extreme scale testing."""
        batch = sample_batches[0]
        analyses = []
        
        print(f"\n🏗️  Creating 50k analysis records...")
        start_time = time.time()
        
        # Create in chunks for memory efficiency
        chunk_size = 5000
        for chunk_start in range(0, 50_000, chunk_size):
            chunk_analyses = []
            
            for i in range(chunk_start, min(chunk_start + chunk_size, 50_000)):
                analysis = Analysis(
                    id=str(uuid.uuid4()),
                    batch_id=batch.id,
                    isbn_or_asin=f"978-{i:010d}",
                    buy_price=Decimal(f"{10 + (i % 100)}.{i % 100:02d}"),
                    fees=Decimal(f"{2 + (i % 20)}.{(i * 7) % 100:02d}"),
                    expected_sale_price=Decimal(f"{20 + (i % 200)}.{(i * 13) % 100:02d}"),
                    profit=Decimal(f"{5 + (i % 50)}.{(i * 17) % 100:02d}"),
                    roi_percent=Decimal(f"{10 + (i % 150)}.{(i * 23) % 100:02d}"),
                    velocity_score=Decimal(f"{1 + (i % 9)}.{(i * 11) % 10}"),
                    raw_keepa={"scale_test_id": i, "batch": "50k"}
                )
                chunk_analyses.append(analysis)
            
            # Insert chunk
            async_db_session.add_all(chunk_analyses)
            await async_db_session.commit()
            
            if chunk_start % 10000 == 0:
                print(f"   📊 Inserted {chunk_start + chunk_size} records...")
        
        setup_time = time.time() - start_time
        print(f"✅ 50k records created in {setup_time:.2f}s")
        
        return 50_000  # Return count instead of list for memory

    @pytest.fixture(autouse=True)
    async def setup_scale_repo(self, async_db_session):
        """Setup scale test repository."""
        self.analysis_repo = AnalysisRepositoryScale(async_db_session, Analysis)

    async def test_10k_first_page_performance(self, dataset_10k):
        """Test first page performance with 10k records."""
        start_time = time.time()
        
        page = await self.analysis_repo.list(
            offset=0,
            limit=100,
            sort_by=["roi_percent"],
            sort_order=[SortOrder.DESC]
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Validate results
        assert len(page.items) == 100
        assert page.total == 10_000
        assert page.has_next is True
        
        # Performance target: <100ms even with 10k records
        assert duration_ms < 100, f"First page (10k): {duration_ms:.2f}ms, expected <100ms"
        
        print(f"📊 10k dataset - First page: {duration_ms:.2f}ms")

    async def test_10k_middle_page_performance(self, dataset_10k):
        """Test middle page performance with 10k records."""
        start_time = time.time()
        
        # Page 50 (offset 4900)
        page = await self.analysis_repo.list(
            offset=4900,
            limit=100,
            sort_by=["roi_percent", "id"],
            sort_order=[SortOrder.DESC, SortOrder.ASC]
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Validate results
        assert len(page.items) == 100
        assert page.offset == 4900
        
        # Performance target: <150ms for middle pages
        assert duration_ms < 150, f"Middle page (10k): {duration_ms:.2f}ms, expected <150ms"
        
        print(f"📊 10k dataset - Middle page (offset 4900): {duration_ms:.2f}ms")

    async def test_10k_filtered_query_performance(self, dataset_10k):
        """Test filtered query performance with 10k records."""
        start_time = time.time()
        
        page = await self.analysis_repo.list(
            filters={
                "roi_percent": {"operator": "gte", "value": Decimal("100.00")},
                "velocity_score": {"operator": "lte", "value": Decimal("8.0")}
            },
            sort_by=["profit"],
            sort_order=[SortOrder.DESC],
            limit=100
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Validate filtering 
        for analysis in page.items:
            assert analysis.roi_percent >= Decimal("100.00")
            assert analysis.velocity_score <= Decimal("8.0")
        
        # Performance target: <200ms for complex filtered queries
        assert duration_ms < 200, f"Filtered query (10k): {duration_ms:.2f}ms, expected <200ms"
        
        print(f"📊 10k dataset - Filtered query: {duration_ms:.2f}ms (results: {len(page.items)})")

    @pytest.mark.slow
    async def test_50k_extreme_pagination_performance(self, dataset_50k):
        """Test extreme pagination performance with 50k records."""
        # Test deep pagination at various points
        test_cases = [
            (0, "First page"),
            (24900, "Middle page (page 250)"),
            (49900, "Last page (page 500)")
        ]
        
        for offset, description in test_cases:
            start_time = time.time()
            
            page = await self.analysis_repo.list(
                offset=offset,
                limit=100,
                sort_by=["roi_percent", "id"],
                sort_order=[SortOrder.DESC, SortOrder.ASC]
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Validate results
            expected_items = min(100, 50_000 - offset)
            assert len(page.items) == expected_items
            assert page.total == 50_000
            
            # Performance target: <250ms even for extreme pagination
            assert duration_ms < 250, f"{description} (50k): {duration_ms:.2f}ms, expected <250ms"
            
            print(f"📊 50k dataset - {description}: {duration_ms:.2f}ms")

    @pytest.mark.slow
    async def test_50k_count_performance(self, dataset_50k):
        """Test count performance with 50k records and filters."""
        start_time = time.time()
        
        count = await self.analysis_repo.count(
            filters={"roi_percent": {"operator": "gte", "value": Decimal("50.0")}}
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Validate count
        assert count > 0
        assert count <= 50_000
        
        # Performance target: <100ms for count queries
        assert duration_ms < 100, f"Count query (50k): {duration_ms:.2f}ms, expected <100ms"
        
        print(f"📊 50k dataset - Count with filter: {duration_ms:.2f}ms (count: {count})")

    @pytest.mark.slow
    async def test_degradation_analysis(self, dataset_10k):
        """Analyze performance degradation across different offsets.

        Note: This test is marked slow and has a relaxed assertion because
        performance can vary significantly based on system load.
        """
        offsets_to_test = [0, 1000, 2500, 5000, 7500, 9900]
        results = []

        print(f"\nPerformance degradation analysis:")

        for offset in offsets_to_test:
            start_time = time.time()

            page = await self.analysis_repo.list(
                offset=offset,
                limit=100,
                sort_by=["roi_percent"],
                sort_order=[SortOrder.DESC]
            )

            duration_ms = (time.time() - start_time) * 1000
            results.append((offset, duration_ms))

            print(f"   Offset {offset:5d}: {duration_ms:6.2f}ms")

        # Check that degradation is not too severe
        first_page_time = results[0][1]
        last_page_time = results[-1][1]

        # Avoid division by zero and handle very fast queries
        if first_page_time < 1.0:
            first_page_time = 1.0

        degradation_ratio = last_page_time / first_page_time

        # Relaxed assertion: 5x allows for system variability
        # In practice, SQLite in-memory should be much faster
        assert degradation_ratio < 5.0, f"Performance degradation too severe: {degradation_ratio:.1f}x"

        print(f"Performance degradation ratio: {degradation_ratio:.1f}x (should be <5x)")