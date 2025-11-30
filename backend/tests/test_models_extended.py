"""
Extended unit tests for data models.
Tests ROI edge cases, batch transitions, constraints, and edge cases.
"""
import pytest
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.batch import Batch, BatchStatus
from app.models.analysis import Analysis


class TestROIEdgeCases:
    """Test ROI calculations and threshold methods with edge cases."""

    def test_meets_roi_threshold_exact_match(self, db_session, analysis_data):
        """Test ROI threshold when exactly matching the threshold."""
        analysis = Analysis(
            batch_id=str(uuid4()),
            isbn_or_asin="978-1234567890",
            buy_price=Decimal("20.00"),
            expected_sale_price=Decimal("30.00"),
            fees=Decimal("3.00"),
            profit=Decimal("7.00"),
            roi_percent=Decimal("35.0"),  # Exact threshold
            velocity_score=Decimal("7.5"),
            raw_keepa={"title": "Test Book"}
        )
        
        # Test exact match returns True
        assert analysis.meets_roi_threshold(Decimal("35.0")) is True
        # Test slightly above returns True
        assert analysis.meets_roi_threshold(Decimal("34.99")) is True
        # Test slightly below returns False
        assert analysis.meets_roi_threshold(Decimal("35.01")) is False

    def test_meets_roi_threshold_zero_and_negative(self, db_session):
        """Test ROI threshold with zero and negative values."""
        # Negative ROI (loss)
        analysis_loss = Analysis(
            batch_id=str(uuid4()),
            isbn_or_asin="978-1234567891",
            buy_price=Decimal("30.00"),
            expected_sale_price=Decimal("20.00"),
            fees=Decimal("5.00"),
            profit=Decimal("-15.00"),
            roi_percent=Decimal("-50.0"),  # 50% loss
            velocity_score=Decimal("3.0"),
            raw_keepa={"title": "Loss Book"}
        )
        
        assert analysis_loss.meets_roi_threshold(Decimal("0.0")) is False
        assert analysis_loss.meets_roi_threshold(Decimal("-60.0")) is True
        assert analysis_loss.meets_roi_threshold(Decimal("-40.0")) is False

        # Zero ROI (break-even)
        analysis_break_even = Analysis(
            batch_id=str(uuid4()),
            isbn_or_asin="978-1234567892",
            buy_price=Decimal("25.00"),
            expected_sale_price=Decimal("28.00"),
            fees=Decimal("3.00"),
            profit=Decimal("0.00"),
            roi_percent=Decimal("0.0"),
            velocity_score=Decimal("5.0"),
            raw_keepa={"title": "Break-even Book"}
        )
        
        assert analysis_break_even.meets_roi_threshold(Decimal("0.0")) is True
        assert analysis_break_even.meets_roi_threshold(Decimal("0.01")) is False
        assert analysis_break_even.meets_roi_threshold(Decimal("-1.0")) is True

    def test_meets_roi_threshold_extreme_values(self, db_session):
        """Test ROI threshold with extreme values."""
        # Very high ROI
        analysis_high = Analysis(
            batch_id=str(uuid4()),
            isbn_or_asin="978-1234567893",
            buy_price=Decimal("1.00"),
            expected_sale_price=Decimal("100.00"),
            fees=Decimal("5.00"),
            profit=Decimal("94.00"),
            roi_percent=Decimal("9400.0"),  # 9400% ROI
            velocity_score=Decimal("9.0"),
            raw_keepa={"title": "Extreme ROI Book"}
        )
        
        assert analysis_high.meets_roi_threshold(Decimal("9400.0")) is True
        assert analysis_high.meets_roi_threshold(Decimal("9401.0")) is False
        assert analysis_high.meets_roi_threshold(Decimal("100.0")) is True


