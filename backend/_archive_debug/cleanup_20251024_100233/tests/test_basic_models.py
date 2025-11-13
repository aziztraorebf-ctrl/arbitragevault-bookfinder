"""
Tests basiques pour valider les modèles et leurs champs.
"""
import pytest
from decimal import Decimal
from app.models.batch import Batch, BatchStatus
from app.models.analysis import Analysis


async def test_basic_batch_creation(make_repo):
    """Test création basique d'un batch."""
    batch_repo = make_repo(Batch)
    
    created = await batch_repo.create(
        user_id="test-user-123",
        name="Test Batch",
        items_total=10,
        strategy_snapshot={"test": "data"}
    )
    
    assert created.id is not None
    assert created.name == "Test Batch"
    assert created.items_total == 10
    assert created.status == BatchStatus.PENDING


async def test_basic_analysis_creation(make_repo):
    """Test création basique d'une analysis."""
    batch_repo = make_repo(Batch)
    analysis_repo = make_repo(Analysis)
    
    # Créer un batch d'abord
    created_batch = await batch_repo.create(
        user_id="test-user-123",
        name="Test Batch",
        items_total=10,
        strategy_snapshot={"test": "data"}
    )
    
    # Créer une analysis
    created = await analysis_repo.create(
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
    
    assert created.id is not None
    assert created.isbn_or_asin == "9781234567890"
    assert created.profit == Decimal("6.50")


def test_batch_status_enum():
    """Test les valeurs du status enum."""
    assert BatchStatus.PENDING.value == "pending"
    assert BatchStatus.RUNNING.value == "running"
    assert BatchStatus.DONE.value == "done"
    assert BatchStatus.FAILED.value == "failed"


async def test_constraint_positive_items(make_repo):
    """Test la contrainte CHECK sur items_total."""
    batch_repo = make_repo(Batch)
    
    # Test avec items_total négatif - doit échouer
    with pytest.raises(Exception):  # IntegrityError attendu
        await batch_repo.create(
            user_id="test-user-123",
            name="Invalid Batch",
            items_total=-5,
            strategy_snapshot={"test": "data"}
        )


async def test_batch_analysis_relationship(make_repo):
    """Test la relation batch-analysis."""
    batch_repo = make_repo(Batch)
    analysis_repo = make_repo(Analysis)
    
    # Créer batch
    created_batch = await batch_repo.create(
        user_id="test-user-123",
        name="Relationship Test",
        items_total=3,
        strategy_snapshot={"test": "data"}
    )
    
    # Créer plusieurs analyses
    for i in range(3):
        await analysis_repo.create(
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
    
    # Vérifier qu'on peut récupérer toutes les analyses du batch
    batch_analyses_page = await analysis_repo.list(filters={"batch_id": created_batch.id})
    assert len(batch_analyses_page.items) == 3