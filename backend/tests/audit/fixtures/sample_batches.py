"""
Sample batch and analysis data generators for audit testing
Creates realistic test datasets with various characteristics
"""
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

from app.models.batch import Batch, BatchStatus
from app.models.analysis import Analysis
from app.models.user import User, UserRole


class SampleDataGenerator:
    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducible tests"""
        random.seed(seed)
        self.isbn_counter = 1000000
        
    def generate_test_user(self, role: UserRole = UserRole.SOURCER) -> Dict[str, Any]:
        """Generate test user data"""
        return {
            'username': f'test_user_{random.randint(1000, 9999)}',
            'email': f'test{random.randint(1000, 9999)}@example.com',
            'role': role,
            'is_active': True
        }
    
    def generate_test_batch(self, 
                           status: BatchStatus = BatchStatus.COMPLETED,
                           total_items: Optional[int] = None) -> Dict[str, Any]:
        """Generate test batch data"""
        if total_items is None:
            total_items = random.randint(50, 200)
            
        processed_items = total_items if status == BatchStatus.COMPLETED else random.randint(0, total_items)
        
        created_at = datetime.now() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23)
        )
        
        return {
            'name': f'Audit Test Batch {random.randint(1000, 9999)}',
            'status': status,
            'total_items': total_items,
            'processed_items': processed_items,
            'error_count': random.randint(0, max(1, total_items // 20)),
            'created_at': created_at,
            'updated_at': created_at + timedelta(minutes=random.randint(1, 60))
        }
    
    def generate_test_analysis(self, 
                              batch_id: int,
                              quality_tier: str = 'mixed') -> Dict[str, Any]:
        """
        Generate test analysis data
        quality_tier: 'high_profit', 'high_velocity', 'balanced', 'low_quality', 'mixed'
        """
        isbn = f'978{self.isbn_counter:07d}'
        self.isbn_counter += 1
        
        # Base random values
        if quality_tier == 'high_profit':
            selling_price = Decimal(str(random.uniform(25, 100)))
            cost_price = Decimal(str(random.uniform(5, 20)))
            roi_percent = Decimal(str(random.uniform(40, 150)))
            velocity_score = Decimal(str(random.uniform(0.3, 0.7)))
            profit_score = Decimal(str(random.uniform(0.7, 1.0)))
            
        elif quality_tier == 'high_velocity':
            selling_price = Decimal(str(random.uniform(15, 50)))
            cost_price = Decimal(str(random.uniform(8, 25)))
            roi_percent = Decimal(str(random.uniform(15, 40)))
            velocity_score = Decimal(str(random.uniform(0.7, 1.0)))
            profit_score = Decimal(str(random.uniform(0.3, 0.7)))
            
        elif quality_tier == 'balanced':
            selling_price = Decimal(str(random.uniform(20, 60)))
            cost_price = Decimal(str(random.uniform(10, 30)))
            roi_percent = Decimal(str(random.uniform(25, 60)))
            velocity_score = Decimal(str(random.uniform(0.5, 0.8)))
            profit_score = Decimal(str(random.uniform(0.5, 0.8)))
            
        elif quality_tier == 'low_quality':
            selling_price = Decimal(str(random.uniform(10, 25)))
            cost_price = Decimal(str(random.uniform(8, 22)))
            roi_percent = Decimal(str(random.uniform(5, 25)))
            velocity_score = Decimal(str(random.uniform(0.1, 0.4)))
            profit_score = Decimal(str(random.uniform(0.1, 0.4)))
            
        else:  # mixed
            tier = random.choice(['high_profit', 'high_velocity', 'balanced', 'low_quality'])
            return self.generate_test_analysis(batch_id, tier)
        
        # Calculate derived values
        amazon_fees = selling_price * Decimal('0.15')  # Approximate 15% fees
        net_profit = selling_price - cost_price - amazon_fees
        
        return {
            'batch_id': batch_id,
            'isbn_or_asin': isbn,
            'book_title': f'Test Book {isbn[-6:]}',
            'selling_price': selling_price,
            'cost_price': cost_price,
            'amazon_fees': amazon_fees,
            'net_profit': net_profit,
            'roi_percent': roi_percent,
            'velocity_score': velocity_score,
            'profit_score': profit_score,
            'rank_bsr': random.randint(1000, 1000000),
            'raw_keepa_data': {'test': 'data'},  # Minimal keepa data
            'created_at': datetime.now()
        }
    
    def generate_batch_with_analyses(self, 
                                   analysis_count: int,
                                   quality_distribution: Optional[Dict[str, float]] = None) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generate a complete batch with analyses
        
        quality_distribution example: {
            'high_profit': 0.2,
            'high_velocity': 0.2, 
            'balanced': 0.3,
            'low_quality': 0.3
        }
        """
        if quality_distribution is None:
            quality_distribution = {
                'high_profit': 0.15,
                'high_velocity': 0.15,
                'balanced': 0.40,
                'low_quality': 0.30
            }
        
        # Generate batch
        batch_data = self.generate_test_batch(
            status=BatchStatus.COMPLETED,
            total_items=analysis_count
        )
        
        # Generate analyses with quality distribution
        analyses = []
        for _ in range(analysis_count):
            # Choose quality tier based on distribution
            tier = random.choices(
                list(quality_distribution.keys()),
                weights=list(quality_distribution.values())
            )[0]
            
            analysis = self.generate_test_analysis(
                batch_id=1,  # Will be updated after batch creation
                quality_tier=tier
            )
            analyses.append(analysis)
        
        return batch_data, analyses
    
    def create_performance_dataset(self, size: int) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Create dataset optimized for performance testing"""
        # For performance tests, use balanced distribution
        quality_dist = {
            'high_profit': 0.25,
            'high_velocity': 0.25,
            'balanced': 0.30,
            'low_quality': 0.20
        }
        
        return self.generate_batch_with_analyses(size, quality_dist)
    
    def create_filtering_dataset(self) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Create dataset with known filtering characteristics"""
        batch_data = self.generate_test_batch(total_items=100)
        analyses = []
        
        # Create specific analyses for filter testing
        # High ROI items (>40%)
        for _ in range(20):
            analysis = self.generate_test_analysis(1, 'high_profit')
            analysis['roi_percent'] = Decimal(str(random.uniform(40, 80)))
            analyses.append(analysis)
        
        # Low ROI items (<20%)
        for _ in range(30):
            analysis = self.generate_test_analysis(1, 'low_quality')
            analysis['roi_percent'] = Decimal(str(random.uniform(5, 19)))
            analyses.append(analysis)
        
        # Medium ROI items (20-40%)
        for _ in range(50):
            analysis = self.generate_test_analysis(1, 'balanced')
            analysis['roi_percent'] = Decimal(str(random.uniform(20, 39)))
            analyses.append(analysis)
        
        return batch_data, analyses
    
    def create_pagination_dataset(self, total_size: int = 10000) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Create large dataset for pagination testing"""
        return self.create_performance_dataset(total_size)
    
    def generate_isbn_list(self, count: int) -> List[str]:
        """Generate list of ISBN codes for testing"""
        isbns = []
        for _ in range(count):
            isbn = f'978{self.isbn_counter:07d}'
            self.isbn_counter += 1
            isbns.append(isbn)
        return isbns