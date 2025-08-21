"""
Performance benchmarking suite with p50/p95/p99 measurements
Tests response times against defined targets with statistical rigor
"""
import asyncio
from typing import Dict, Any

from ..utils.database import get_audit_db_session
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.batch_repository import BatchRepository  
from app.repositories.user_repository import UserRepository
from app.models.user import UserRole
from ..fixtures.sample_batches import SampleDataGenerator
from ..utils.metrics_collector import MetricsCollector


class PerformanceSuite:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.data_generator = SampleDataGenerator()
        
    async def run_benchmark(self, dataset_size: int) -> Dict[str, Any]:
        """Run complete performance benchmark for given dataset size"""
        print(f"  🏃 Setting up {dataset_size:,} item dataset...")
        
        # Setup test data
        batch_id, analysis_ids = await self._setup_test_data(dataset_size)
        
        try:
            results = {}
            
            # Test basic listing performance
            results.update(await self._benchmark_basic_listing(batch_id, dataset_size))
            
            # Test filtered queries
            results.update(await self._benchmark_filtered_queries(batch_id))
            
            # Test pagination performance
            results.update(await self._benchmark_pagination(batch_id, dataset_size))
            
            # Test top-N queries
            results.update(await self._benchmark_top_queries(batch_id))
            
            return results
            
        finally:
            # Cleanup test data
            await self._cleanup_test_data(batch_id, analysis_ids)
    
    async def _setup_test_data(self, size: int) -> tuple[int, list[int]]:
        """Setup test dataset and return batch_id and analysis_ids"""
        with get_audit_db_session() as session:
            # Create test user
            user_repo = UserRepository(session)
            user_data = self.data_generator.generate_test_user(UserRole.SOURCER)
            user = user_repo.create(**user_data)
            
            # Create test batch
            batch_repo = BatchRepository(session)
            batch_data, analyses_data = self.data_generator.create_performance_dataset(size)
            batch_data['user_id'] = user.id
            batch = batch_repo.create(**batch_data)
            
            # Create analyses
            analysis_repo = AnalysisRepository(session)
            analysis_ids = []
            
            # Batch insert for performance
            for i, analysis_data in enumerate(analyses_data):
                if i % 1000 == 0:
                    print(f"    Creating analyses: {i:,}/{size:,}")
                    
                analysis_data['batch_id'] = batch.id
                analysis = analysis_repo.create(**analysis_data)
                analysis_ids.append(analysis.id)
            
            session.commit()
            print(f"    ✅ Created {len(analysis_ids):,} analyses in batch {batch.id}")
            
            return batch.id, analysis_ids
    
    async def _cleanup_test_data(self, batch_id: int, analysis_ids: list[int]):
        """Clean up test data"""
        with get_audit_db_session() as session:
            analysis_repo = AnalysisRepository(session)
            batch_repo = BatchRepository(session)
            
            # Delete analyses (should cascade, but being explicit)
            print(f"    🧹 Cleaning up {len(analysis_ids):,} analyses...")
            for analysis_id in analysis_ids:
                analysis_repo.delete(analysis_id)
            
            # Delete batch
            batch_repo.delete(batch_id)
            session.commit()
    
    async def _benchmark_basic_listing(self, batch_id: int, dataset_size: int) -> Dict[str, Any]:
        """Benchmark basic listing operations"""
        results = {}
        
        def run_basic_query():
            with get_audit_db_session() as session:
                repo = AnalysisRepository(session)
                analyses, _ = repo.list_filtered(
                    batch_id=batch_id,
                    offset=0,
                    limit=100
                )
                return len(analyses)
        
        # Warmup
        self.metrics.run_warmup(run_basic_query, 1)
        
        # Benchmark 100 items query
        print(f"    📊 Benchmarking basic listing (100 items from {dataset_size:,})...")
        results['basic_100_items'] = self.metrics.run_timed_iterations(
            f'{dataset_size}_items_basic',
            run_basic_query,
            30
        )
        
        # Also test larger result sets if dataset is big enough
        if dataset_size >= 1000:
            def run_large_query():
                with get_audit_db_session() as session:
                    repo = AnalysisRepository(session)
                    analyses, _ = repo.list_filtered(
                        batch_id=batch_id,
                        offset=0,
                        limit=1000
                    )
                    return len(analyses)
            
            print(f"    📊 Benchmarking large listing (1000 items)...")
            results['basic_1000_items'] = self.metrics.run_timed_iterations(
                f'{dataset_size}_items_large',
                run_large_query,
                30
            )
        
        return results
    
    async def _benchmark_filtered_queries(self, batch_id: int) -> Dict[str, Any]:
        """Benchmark filtered queries with various combinations"""
        results = {}
        
        # ROI filter test
        def run_roi_filter():
            with get_audit_db_session() as session:
                repo = AnalysisRepository(session)
                analyses, _ = repo.list_filtered(
                    batch_id=batch_id,
                    min_roi=30.0,
                    max_roi=80.0,
                    offset=0,
                    limit=100
                )
                return len(analyses)
        
        print("    📊 Benchmarking ROI filter...")
        results['roi_filter'] = self.metrics.run_timed_iterations(
            'roi_filter',
            run_roi_filter,
            30
        )
        
        # Combined filters test
        def run_combined_filters():
            with get_audit_db_session() as session:
                repo = AnalysisRepository(session)
                analyses, _ = repo.list_filtered(
                    batch_id=batch_id,
                    min_roi=25.0,
                    min_velocity=0.4,
                    profit_min=5.0,
                    offset=0,
                    limit=100
                )
                return len(analyses)
        
        print("    📊 Benchmarking combined filters...")
        results['combined_filters'] = self.metrics.run_timed_iterations(
            'combined_filters',
            run_combined_filters,
            30
        )
        
        return results
    
    async def _benchmark_pagination(self, batch_id: int, dataset_size: int) -> Dict[str, Any]:
        """Benchmark pagination performance, especially deep pagination"""
        results = {}
        
        # Test pagination at different depths
        if dataset_size >= 5000:
            # Deep pagination test (page 50+ with 100 items per page)
            deep_offset = 5000
            
            def run_deep_pagination():
                with get_audit_db_session() as session:
                    repo = AnalysisRepository(session)
                    analyses, _ = repo.list_filtered(
                        batch_id=batch_id,
                        offset=deep_offset,
                        limit=100
                    )
                    return len(analyses)
            
            print("    📊 Benchmarking deep pagination (offset 5000)...")
            results['deep_pagination'] = self.metrics.run_timed_iterations(
                'deep_pagination',
                run_deep_pagination,
                30
            )
        
        return results
    
    async def _benchmark_top_queries(self, batch_id: int) -> Dict[str, Any]:
        """Benchmark strategic top-N queries"""
        results = {}
        
        # Top ROI query
        def run_top_roi():
            with get_audit_db_session() as session:
                repo = AnalysisRepository(session)
                analyses = repo.top_n_for_batch(
                    batch_id=batch_id,
                    n=10,
                    strategy='roi'
                )
                return len(analyses)
        
        print("    📊 Benchmarking top ROI query...")
        results['top_roi'] = self.metrics.run_timed_iterations(
            'top_roi',
            run_top_roi,
            30
        )
        
        # Balanced strategy query
        def run_top_balanced():
            with get_audit_db_session() as session:
                repo = AnalysisRepository(session)
                analyses = repo.top_n_for_batch(
                    batch_id=batch_id,
                    n=10,
                    strategy='balanced'
                )
                return len(analyses)
        
        print("    📊 Benchmarking balanced strategy query...")
        results['top_balanced'] = self.metrics.run_timed_iterations(
            'top_balanced',
            run_top_balanced,
            30
        )
        
        return results