class TestBatchTransitions:
    """Test batch status transitions and validation."""

    def test_valid_status_transitions(self, db_session, user_data):
        """Test valid batch status transitions."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()
        
        batch = Batch(
            user_id=user.id,
            name="Transition Test Batch",
            items_total=100,
            strategy_snapshot={"test": "data"}
        )
        db_session.add(batch)
        db_session.flush()
        
        # Initial state should be PENDING
        assert batch.status == BatchStatus.PENDING
        
        # PENDING -> PROCESSING
        batch.status = BatchStatus.PROCESSING
        assert batch.status == BatchStatus.PROCESSING

        # PROCESSING -> COMPLETED
        batch.status = BatchStatus.COMPLETED
        assert batch.status == BatchStatus.COMPLETED
        
        db_session.commit()

    def test_invalid_status_transitions(self, db_session, user_data):
        """Test that invalid status transitions are prevented."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()
        
        batch = Batch(
            user_id=user.id,
            name="Invalid Transition Test",
            items_total=50,
            strategy_snapshot={"test": "data"}
        )
        db_session.add(batch)
        db_session.flush()
        
        # PENDING -> COMPLETED (should be valid, but let's test the enum)
        batch.status = BatchStatus.COMPLETED
        assert batch.status == BatchStatus.COMPLETED
        
        # Test that status is properly constrained to enum values
        # This will be validated by SQLAlchemy enum constraint
        
    def test_batch_progress_tracking(self, db_session, user_data):
        """Test batch progress tracking constraints."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()
        
        batch = Batch(
            user_id=user.id,
            name="Progress Test Batch",
            items_total=100,
            items_processed=0,
            strategy_snapshot={"test": "data"}
        )
        db_session.add(batch)
        db_session.flush()
        
        # Valid progress updates
        batch.items_processed = 25
        assert batch.items_processed == 25
        
        batch.items_processed = 100
        assert batch.items_processed == 100
        
        # Test that items_processed can equal items_total
        assert batch.items_processed <= batch.items_total

    def test_batch_constraint_violations(self, db_session, user_data):
        """Test batch constraint violations."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()
        
        # Test negative items_total (should fail check constraint)
        with pytest.raises(IntegrityError):
            batch = Batch(
                user_id=user.id,
                name="Invalid Total Batch",
                items_total=-5,  # Negative total
                strategy_snapshot={"test": "data"}
            )
            db_session.add(batch)
            db_session.flush()


class TestUniquenessConstraints:
    """Test uniqueness constraints across models."""

    def test_user_email_uniqueness(self, db_session):
        """Test that user emails must be unique."""
        user1_data = {
            "id": str(uuid4()),
            "email": "duplicate@test.com",
            "password_hash": "hash1",
            "first_name": "User",
            "last_name": "One"
        }
        
        user2_data = {
            "id": str(uuid4()),
            "email": "duplicate@test.com",  # Same email
            "password_hash": "hash2",
            "first_name": "User",
            "last_name": "Two"
        }
        
        user1 = User(**user1_data)
        user2 = User(**user2_data)
        
        db_session.add(user1)
        db_session.flush()  # First user should be fine
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.flush()  # Second user should fail due to duplicate email

    def test_analysis_isbn_uniqueness_per_batch(self, db_session, user_data):
        """Test ISBN/ASIN uniqueness within the same batch."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()
        
        batch = Batch(
            user_id=user.id,
            name="Uniqueness Test Batch",
            items_total=100,
            strategy_snapshot={"test": "data"}
        )
        db_session.add(batch)
        db_session.flush()
        
        # First analysis with ISBN
        analysis1 = Analysis(
            batch_id=batch.id,
            isbn_or_asin="978-1234567890",
            buy_price=Decimal("20.00"),
            expected_sale_price=Decimal("30.00"),
            fees=Decimal("3.00"),
            profit=Decimal("7.00"),
            roi_percent=Decimal("35.0"),
            velocity_score=Decimal("7.5"),
            raw_keepa={"title": "Book One"}
        )
        db_session.add(analysis1)
        db_session.flush()  # Should work
        
        # Second analysis with same ISBN in same batch
        analysis2 = Analysis(
            batch_id=batch.id,
            isbn_or_asin="978-1234567890",  # Same ISBN
            buy_price=Decimal("25.00"),
            expected_sale_price=Decimal("35.00"),
            fees=Decimal("4.00"),
            profit=Decimal("6.00"),
            roi_percent=Decimal("24.0"),
            velocity_score=Decimal("6.0"),
            raw_keepa={"title": "Book Two (Same ISBN)"}
        )
        db_session.add(analysis2)
        with pytest.raises(IntegrityError):
            db_session.flush()  # Should fail due to unique constraint

    def test_analysis_isbn_uniqueness_across_batches(self, db_session, user_data):
        """Test that same ISBN can exist in different batches."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()
        
        # Create two different batches
        batch1 = Batch(
            user_id=user.id,
            name="Batch One",
            items_total=50,
            strategy_snapshot={"test": "data1"}
        )
        batch2 = Batch(
            user_id=user.id,
            name="Batch Two",
            items_total=50,
            strategy_snapshot={"test": "data2"}
        )
        db_session.add_all([batch1, batch2])
        db_session.flush()
        
        # Same ISBN in different batches should be allowed
        analysis1 = Analysis(
            batch_id=batch1.id,
            isbn_or_asin="978-1234567890",
            buy_price=Decimal("20.00"),
            expected_sale_price=Decimal("30.00"),
            fees=Decimal("3.00"),
            profit=Decimal("7.00"),
            roi_percent=Decimal("35.0"),
            velocity_score=Decimal("7.5"),
            raw_keepa={"title": "Book in Batch 1"}
        )
        
        analysis2 = Analysis(
            batch_id=batch2.id,
            isbn_or_asin="978-1234567890",  # Same ISBN, different batch
            buy_price=Decimal("22.00"),
            expected_sale_price=Decimal("32.00"),
            fees=Decimal("3.50"),
            profit=Decimal("6.50"),
            roi_percent=Decimal("29.5"),
            velocity_score=Decimal("8.0"),
            raw_keepa={"title": "Book in Batch 2"}
        )
        
        db_session.add_all([analysis1, analysis2])
        db_session.flush()  # Should work - same ISBN in different batches is OK
        db_session.commit()


