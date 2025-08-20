"""Concurrency tests with separate sessions for BaseRepository."""

import pytest
import asyncio
from decimal import Decimal
import uuid
from typing import List

from app.repositories.base_repository import BaseRepository, SortOrder
from app.models.analysis import Analysis
from tests.conftest import AsyncSessionLocal


class AnalysisRepositoryConcurrent(BaseRepository[Analysis]):
    """Concurrent test repository for Analysis model."""
    SORTABLE_FIELDS = ["id", "roi_percent", "velocity_score", "profit", "created_at"]
    FILTERABLE_FIELDS = ["id", "batch_id", "roi_percent", "velocity_score", "profit"]


class TestBaseRepositoryConcurrent:
    """Concurrency tests with separate database sessions."""

    @pytest.fixture
    async def concurrent_dataset(self, sample_batches):
        """Create dataset for concurrent access tests."""
        batch = sample_batches[0]
        analyses = []
        
        # Use a separate session for setup
        async with AsyncSessionLocal() as setup_session:
            for i in range(1000):
                analysis = Analysis(
                    id=str(uuid.uuid4()),
                    batch_id=batch.id,
                    isbn_or_asin=f"978-{i:010d}",
                    buy_price=Decimal(f"{10 + (i % 50)}.{i % 100:02d}"),
                    fees=Decimal(f"{2 + (i % 10)}.{(i * 7) % 100:02d}"),
                    expected_sale_price=Decimal(f"{20 + (i % 100)}.{(i * 13) % 100:02d}"),
                    profit=Decimal(f"{5 + (i % 30)}.{(i * 17) % 100:02d}"),
                    roi_percent=Decimal(f"{10 + (i % 100)}.{(i * 23) % 100:02d}"),
                    velocity_score=Decimal(f"{1 + (i % 9)}.{(i * 11) % 10}"),
                    raw_keepa={"concurrent_test_id": i}
                )
                analyses.append(analysis)
            
            setup_session.add_all(analyses)
            await setup_session.commit()
            
            return len(analyses)

    async def _query_worker(self, worker_id: int, total_operations: int) -> List[float]:
        """Worker function for concurrent queries using separate session."""
        durations = []
        
        # Each worker gets its own session
        async with AsyncSessionLocal() as session:
            repo = AnalysisRepositoryConcurrent(session, Analysis)
            
            for i in range(total_operations):
                import time
                start_time = time.time()
                
                # Vary query patterns to simulate real usage
                offset = (worker_id * 100 + i * 10) % 900
                
                page = await repo.list(
                    offset=offset,
                    limit=20,
                    sort_by=["roi_percent"],
                    sort_order=[SortOrder.DESC]
                )
                
                duration_ms = (time.time() - start_time) * 1000
                durations.append(duration_ms)
                
                # Validate basic results
                assert len(page.items) <= 20
                assert page.total == 1000
        
        return durations

    async def test_concurrent_queries_separate_sessions(self, concurrent_dataset):
        """Test concurrent queries with separate sessions."""
        num_workers = 5
        operations_per_worker = 20
        
        print(f"\n🔄 Testing {num_workers} workers × {operations_per_worker} operations each")
        
        # Start concurrent workers
        tasks = []
        for worker_id in range(num_workers):
            task = asyncio.create_task(
                self._query_worker(worker_id, operations_per_worker)
            )
            tasks.append(task)
        
        # Wait for all workers to complete
        results = await asyncio.gather(*tasks)
        
        # Analyze results
        all_durations = []
        for worker_id, worker_durations in enumerate(results):
            all_durations.extend(worker_durations)
            avg_duration = sum(worker_durations) / len(worker_durations)
            max_duration = max(worker_durations)
            print(f"   Worker {worker_id}: avg {avg_duration:.2f}ms, max {max_duration:.2f}ms")
        
        # Overall statistics
        total_operations = sum(len(durations) for durations in results)
        avg_duration = sum(all_durations) / len(all_durations)
        max_duration = max(all_durations)
        p95_duration = sorted(all_durations)[int(0.95 * len(all_durations))]
        
        print(f"📊 Total operations: {total_operations}")
        print(f"📊 Average duration: {avg_duration:.2f}ms")
        print(f"📊 P95 duration: {p95_duration:.2f}ms")
        print(f"📊 Max duration: {max_duration:.2f}ms")
        
        # Performance assertions
        assert avg_duration < 50, f"Average duration {avg_duration:.2f}ms exceeds 50ms"
        assert p95_duration < 100, f"P95 duration {p95_duration:.2f}ms exceeds 100ms"
        assert max_duration < 200, f"Max duration {max_duration:.2f}ms exceeds 200ms"

    async def _mixed_operations_worker(self, worker_id: int) -> dict:
        """Worker performing mixed read/write operations."""
        async with AsyncSessionLocal() as session:
            repo = AnalysisRepositoryConcurrent(session, Analysis)
            
            operations = {"reads": 0, "counts": 0, "durations": []}
            
            for i in range(10):
                import time
                
                # Read operation
                start_time = time.time()
                page = await repo.list(
                    offset=worker_id * 50,
                    limit=10,
                    filters={"roi_percent": {"operator": "gte", "value": Decimal("50.0")}},
                    sort_by=["profit"],
                    sort_order=[SortOrder.DESC]
                )
                read_duration = (time.time() - start_time) * 1000
                operations["reads"] += 1
                operations["durations"].append(("read", read_duration))
                
                # Count operation
                start_time = time.time()
                count = await repo.count(
                    filters={"velocity_score": {"operator": "lte", "value": Decimal("8.0")}}
                )
                count_duration = (time.time() - start_time) * 1000
                operations["counts"] += 1
                operations["durations"].append(("count", count_duration))
                
                # Validate results
                assert len(page.items) <= 10
                assert count > 0
            
            return operations

    async def test_mixed_concurrent_operations(self, concurrent_dataset):
        """Test mixed read/count operations with separate sessions."""
        num_workers = 3
        
        print(f"\n🔀 Testing mixed operations with {num_workers} workers")
        
        # Start concurrent workers
        tasks = []
        for worker_id in range(num_workers):
            task = asyncio.create_task(
                self._mixed_operations_worker(worker_id)
            )
            tasks.append(task)
        
        # Wait for completion
        results = await asyncio.gather(*tasks)
        
        # Analyze results by operation type
        read_durations = []
        count_durations = []
        
        for worker_id, worker_results in enumerate(results):
            worker_reads = [d for op, d in worker_results["durations"] if op == "read"]
            worker_counts = [d for op, d in worker_results["durations"] if op == "count"]
            
            read_durations.extend(worker_reads)
            count_durations.extend(worker_counts)
            
            print(f"   Worker {worker_id}: {worker_results['reads']} reads, {worker_results['counts']} counts")
        
        # Performance statistics
        avg_read = sum(read_durations) / len(read_durations)
        avg_count = sum(count_durations) / len(count_durations)
        
        print(f"📊 Read operations: {len(read_durations)} total, {avg_read:.2f}ms avg")
        print(f"📊 Count operations: {len(count_durations)} total, {avg_count:.2f}ms avg")
        
        # Assertions
        assert avg_read < 100, f"Average read duration {avg_read:.2f}ms too high"
        assert avg_count < 50, f"Average count duration {avg_count:.2f}ms too high"

    async def test_session_isolation(self, concurrent_dataset):
        """Test that sessions are properly isolated."""
        
        # Two separate sessions should not interfere
        async with AsyncSessionLocal() as session1:
            repo1 = AnalysisRepositoryConcurrent(session1, Analysis)
            
            async with AsyncSessionLocal() as session2:
                repo2 = AnalysisRepositoryConcurrent(session2, Analysis)
                
                # Concurrent queries on different sessions
                import asyncio
                
                task1 = asyncio.create_task(
                    repo1.list(offset=0, limit=50, sort_by=["roi_percent"])
                )
                task2 = asyncio.create_task(
                    repo2.count(filters={"profit": {"operator": "gte", "value": Decimal("20.0")}})
                )
                
                page, count = await asyncio.gather(task1, task2)
                
                # Both operations should succeed
                assert len(page.items) <= 50
                assert page.total == 1000
                assert count >= 0
                
                print(f"📊 Session isolation test: page with {len(page.items)} items, count {count}")

    async def test_transaction_boundaries(self, concurrent_dataset):
        """Test that each session maintains proper transaction boundaries."""
        
        errors = []
        
        async def transaction_worker(worker_id: int):
            try:
                async with AsyncSessionLocal() as session:
                    repo = AnalysisRepositoryConcurrent(session, Analysis)
                    
                    # Multiple operations in same transaction
                    page1 = await repo.list(offset=0, limit=10)
                    count1 = await repo.count()
                    page2 = await repo.list(
                        filters={"roi_percent": {"operator": "gte", "value": Decimal("75.0")}},
                        limit=5
                    )
                    
                    # All should see consistent data
                    assert page1.total == count1 == 1000
                    assert len(page1.items) == 10
                    assert len(page2.items) <= 5
                    
                    return {
                        "worker_id": worker_id,
                        "total_records": count1,
                        "filtered_results": len(page2.items)
                    }
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")
                raise
        
        # Run multiple workers
        tasks = [transaction_worker(i) for i in range(4)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for errors
        if errors:
            print(f"❌ Transaction errors: {errors}")
            pytest.fail("Transaction boundary errors occurred")
        
        # Validate all workers saw consistent data
        total_counts = [r["total_records"] for r in results if isinstance(r, dict)]
        assert all(count == 1000 for count in total_counts), f"Inconsistent counts: {total_counts}"
        
        print(f"📊 Transaction boundaries verified across {len(results)} workers")