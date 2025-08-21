"""
Database performance analyzer with EXPLAIN ANALYZE
Verifies index usage and query optimization
"""
import json
from typing import Dict, Any, List
from sqlalchemy import create_engine, text

from app.core.settings import Settings
from ..fixtures.sample_batches import SampleDataGenerator
from ..utils.metrics_collector import MetricsCollector


class DatabaseAnalyzer:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.settings = Settings()
        self.data_generator = SampleDataGenerator()
        
    async def analyze(self) -> Dict[str, Any]:
        """Run comprehensive database analysis"""
        results = {}
        
        print("    🔍 Analyzing database performance...")
        
        # Setup test data for analysis
        batch_id = await self._setup_analysis_data()
        
        try:
            # Analyze critical queries
            results['index_usage'] = await self._analyze_index_usage(batch_id)
            results['query_performance'] = await self._analyze_query_performance(batch_id)
            results['database_stats'] = await self._get_database_statistics()
            
            return results
            
        finally:
            # Cleanup
            await self._cleanup_analysis_data(batch_id)
    
    async def _setup_analysis_data(self) -> int:
        """Setup data for database analysis"""
        from app.core.database import get_db_session
        from app.repositories.batch_repository import BatchRepository
        from app.repositories.user_repository import UserRepository
        from app.repositories.analysis_repository import AnalysisRepository
        from app.models.user import UserRole
        
        with get_db_session() as session:
            # Create test user
            user_repo = UserRepository(session)
            user_data = self.data_generator.generate_test_user(UserRole.SOURCER)
            user = user_repo.create(**user_data)
            
            # Create test batch with moderate size
            batch_repo = BatchRepository(session)
            batch_data, analyses_data = self.data_generator.create_performance_dataset(2000)
            batch_data['user_id'] = user.id
            batch = batch_repo.create(**batch_data)
            
            # Create analyses
            analysis_repo = AnalysisRepository(session)
            for analysis_data in analyses_data:
                analysis_data['batch_id'] = batch.id
                analysis_repo.create(**analysis_data)
            
            session.commit()
            print(f"    ✅ Created analysis dataset: batch {batch.id}")
            
            return batch.id
    
    async def _cleanup_analysis_data(self, batch_id: int):
        """Cleanup analysis data"""
        from app.core.database import get_db_session
        from app.repositories.batch_repository import BatchRepository
        
        with get_db_session() as session:
            batch_repo = BatchRepository(session)
            batch_repo.delete(batch_id)
            session.commit()
    
    async def _analyze_index_usage(self, batch_id: int) -> Dict[str, Any]:
        """Analyze index usage for critical queries"""
        results = {}
        
        # Critical queries to analyze
        queries = {
            'basic_batch_filter': f"""
                SELECT * FROM analyses 
                WHERE batch_id = {batch_id} 
                ORDER BY id 
                LIMIT 100
            """,
            
            'roi_filter': f"""
                SELECT * FROM analyses 
                WHERE batch_id = {batch_id} 
                  AND roi_percent >= 30.0 
                  AND roi_percent <= 80.0
                ORDER BY roi_percent DESC 
                LIMIT 100
            """,
            
            'velocity_filter': f"""
                SELECT * FROM analyses 
                WHERE batch_id = {batch_id} 
                  AND velocity_score >= 0.5
                ORDER BY velocity_score DESC 
                LIMIT 100
            """,
            
            'combined_filters': f"""
                SELECT * FROM analyses 
                WHERE batch_id = {batch_id} 
                  AND roi_percent >= 25.0 
                  AND velocity_score >= 0.4 
                  AND net_profit >= 5.0
                ORDER BY (roi_percent * 0.6 + velocity_score * 100 * 0.4) DESC 
                LIMIT 100
            """,
            
            'isbn_lookup': f"""
                SELECT * FROM analyses 
                WHERE batch_id = {batch_id} 
                  AND isbn_or_asin = '9781000001'
            """
        }
        
        engine = create_engine(self.settings.database_url)
        
        for query_name, query in queries.items():
            print(f"      📊 Analyzing: {query_name}")
            
            try:
                with engine.connect() as conn:
                    # Run EXPLAIN ANALYZE
                    explain_result = conn.execute(
                        text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
                    )
                    
                    explain_data = explain_result.scalar()
                    plan = explain_data[0]['Plan']
                    
                    # Analyze the query plan
                    analysis = self._analyze_query_plan(plan)
                    results[query_name] = analysis
                    
            except Exception as e:
                print(f"        ❌ Error analyzing {query_name}: {e}")
                results[query_name] = {
                    'status': 'ERROR',
                    'error': str(e),
                    'index_used': False,
                    'seq_scan_detected': True
                }
        
        return results
    
    def _analyze_query_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a PostgreSQL query execution plan"""
        analysis = {
            'execution_time_ms': plan.get('Actual Total Time', 0),
            'rows_processed': plan.get('Actual Rows', 0),
            'index_used': False,
            'seq_scan_detected': False,
            'buffer_hits': 0,
            'buffer_reads': 0,
            'node_type': plan.get('Node Type', ''),
            'index_name': None,
            'cost': plan.get('Total Cost', 0),
            'warnings': []
        }
        
        # Check for index usage
        if 'Index' in plan.get('Node Type', ''):
            analysis['index_used'] = True
            analysis['index_name'] = plan.get('Index Name')
        
        # Check for sequential scans
        if plan.get('Node Type') == 'Seq Scan':
            analysis['seq_scan_detected'] = True
            analysis['warnings'].append('Sequential scan detected - consider adding index')
        
        # Analyze buffer usage
        if 'Shared Hit Blocks' in plan:
            analysis['buffer_hits'] = plan['Shared Hit Blocks']
        if 'Shared Read Blocks' in plan:
            analysis['buffer_reads'] = plan['Shared Read Blocks']
        
        # Check performance warnings
        if analysis['execution_time_ms'] > 100:
            analysis['warnings'].append(f"Slow query: {analysis['execution_time_ms']:.1f}ms")
        
        if analysis['buffer_reads'] > analysis['buffer_hits']:
            analysis['warnings'].append("More disk reads than cache hits")
        
        # Recursively analyze child plans
        if 'Plans' in plan:
            child_analyses = []
            for child_plan in plan['Plans']:
                child_analysis = self._analyze_query_plan(child_plan)
                child_analyses.append(child_analysis)
                
                # Inherit some properties from children
                if child_analysis['index_used']:
                    analysis['index_used'] = True
                if child_analysis['seq_scan_detected']:
                    analysis['seq_scan_detected'] = True
            
            analysis['child_plans'] = child_analyses
        
        return analysis
    
    async def _analyze_query_performance(self, batch_id: int) -> Dict[str, Any]:
        """Analyze query performance metrics"""
        results = {}
        
        engine = create_engine(self.settings.database_url)
        
        # Test key operations with timing
        operations = {
            'count_batch_analyses': f"SELECT COUNT(*) FROM analyses WHERE batch_id = {batch_id}",
            'avg_roi_calculation': f"SELECT AVG(roi_percent) FROM analyses WHERE batch_id = {batch_id}",
            'top_10_roi': f"""
                SELECT * FROM analyses 
                WHERE batch_id = {batch_id} 
                ORDER BY roi_percent DESC 
                LIMIT 10
            """,
            'top_10_balanced': f"""
                SELECT *, (roi_percent * 0.6 + velocity_score * 100 * 0.4) as balanced_score
                FROM analyses 
                WHERE batch_id = {batch_id} 
                ORDER BY balanced_score DESC 
                LIMIT 10
            """
        }
        
        for op_name, query in operations.items():
            print(f"      ⏱️  Timing: {op_name}")
            
            try:
                with engine.connect() as conn:
                    # Time the query execution
                    import time
                    start_time = time.perf_counter()
                    
                    result = conn.execute(text(query))
                    rows = result.fetchall()
                    
                    end_time = time.perf_counter()
                    execution_time_ms = (end_time - start_time) * 1000
                    
                    results[op_name] = {
                        'execution_time_ms': execution_time_ms,
                        'rows_returned': len(rows),
                        'status': 'SUCCESS'
                    }
                    
            except Exception as e:
                results[op_name] = {
                    'execution_time_ms': 0,
                    'rows_returned': 0,
                    'status': 'ERROR',
                    'error': str(e)
                }
        
        return results
    
    async def _get_database_statistics(self) -> Dict[str, Any]:
        """Get general database statistics"""
        stats = {}
        
        engine = create_engine(self.settings.database_url)
        
        try:
            with engine.connect() as conn:
                # Database version
                version_result = conn.execute(text("SELECT version()"))
                stats['postgresql_version'] = version_result.scalar()
                
                # Cache hit ratio
                cache_hit_query = text("""
                    SELECT 
                        round(
                            (sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read))) * 100, 
                            2
                        ) as cache_hit_ratio
                    FROM pg_statio_user_tables
                """)
                cache_result = conn.execute(cache_hit_query)
                cache_ratio = cache_result.scalar()
                stats['cache_hit_ratio_percent'] = float(cache_ratio) if cache_ratio else 0
                
                # Index usage statistics
                index_usage_query = text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE schemaname = 'public'
                    ORDER BY idx_scan DESC
                """)
                index_result = conn.execute(index_usage_query)
                index_stats = [dict(row._mapping) for row in index_result]
                stats['index_usage'] = index_stats
                
                # Table statistics
                table_stats_query = text("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'public'
                """)
                table_result = conn.execute(table_stats_query)
                table_stats = [dict(row._mapping) for row in table_result]
                stats['table_statistics'] = table_stats
                
                # Connection information
                conn_query = text("SELECT count(*) FROM pg_stat_activity")
                conn_result = conn.execute(conn_query)
                stats['active_connections'] = conn_result.scalar()
                
        except Exception as e:
            print(f"      ⚠️  Could not gather database statistics: {e}")
            stats['error'] = str(e)
        
        return stats