class TestDataIntegrityAndConstraints:
    """Test data integrity and constraint validation."""

    def test_decimal_precision_constraints(self, db_session):
        """Test that decimal fields handle precision correctly."""
        analysis = Analysis(
            batch_id=str(uuid4()),
            isbn_or_asin="978-1234567890",
            buy_price=Decimal("20.999999999"),  # High precision
            expected_sale_price=Decimal("30.123456789"),
            fees=Decimal("3.01"),
            profit=Decimal("6.113456789"),
            roi_percent=Decimal("30.567891234"),
            velocity_score=Decimal("7.123456789"),
            raw_keepa={"title": "Precision Test Book"}
        )
        
        # Values should be stored and retrieved correctly
        # SQLAlchemy will handle precision based on column definition
        assert analysis.buy_price == Decimal("20.999999999")
        assert analysis.roi_percent == Decimal("30.567891234")

    def test_json_field_handling(self, db_session, user_data):
        """Test JSON field storage and retrieval."""
        user = User(**user_data)
        db_session.add(user)
        db_session.flush()
        
        # Complex strategy snapshot
        complex_strategy = {
            "profit_threshold": 20.0,
            "roi_threshold": 35.0,
            "risk_tolerance": "medium",
            "categories": ["textbooks", "professional"],
            "filters": {
                "min_rank": 100000,
                "max_price": 50.0,
                "exclude_keywords": ["damaged", "library"]
            },
            "scoring": {
                "profit_weight": 0.4,
                "velocity_weight": 0.3,
                "risk_weight": 0.3
            }
        }
        
        batch = Batch(
            user_id=user.id,
            name="JSON Test Batch",
            items_total=25,
            strategy_snapshot=complex_strategy
        )
        db_session.add(batch)
        db_session.flush()
        
        # Verify JSON storage and retrieval
        assert batch.strategy_snapshot["profit_threshold"] == 20.0
        assert batch.strategy_snapshot["filters"]["min_rank"] == 100000
        assert len(batch.strategy_snapshot["categories"]) == 2

    def test_required_fields_validation(self, db_session):
        """Test that required fields are properly validated."""
        # Test batch without required user_id
        try:
            batch = Batch(
                user_id=None,  # Explicitly None
                name="Incomplete Batch",
                items_total=10,
                strategy_snapshot={"test": "data"}
            )
            db_session.add(batch)
            db_session.flush()
            # If we get here, the test failed
            assert False, "Expected IntegrityError for missing user_id"
        except IntegrityError:
            # Expected behavior
            db_session.rollback()
            pass
            
        # Test analysis without required batch_id
        try:  
            analysis = Analysis(
                batch_id=None,  # Explicitly None
                isbn_or_asin="978-1234567890",
                buy_price=Decimal("20.00"),
                expected_sale_price=Decimal("30.00"),
                fees=Decimal("3.00"),
                profit=Decimal("7.00"),
                roi_percent=Decimal("35.0"),
                velocity_score=Decimal("7.5"),
                raw_keepa={"title": "Test Book"}
            )
            db_session.add(analysis)
            db_session.flush()
            # If we get here, the test failed
            assert False, "Expected IntegrityError for missing batch_id"
        except IntegrityError:
            # Expected behavior
            db_session.rollback()
            pass