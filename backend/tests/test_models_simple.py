"""
Simple tests for data models - direct testing
"""
import pytest
from decimal import Decimal
from app.models.batch import Batch, BatchStatus
from app.models.analysis import Analysis
from app.models.user import User


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    import uuid
    unique_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        password_hash="hashed_password_123",
        first_name="Test",
        last_name="User",
        role="SOURCER"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def batch_data():
    """Sample batch data."""
    return {
        "name": "Test Analysis Batch", 
        "items_total": 50,
        "strategy_snapshot": {
            "roi_threshold": 35.0,
            "profit_threshold": 20.0,
            "risk_tolerance": "medium"
        }
    }


@pytest.fixture
def analysis_data():
    """Sample analysis data.""" 
    return {
        "asin": "B07ABCD123",
        "buy_price": 15.99,
        "expected_sale_price": 24.99,
        "amazon_fees": 3.75,
        "profit": 5.25,
        "roi_percentage": 32.83,
        "velocity_score": 75.0,
        "raw_keepa": {
            "title": "Python Programming Book",
            "category": "Books", 
            "sales_rank": 12500
        }
    }


def test_batch_creation(db_session, test_user, batch_data):
    """Test basic batch creation."""
    batch = Batch(
        user_id=test_user.id,
        name=batch_data["name"],
        items_total=batch_data["items_total"],
        strategy_snapshot=batch_data["strategy_snapshot"]
    )
    
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    
    assert batch.id is not None
    assert batch.items_total == batch_data["items_total"]
    assert batch.status == BatchStatus.PENDING
    assert batch.items_processed == 0
    assert batch.progress_percentage == 0.0


def test_analysis_creation_with_batch(db_session, test_user, batch_data, analysis_data):
    """Test analysis creation linked to batch."""
    # Create batch first
    batch = Batch(
        user_id=test_user.id,
        name=batch_data["name"],
        items_total=batch_data["items_total"],
        strategy_snapshot=batch_data["strategy_snapshot"]
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    
    # Create analysis with batch reference
    analysis = Analysis(
        batch_id=batch.id,
        isbn_or_asin=analysis_data["asin"],
        buy_price=Decimal(str(analysis_data["buy_price"])),
        expected_sale_price=Decimal(str(analysis_data["expected_sale_price"])),
        fees=Decimal(str(analysis_data["amazon_fees"])),
        profit=Decimal(str(analysis_data["profit"])),
        roi_percent=Decimal(str(analysis_data["roi_percentage"])),
        velocity_score=Decimal(str(analysis_data["velocity_score"])),
        raw_keepa=analysis_data["raw_keepa"]
    )
    
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    
    assert analysis.id is not None
    assert analysis.batch_id == batch.id
    assert analysis.isbn_or_asin == analysis_data["asin"]
    assert analysis.profit == Decimal(str(analysis_data["profit"]))


def test_batch_status_transitions(db_session, test_user, batch_data):
    """Test batch status transitions."""
    batch = Batch(
        user_id=test_user.id,
        name=batch_data["name"],
        items_total=batch_data["items_total"],
        strategy_snapshot=batch_data["strategy_snapshot"]
    )
    db_session.add(batch)
    db_session.commit()
    
    # Test valid transitions
    assert batch.can_transition_to(BatchStatus.RUNNING)
    assert not batch.can_transition_to(BatchStatus.DONE)
    assert not batch.can_transition_to(BatchStatus.FAILED)
    
    # Transition to running
    batch.status = BatchStatus.RUNNING
    db_session.commit()
    
    assert batch.can_transition_to(BatchStatus.DONE)
    assert batch.can_transition_to(BatchStatus.FAILED)
    assert not batch.can_transition_to(BatchStatus.PENDING)


def test_batch_progress_tracking(db_session, test_user, batch_data):
    """Test batch progress tracking."""
    batch = Batch(
        user_id=test_user.id,
        name=batch_data["name"],
        items_total=100,
        strategy_snapshot=batch_data["strategy_snapshot"]
    )
    db_session.add(batch)
    db_session.commit()
    
    # Update progress
    batch.items_processed = 25
    db_session.commit()
    
    assert batch.progress_percentage == 25.0
    assert not batch.is_completed
    
    # Complete batch
    batch.items_processed = 100
    batch.status = BatchStatus.DONE
    db_session.commit()
    
    assert batch.progress_percentage == 100.0
    assert batch.is_completed


def test_roi_calculations(db_session, test_user, batch_data):
    """Test ROI calculations in analysis."""
    batch = Batch(
        user_id=test_user.id,
        name=batch_data["name"],
        items_total=batch_data["items_total"],
        strategy_snapshot=batch_data["strategy_snapshot"]
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    
    # Create analysis with known values
    analysis = Analysis(
        batch_id=batch.id,
        isbn_or_asin="B071234567",
        buy_price=Decimal("10.00"),
        expected_sale_price=Decimal("20.00"),
        fees=Decimal("2.50"),
        profit=Decimal("7.50"),  # 20 - 2.5 - 10
        roi_percent=Decimal("75.00"),  # 7.5/10 * 100
        velocity_score=Decimal("85.0"),
        raw_keepa={"title": "Test Book"}
    )
    
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    
    # Test calculated fields
    assert analysis.profit == Decimal("7.50")
    assert analysis.roi_percent == Decimal("75.00")
    assert analysis.is_profitable
    assert analysis.meets_roi_threshold(Decimal("50.00"))
    assert not analysis.meets_roi_threshold(Decimal("80.00"))


def test_multiple_analyses_per_batch(db_session, test_user, batch_data):
    """Test multiple analyses linked to one batch."""
    batch = Batch(
        user_id=test_user.id,
        name=batch_data["name"],
        items_total=3,
        strategy_snapshot=batch_data["strategy_snapshot"]
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    
    # Create multiple analyses
    analyses_data = [
        {"isbn_or_asin": "B071111111", "profit": "5.00", "roi": "25.0"},
        {"isbn_or_asin": "B072222222", "profit": "10.00", "roi": "50.0"},
        {"isbn_or_asin": "B073333333", "profit": "15.00", "roi": "75.0"}
    ]
    
    for data in analyses_data:
        analysis = Analysis(
            batch_id=batch.id,
            isbn_or_asin=data["isbn_or_asin"],
            buy_price=Decimal("20.00"),
            expected_sale_price=Decimal("30.00"),
            fees=Decimal("5.00"),
            profit=Decimal(data["profit"]),
            roi_percent=Decimal(data["roi"]),
            velocity_score=Decimal("60.0"),
            raw_keepa={"title": f"Book {data['isbn_or_asin']}"}
        )
        db_session.add(analysis)
    
    db_session.commit()
    
    # Test relationship by querying directly
    analyses_count = db_session.query(Analysis).filter_by(batch_id=batch.id).count()
    assert analyses_count == 3
    
    # Test filtering
    analyses = db_session.query(Analysis).filter_by(batch_id=batch.id).all()
    profitable_analyses = [a for a in analyses if a.is_profitable]
    assert len(profitable_analyses) == 3  # All should be profitable
    
    high_roi_analyses = [a for a in analyses if a.meets_roi_threshold(Decimal("40.0"))]
    assert len(high_roi_analyses) == 2  # 50% and 75%