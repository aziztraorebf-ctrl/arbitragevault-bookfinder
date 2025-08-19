"""
Tests basiques pour valider les modèles et leurs champs.
"""
import pytest
from decimal import Decimal
from app.models.batch import Batch, BatchStatus
from app.models.analysis import Analysis
from app.repositories.batch_repository import BatchRepository
from app.repositories.analysis_repository import AnalysisRepository


def test_basic_batch_creation(db_session):
    """Test création basique d'un batch."""
    batch_repo = BatchRepository(db_session)
    
    batch = Batch(
        user_id="test-user-123",
        name="Test Batch",
        items_total=10,
        strategy_snapshot={"test": "data"}
    )
    
    created = batch_repo.create(batch)
    assert created.id is not None
    assert created.name == "Test Batch"
    assert created.items_total == 10
    assert created.status == BatchStatus.PENDING


def test_basic_analysis_creation(db_session):
    """Test création basique d'une analysis."""
    batch_repo = BatchRepository(db_session)
    analysis_repo = AnalysisRepository(db_session)
    
    # Créer un batch d'abord
    batch = Batch(
        user_id="test-user-123",
        name="Test Batch",
        items_total=10,
        strategy_snapshot={"test": "data"}
    )
    created_batch = batch_repo.create(batch)
    
    # Créer une analysis
    analysis = Analysis(
        batch_id=created_batch.id,
        isbn_or_asin="9781234567890",
        buy_price=Decimal("15.00"),
        expected_sale_price=Decimal("25.00"),
        fees=Decimal("3.50"),
        profit=Decimal("6.50"),
        roi_percent=Decimal("43.33"),
        velocity_score=Decimal("7.2"),
        raw_keepa={"title": "Test Book"}
    )
    
    created = analysis_repo.create(analysis)
    assert created.id is not None
    assert created.isbn_or_asin == "9781234567890"
    assert created.profit == Decimal("6.50")


def test_batch_status_enum():
    """Test les valeurs du status enum."""
    assert BatchStatus.PENDING.value == "pending"
    assert BatchStatus.RUNNING.value == "running"
    assert BatchStatus.DONE.value == "done"
    assert BatchStatus.FAILED.value == "failed"


def test_constraint_positive_items(db_session):
    """Test la contrainte CHECK sur items_total."""
    batch_repo = BatchRepository(db_session)
    
    # Test avec items_total négatif - doit échouer
    batch = Batch(
        user_id="test-user-123",
        name="Invalid Batch",
        items_total=-5,
        strategy_snapshot={"test": "data"}
    )
    
    with pytest.raises(Exception):  # IntegrityError attendu
        batch_repo.create(batch)


def test_batch_analysis_relationship(db_session):
    """Test la relation batch-analysis."""
    batch_repo = BatchRepository(db_session)
    analysis_repo = AnalysisRepository(db_session)
    
    # Créer batch
    batch = Batch(
        user_id="test-user-123",
        name="Relationship Test",
        items_total=3,
        strategy_snapshot={"test": "data"}
    )
    created_batch = batch_repo.create(batch)
    
    # Créer plusieurs analyses
    for i in range(3):
        analysis = Analysis(
            batch_id=created_batch.id,
            isbn_or_asin=f"978{i:010d}",
            buy_price=Decimal("10.00"),
            expected_sale_price=Decimal("20.00"),
            fees=Decimal("2.50"),
            profit=Decimal("7.50"),
            roi_percent=Decimal("75.0"),
            velocity_score=Decimal("5.0"),
            raw_keepa={"book": f"Book {i}"}
        )
        analysis_repo.create(analysis)
    
    # Vérifier qu'on peut récupérer toutes les analyses du batch
    batch_analyses = analysis_repo.get_by_batch_id(created_batch.id)
    assert len(batch_analyses) == 3