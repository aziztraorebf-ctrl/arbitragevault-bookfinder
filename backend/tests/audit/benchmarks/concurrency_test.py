"""
Concurrency testing suite with both threading and async approaches
Tests concurrent load performance with multiple simulated users
"""
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List
import aiohttp

from ..utils.database import get_audit_db_session
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.batch_repository import BatchRepository
from app.repositories.user_repository import UserRepository
from app.models.user import UserRole
from ..fixtures.sample_batches import SampleDataGenerator
from ..utils.metrics_collector import MetricsCollector


class ConcurrencyTester:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.data_generator = SampleDataGenerator()
        self.api_base_url = "http://localhost:8000"  # FastAPI server URL
        
    async def test_concurrent_load(self, concurrent_users: int) -> Dict[str, Any]:
        """Test concurrent load with specified number of users"""
        results = {}
        
        print(f"    👥 Setting up {concurrent_users} concurrent users test...")
        
        # Setup test data
        batch_id, analysis_ids = await self._setup_concurrent_test_data()
        
        try:
            # Test both approaches
            results['threading_approach'] = await self._test_threading_concurrency(
                batch_id, concurrent_users
            )
            
            results['async_approach'] = await self._test_async_concurrency(
                batch_id, concurrent_users
            )
            
            # Compare approaches
            results['comparison'] = self._compare_approaches(
                results['threading_approach'], 
                results['async_approach']
            )
            
            return results
            
        finally:
            # Cleanup
            await self._cleanup_concurrent_test_data(batch_id, analysis_ids)
    
    async def _setup_concurrent_test_data(self) -> tuple[int, list[int]]:
        """Setup test data for concurrency testing"""
        with get_audit_db_session() as session:
            # Create test user
            user_repo = UserRepository(session)
            user_data = self.data_generator.generate_test_user(UserRole.SOURCER)
            user = user_repo.create(**user_data)
            
            # Create test batch with moderate size for concurrency testing
            batch_repo = BatchRepository(session)
            batch_data, analyses_data = self.data_generator.create_performance_dataset(1000)
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
            
            print(f"    ✅ Created concurrency test dataset: batch {batch.id}")
            return batch.id, analysis_ids
    
    async def _cleanup_concurrent_test_data(self, batch_id: int, analysis_ids: list[int]):
        """Cleanup concurrency test data"""
        with get_audit_db_session() as session:
            analysis_repo = AnalysisRepository(session)
            batch_repo = BatchRepository(session)
            
            # Delete analyses
            for analysis_id in analysis_ids:
                analysis_repo.delete(analysis_id)
            
            # Delete batch
            batch_repo.delete(batch_id)
            session.commit()
    
    async def _test_threading_concurrency(self, batch_id: int, concurrent_users: int) -> Dict[str, Any]:
        """Test concurrency using threading approach"""
        print(f"      🧵 Testing threading concurrency ({concurrent_users} threads)...")
        
        def worker_function():
            """Function executed by each thread"""
            start_time = time.perf_counter()
            
            try:
                # Simulate user operations
                with get_audit_db_session() as session:
                    repo = AnalysisRepository(session)
                    
                    # Operation 1: List analyses
                    analyses, _ = repo.list_filtered(
                        batch_id=batch_id,
                        offset=0,
                        limit=50
                    )
                    
                    # Operation 2: Get top analyses
                    top_analyses = repo.top_n_for_batch(
                        batch_id=batch_id,
                        n=10,
                        strategy='roi'
                    )
                    
                    return len(analyses) + len(top_analyses)
                    
            except Exception as e:
                print(f"        ❌ Thread error: {e}")
                return 0
            finally:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                self.metrics.record_timing('threading_worker', duration_ms)
        
        # Run threading test
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(worker_function) for _ in range(concurrent_users)]
            
            # Wait for all threads to complete
            results = [future.result() for future in futures]
        
        end_time = time.perf_counter()
        total_duration_ms = (end_time - start_time) * 1000
        
        # Calculate metrics
        worker_stats = self.metrics.calculate_percentiles('threading_worker')
        
        return {
            'total_duration_ms': total_duration_ms,
            'successful_operations': sum(1 for r in results if r > 0),
            'failed_operations': sum(1 for r in results if r == 0),
            'worker_stats': worker_stats,
            'approach': 'threading'
        }
    
    async def _test_async_concurrency(self, batch_id: int, concurrent_users: int) -> Dict[str, Any]:
        """Test concurrency using async/aiohttp approach"""
        print(f"      🌐 Testing async HTTP concurrency ({concurrent_users} clients)...")
        
        # First check if API server is running
        api_available = await self._check_api_availability()
        if not api_available:
            return {
                'status': 'SKIPPED',
                'reason': 'FastAPI server not available',
                'approach': 'async_http'
            }
        
        async def async_worker(session: aiohttp.ClientSession):
            """Async worker function using HTTP API"""
            start_time = time.perf_counter()
            
            try:
                # Operation 1: List analyses via API
                async with session.get(
                    f"{self.api_base_url}/api/v1/analyses",
                    params={
                        'batch_id': batch_id,
                        'offset': 0,
                        'limit': 50
                    }
                ) as response:
                    if response.status == 200:
                        data1 = await response.json()
                    else:
                        return 0
                
                # Operation 2: Get top analyses via API  
                async with session.get(
                    f"{self.api_base_url}/api/v1/analyses/top",
                    params={
                        'batch_id': batch_id,
                        'n': 10,
                        'strategy': 'roi'
                    }
                ) as response:
                    if response.status == 200:
                        data2 = await response.json()
                    else:
                        return 0
                
                return len(data1.get('items', [])) + len(data2.get('analyses', []))
                
            except Exception as e:
                print(f"        ❌ Async worker error: {e}")
                return 0
            finally:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                self.metrics.record_timing('async_worker', duration_ms)
        
        # Run async test
        start_time = time.perf_counter()
        
        async with aiohttp.ClientSession() as session:
            tasks = [async_worker(session) for _ in range(concurrent_users)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        total_duration_ms = (end_time - start_time) * 1000
        
        # Process results
        successful_results = [r for r in results if isinstance(r, int) and r > 0]
        failed_results = [r for r in results if not isinstance(r, int) or r == 0]
        
        # Calculate metrics
        worker_stats = self.metrics.calculate_percentiles('async_worker')
        
        return {
            'total_duration_ms': total_duration_ms,
            'successful_operations': len(successful_results),
            'failed_operations': len(failed_results),
            'worker_stats': worker_stats,
            'approach': 'async_http'
        }
    
    async def _check_api_availability(self) -> bool:
        """Check if FastAPI server is running and accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/health",
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    def _compare_approaches(self, threading_result: Dict[str, Any], async_result: Dict[str, Any]) -> Dict[str, Any]:
        """Compare threading vs async approaches"""
        comparison = {
            'both_available': True,
            'recommendation': None,
            'analysis': {}
        }
        
        # Check if async was skipped
        if async_result.get('status') == 'SKIPPED':
            comparison['both_available'] = False
            comparison['recommendation'] = 'Threading (async HTTP not available)'
            comparison['analysis'] = {
                'reason': 'FastAPI server not running for HTTP tests'
            }
            return comparison
        
        # Compare performance
        threading_p95 = threading_result.get('worker_stats', {}).get('p95_ms', 0)
        async_p95 = async_result.get('worker_stats', {}).get('p95_ms', 0)
        
        # Compare success rates
        threading_success_rate = (
            threading_result.get('successful_operations', 0) / 
            (threading_result.get('successful_operations', 0) + threading_result.get('failed_operations', 1))
        )
        
        async_success_rate = (
            async_result.get('successful_operations', 0) / 
            (async_result.get('successful_operations', 0) + async_result.get('failed_operations', 1))
        )
        
        # Make recommendation
        if threading_success_rate > async_success_rate:
            recommendation = 'Threading (better reliability)'
        elif async_p95 < threading_p95:
            recommendation = 'Async HTTP (better performance)'
        else:
            recommendation = 'Threading (similar performance, less complexity)'
        
        comparison.update({
            'recommendation': recommendation,
            'analysis': {
                'threading_p95_ms': threading_p95,
                'async_p95_ms': async_p95,
                'threading_success_rate': threading_success_rate,
                'async_success_rate': async_success_rate,
                'performance_difference_ms': abs(threading_p95 - async_p95)
            }
        })
        
        return comparison