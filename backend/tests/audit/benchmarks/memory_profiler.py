"""
Memory profiling utilities for audit suite
Tracks RSS memory usage and tracemalloc peaks during operations
"""
import gc
import tracemalloc
from typing import Dict, Any

from ..utils.database import get_audit_db_session
from app.repositories.analysis_repository import AnalysisRepository
from ..fixtures.sample_batches import SampleDataGenerator
from ..utils.metrics_collector import MetricsCollector


class MemoryProfiler:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.data_generator = SampleDataGenerator()
        
    async def profile_operations(self) -> Dict[str, Any]:
        """Profile memory usage across various operations"""
        results = {}
        
        print("    🧠 Profiling memory usage...")
        
        # Profile dataset creation
        results['dataset_creation'] = await self._profile_dataset_creation()
        
        # Profile query operations
        results['query_operations'] = await self._profile_query_operations()
        
        # Profile overall memory behavior
        results['memory_summary'] = self._get_memory_summary()
        
        return results
    
    async def _profile_dataset_creation(self) -> Dict[str, Any]:
        """Profile memory usage during dataset creation"""
        results = {}
        
        # Test different dataset sizes
        sizes = [100, 1000, 5000]
        
        for size in sizes:
            if size > 1000:  # Skip large datasets in memory profiling
                print(f"      ⏭️  Skipping {size} items (too large for memory test)")
                continue
                
            print(f"      📈 Profiling {size} item dataset creation...")
            
            # Force garbage collection before test
            gc.collect()
            
            with self.metrics.memory_trace(f'create_{size}_items'):
                batch_id, analysis_ids = await self._create_temp_dataset(size)
                # Cleanup immediately
                await self._cleanup_temp_dataset(batch_id, analysis_ids)
            
            # Get results
            profile_result = self.metrics.get_operation_summary(f'create_{size}_items')
            results[f'{size}_items'] = profile_result
        
        return results
    
    async def _profile_query_operations(self) -> Dict[str, Any]:
        """Profile memory usage during various query operations"""
        results = {}
        
        # Create a medium-sized dataset for querying
        print("      🏗️  Setting up query test dataset...")
        batch_id, analysis_ids = await self._create_temp_dataset(1000)
        
        try:
            # Profile different query types
            query_types = [
                ('simple_list', self._simple_list_query),
                ('filtered_query', self._filtered_query),
                ('top_n_query', self._top_n_query)
            ]
            
            for query_name, query_func in query_types:
                print(f"      🔍 Profiling {query_name}...")
                
                gc.collect()  # Clean slate
                
                with self.metrics.memory_trace(query_name):
                    # Run query multiple times to see memory behavior
                    for _ in range(10):
                        query_func(batch_id)
                
                results[query_name] = self.metrics.get_operation_summary(query_name)
        
        finally:
            # Cleanup
            await self._cleanup_temp_dataset(batch_id, analysis_ids)
        
        return results
    
    def _simple_list_query(self, batch_id: int):
        """Simple list query for memory profiling"""
        with get_audit_db_session() as session:
            repo = AnalysisRepository(session)
            analyses, _ = repo.list_filtered(
                batch_id=batch_id,
                offset=0,
                limit=100
            )
            return len(analyses)
    
    def _filtered_query(self, batch_id: int):
        """Filtered query for memory profiling"""
        with get_audit_db_session() as session:
            repo = AnalysisRepository(session)
            analyses, _ = repo.list_filtered(
                batch_id=batch_id,
                min_roi=20.0,
                min_velocity=0.3,
                offset=0,
                limit=100
            )
            return len(analyses)
    
    def _top_n_query(self, batch_id: int):
        """Top-N query for memory profiling"""
        with get_audit_db_session() as session:
            repo = AnalysisRepository(session)
            analyses = repo.top_n_for_batch(
                batch_id=batch_id,
                n=20,
                strategy='balanced'
            )
            return len(analyses)
    
    async def _create_temp_dataset(self, size: int) -> tuple[int, list[int]]:
        """Create temporary dataset for memory testing"""
        with get_audit_db_session() as session:
            from app.repositories.batch_repository import BatchRepository
            from app.repositories.user_repository import UserRepository
            from app.models.user import UserRole
            
            # Create user
            user_repo = UserRepository(session)
            user_data = self.data_generator.generate_test_user(UserRole.SOURCER)
            user = user_repo.create(**user_data)
            
            # Create batch
            batch_repo = BatchRepository(session)
            batch_data, analyses_data = self.data_generator.create_performance_dataset(size)
            batch_data['user_id'] = user.id
            batch = batch_repo.create(**batch_data)
            
            # Create analyses
            analysis_repo = AnalysisRepository(session)
            analysis_ids = []
            
            for analysis_data in analyses_data:
                analysis_data['batch_id'] = batch.id
                analysis = analysis_repo.create(**analysis_data)
                analysis_ids.append(analysis.id)
            
            session.commit()
            
            return batch.id, analysis_ids
    
    async def _cleanup_temp_dataset(self, batch_id: int, analysis_ids: list[int]):
        """Cleanup temporary dataset"""
        with get_audit_db_session() as session:
            analysis_repo = AnalysisRepository(session)
            batch_repo = BatchRepository(session)
            
            # Delete analyses
            for analysis_id in analysis_ids:
                analysis_repo.delete(analysis_id)
            
            # Delete batch
            batch_repo.delete(batch_id)
            session.commit()
    
    def _get_memory_summary(self) -> Dict[str, Any]:
        """Get overall memory usage summary"""
        current_memory = self.metrics.get_memory_info()
        
        return {
            'current_rss_mb': current_memory['rss_mb'],
            'current_vms_mb': current_memory['vms_mb'],
            'target_max_mb': 100,  # Our target: <100MB for 10k analyses
            'within_target': current_memory['rss_mb'] < 100
        }