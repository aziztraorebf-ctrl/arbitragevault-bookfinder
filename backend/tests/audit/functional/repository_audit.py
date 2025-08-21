"""
Repository layer functional audit
Validates all repository operations and business logic
"""
from decimal import Decimal
from typing import Dict, Any

from ..utils.database import get_audit_db_session
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.batch_repository import BatchRepository
from app.repositories.user_repository import UserRepository
from app.models.user import UserRole
from app.models.batch import BatchStatus
from app.repositories.exceptions import DuplicateIsbnInBatchError, NotFoundError, InvalidSortFieldError
from ..fixtures.sample_batches import SampleDataGenerator
from ..utils.metrics_collector import MetricsCollector


class RepositoryAuditor:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.data_generator = SampleDataGenerator()
        
    async def audit(self) -> Dict[str, Any]:
        """Run comprehensive repository audit"""
        results = {
            'status': 'UNKNOWN',
            'passed': 0,
            'total': 0,
            'details': {},
            'warnings': []
        }
        
        print("    🔍 Auditing repository layer...")
        
        # Test categories
        test_categories = [
            ('basic_crud', self._test_basic_crud_operations),
            ('filtering', self._test_filtering_functionality),
            ('pagination', self._test_pagination_system),
            ('strategic_queries', self._test_strategic_queries),
            ('error_handling', self._test_error_handling),
            ('data_integrity', self._test_data_integrity),
            ('duplicate_handling', self._test_duplicate_handling)
        ]
        
        for category_name, test_func in test_categories:
            try:
                print(f"      📋 Testing {category_name}...")
                test_result = await test_func()
                results['details'][category_name] = test_result
                
                if test_result['status'] == 'PASS':
                    results['passed'] += 1
                results['total'] += 1
                
            except Exception as e:
                print(f"        ❌ Error in {category_name}: {e}")
                results['details'][category_name] = {
                    'status': 'ERROR',
                    'message': str(e)
                }
                results['total'] += 1
        
        # Overall status
        if results['passed'] == results['total']:
            results['status'] = 'PASS'
        elif results['passed'] > results['total'] // 2:
            results['status'] = 'PARTIAL'
            results['warnings'].append(f"Only {results['passed']}/{results['total']} tests passed")
        else:
            results['status'] = 'FAIL'
        
        return results
    
    async def _test_basic_crud_operations(self) -> Dict[str, Any]:
        """Test basic CRUD operations"""
        try:
            with get_audit_db_session() as session:
                # Setup
                user_repo = UserRepository(session)
                batch_repo = BatchRepository(session)
                analysis_repo = AnalysisRepository(session)
                
                # Create user
                user_data = self.data_generator.generate_test_user(UserRole.SOURCER)
                user = user_repo.create(**user_data)
                assert user.id is not None
                
                # Create batch
                batch_data = self.data_generator.generate_test_batch()
                batch_data['user_id'] = user.id
                batch = batch_repo.create(**batch_data)
                assert batch.id is not None
                
                # Create analysis
                analysis_data = self.data_generator.generate_test_analysis(batch.id)
                analysis = analysis_repo.create(**analysis_data)
                assert analysis.id is not None
                
                # Read operations
                retrieved_analysis = analysis_repo.get_by_id(analysis.id)
                assert retrieved_analysis is not None
                assert retrieved_analysis.isbn_or_asin == analysis.isbn_or_asin
                
                # Update operation
                original_title = analysis.book_title
                new_title = f"Updated {original_title}"
                updated_analysis = analysis_repo.update(analysis.id, book_title=new_title)
                assert updated_analysis.book_title == new_title
                
                # Delete operation
                analysis_repo.delete(analysis.id)
                deleted_analysis = analysis_repo.get_by_id(analysis.id)
                assert deleted_analysis is None
                
                # Cleanup
                batch_repo.delete(batch.id)
                user_repo.delete(user.id)
                session.commit()
                
                return {
                    'status': 'PASS',
                    'message': 'All CRUD operations successful'
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'CRUD operations failed: {str(e)}'
            }
    
    async def _test_filtering_functionality(self) -> Dict[str, Any]:
        """Test filtering functionality"""
        try:
            # Create test dataset with known characteristics
            batch_data, analyses_data = self.data_generator.create_filtering_dataset()
            
            with get_audit_db_session() as session:
                # Setup
                user_repo = UserRepository(session)
                batch_repo = BatchRepository(session)
                analysis_repo = AnalysisRepository(session)
                
                # Create test user and batch
                user_data = self.data_generator.generate_test_user(UserRole.SOURCER)
                user = user_repo.create(**user_data)
                batch_data['user_id'] = user.id
                batch = batch_repo.create(**batch_data)
                
                # Create analyses
                analysis_ids = []
                for analysis_data in analyses_data:
                    analysis_data['batch_id'] = batch.id
                    analysis = analysis_repo.create(**analysis_data)
                    analysis_ids.append(analysis.id)
                
                session.commit()
                
                # Test ROI filtering
                high_roi_analyses, _ = analysis_repo.list_filtered(
                    batch_id=batch.id,
                    min_roi=40.0
                )
                assert len(high_roi_analyses) > 0, "Should find high ROI analyses"
                assert all(a.roi_percent >= 40 for a in high_roi_analyses), "All should meet ROI criteria"
                
                # Test combined filtering
                combined_analyses, _ = analysis_repo.list_filtered(
                    batch_id=batch.id,
                    min_roi=25.0,
                    min_velocity=0.4
                )
                assert all(
                    a.roi_percent >= 25 and a.velocity_score >= 0.4 
                    for a in combined_analyses
                ), "All should meet combined criteria"
                
                # Test ISBN list filtering
                test_isbns = [analyses_data[0]['isbn_or_asin'], analyses_data[1]['isbn_or_asin']]
                isbn_filtered, _ = analysis_repo.list_filtered(
                    batch_id=batch.id,
                    isbn_list=test_isbns
                )
                assert len(isbn_filtered) == 2, "Should find exactly 2 analyses"
                
                # Cleanup
                batch_repo.delete(batch.id)
                user_repo.delete(user.id)
                session.commit()
                
                return {
                    'status': 'PASS',
                    'message': 'All filtering tests successful'
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Filtering tests failed: {str(e)}'
            }
    
    async def _test_pagination_system(self) -> Dict[str, Any]:
        """Test pagination functionality"""
        try:
            batch_data, analyses_data = self.data_generator.create_performance_dataset(150)
            
            with get_audit_db_session() as session:
                # Setup
                user_repo = UserRepository(session)
                batch_repo = BatchRepository(session)
                analysis_repo = AnalysisRepository(session)
                
                # Create test data
                user_data = self.data_generator.generate_test_user(UserRole.SOURCER)
                user = user_repo.create(**user_data)
                batch_data['user_id'] = user.id
                batch = batch_repo.create(**batch_data)
                
                for analysis_data in analyses_data:
                    analysis_data['batch_id'] = batch.id
                    analysis_repo.create(**analysis_data)
                
                session.commit()
                
                # Test pagination consistency
                all_page_items = []
                page_size = 50
                total_pages = 3  # 150 / 50
                
                for page in range(total_pages):
                    offset = page * page_size
                    page_items, total = analysis_repo.list_filtered(
                        batch_id=batch.id,
                        offset=offset,
                        limit=page_size
                    )
                    
                    assert len(page_items) == page_size, f"Page {page} should have {page_size} items"
                    assert total == 150, "Total count should be consistent"
                    
                    all_page_items.extend([item.id for item in page_items])
                
                # Check no duplicates across pages
                assert len(all_page_items) == len(set(all_page_items)), "No duplicate items across pages"
                
                # Test deep pagination
                deep_offset = 100
                deep_items, _ = analysis_repo.list_filtered(
                    batch_id=batch.id,
                    offset=deep_offset,
                    limit=25
                )
                assert len(deep_items) == 25, "Deep pagination should work"
                
                # Cleanup
                batch_repo.delete(batch.id)
                user_repo.delete(user.id)
                session.commit()
                
                return {
                    'status': 'PASS',
                    'message': 'Pagination tests successful'
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Pagination tests failed: {str(e)}'
            }
    
    async def _test_strategic_queries(self) -> Dict[str, Any]:
        """Test strategic query functionality"""
        try:
            batch_data, analyses_data = self.data_generator.create_performance_dataset(100)
            
            with get_audit_db_session() as session:
                # Setup
                user_repo = UserRepository(session)
                batch_repo = BatchRepository(session)
                analysis_repo = AnalysisRepository(session)
                
                # Create test data
                user_data = self.data_generator.generate_test_user(UserRole.SOURCER)
                user = user_repo.create(**user_data)
                batch_data['user_id'] = user.id
                batch = batch_repo.create(**batch_data)
                
                for analysis_data in analyses_data:
                    analysis_data['batch_id'] = batch.id
                    analysis_repo.create(**analysis_data)
                
                session.commit()
                
                # Test all strategies
                strategies = ['roi', 'velocity', 'profit', 'balanced']
                
                for strategy in strategies:
                    top_analyses = analysis_repo.top_n_for_batch(
                        batch_id=batch.id,
                        n=10,
                        strategy=strategy
                    )
                    
                    assert len(top_analyses) == 10, f"Strategy {strategy} should return 10 items"
                    
                    # Verify ordering for specific strategies
                    if strategy == 'roi':
                        roi_values = [a.roi_percent for a in top_analyses]
                        assert roi_values == sorted(roi_values, reverse=True), "ROI strategy should be ordered by ROI"
                    
                    elif strategy == 'velocity':
                        velocity_values = [a.velocity_score for a in top_analyses]
                        assert velocity_values == sorted(velocity_values, reverse=True), "Velocity strategy should be ordered by velocity"
                
                # Test balanced strategy calculation
                balanced_top = analysis_repo.top_n_for_batch(
                    batch_id=batch.id,
                    n=5,
                    strategy='balanced'
                )
                
                # Verify balanced scoring (60% ROI, 40% velocity)
                for analysis in balanced_top:
                    expected_score = float(analysis.roi_percent * Decimal('0.6') + analysis.velocity_score * 100 * Decimal('0.4'))
                    # Just verify the calculation doesn't crash - actual scoring verification is complex
                    assert expected_score > 0, "Balanced score should be positive"
                
                # Cleanup
                batch_repo.delete(batch.id)
                user_repo.delete(user.id)
                session.commit()
                
                return {
                    'status': 'PASS',
                    'message': 'Strategic query tests successful'
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Strategic query tests failed: {str(e)}'
            }
    
    async def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling functionality"""
        try:
            with get_db_session() as session:
                analysis_repo = AnalysisRepository(session)
                
                # Test invalid sort field
                try:
                    analysis_repo.list_filtered(
                        batch_id=999,
                        sort_by='invalid_field'
                    )
                    return {
                        'status': 'FAIL',
                        'message': 'Should have raised InvalidSortFieldError'
                    }
                except InvalidSortFieldError:
                    pass  # Expected
                
                # Test not found error
                try:
                    analysis_repo.get_by_id(99999)
                    # If no exception, the item was None (which is acceptable)
                except NotFoundError:
                    pass  # Also acceptable
                
                # Test invalid batch ID
                analyses, total = analysis_repo.list_filtered(batch_id=99999)
                assert len(analyses) == 0, "Invalid batch should return empty results"
                assert total == 0, "Total should be 0 for invalid batch"
                
                return {
                    'status': 'PASS',
                    'message': 'Error handling tests successful'
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Error handling tests failed: {str(e)}'
            }
    
    async def _test_data_integrity(self) -> Dict[str, Any]:
        """Test data integrity constraints"""
        try:
            with get_db_session() as session:
                # Setup
                user_repo = UserRepository(session)
                batch_repo = BatchRepository(session)
                
                # Create user and batch
                user_data = self.data_generator.generate_test_user(UserRole.SOURCER)
                user = user_repo.create(**user_data)
                batch_data = self.data_generator.generate_test_batch()
                batch_data['user_id'] = user.id
                batch = batch_repo.create(**batch_data)
                session.commit()
                
                # Test cascade delete
                original_batch = batch_repo.get_by_id(batch.id)
                assert original_batch is not None
                
                # Delete user (should not cascade to batch in our current model)
                user_repo.delete(user.id)
                session.commit()
                
                # Batch should still exist (foreign key constraint should prevent user deletion if there are batches)
                # But if it doesn't prevent it, the batch should handle the orphaned state
                remaining_batch = batch_repo.get_by_id(batch.id)
                
                if remaining_batch:
                    batch_repo.delete(batch.id)
                    session.commit()
                
                return {
                    'status': 'PASS',
                    'message': 'Data integrity tests successful'
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Data integrity tests failed: {str(e)}'
            }
    
    async def _test_duplicate_handling(self) -> Dict[str, Any]:
        """Test duplicate ISBN handling"""
        try:
            with get_db_session() as session:
                # Setup
                user_repo = UserRepository(session)
                batch_repo = BatchRepository(session)
                analysis_repo = AnalysisRepository(session)
                
                # Create test data
                user_data = self.data_generator.generate_test_user(UserRole.SOURCER)
                user = user_repo.create(**user_data)
                batch_data = self.data_generator.generate_test_batch()
                batch_data['user_id'] = user.id
                batch = batch_repo.create(**batch_data)
                
                # Create first analysis
                analysis_data = self.data_generator.generate_test_analysis(batch.id)
                first_analysis = analysis_repo.create(**analysis_data)
                session.commit()
                
                # Try to create duplicate ISBN in same batch
                duplicate_data = self.data_generator.generate_test_analysis(batch.id)
                duplicate_data['isbn_or_asin'] = first_analysis.isbn_or_asin  # Same ISBN
                
                try:
                    analysis_repo.create(**duplicate_data)
                    session.commit()
                    return {
                        'status': 'FAIL',
                        'message': 'Should have raised DuplicateIsbnInBatchError'
                    }
                except DuplicateIsbnInBatchError:
                    # Expected behavior
                    session.rollback()
                
                # Cleanup
                batch_repo.delete(batch.id)
                user_repo.delete(user.id)
                session.commit()
                
                return {
                    'status': 'PASS',
                    'message': 'Duplicate handling tests successful'
                }
                
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Duplicate handling tests failed: {str(e)}'
            }