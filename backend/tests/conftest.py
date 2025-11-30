"""Test configuration and fixtures."""

import asyncio
import tempfile
import os
import uuid
from typing import AsyncGenerator, List
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.user import User
from app.models.batch import Batch, BatchStatus
from app.models.analysis import Analysis

# Test database URLs
TEST_DATABASE_URL = "sqlite:///:memory:"
TEST_ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def async_test_engine():
    """Create async test database engine."""
    engine = create_async_engine(
        TEST_ASYNC_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    yield engine


@pytest.fixture
def db_session(test_engine) -> Session:
    """Create database session for testing."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    yield session
    
    # Cleanup
    session.rollback()
    session.close()


@pytest_asyncio.fixture
async def async_db_session(async_test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing."""
    from sqlalchemy.ext.asyncio import AsyncSession as AsyncSessionClass
    
    # Create tables fresh for each test
    async with async_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session with expire_on_commit=False to avoid lazy loading issues
    async_session = AsyncSessionClass(bind=async_test_engine, expire_on_commit=False)
    
    yield async_session
    
    # Cleanup
    await async_session.rollback()
    await async_session.close()


@pytest_asyncio.fixture
async def sample_users(async_db_session: AsyncSession) -> List[User]:
    """Create sample users for testing."""
    users = [
        User(
            id=str(uuid.uuid4()),
            email="admin@example.com",
            password_hash="hashed_admin_password",
            first_name="Admin",
            last_name="User",
            role="admin"
        ),
        User(
            id=str(uuid.uuid4()),
            email="sourcer1@example.com", 
            password_hash="hashed_sourcer1_password",
            first_name="Sourcer",
            last_name="One",
            role="sourcer"
        ),
        User(
            id=str(uuid.uuid4()),
            email="sourcer2@example.com",
            password_hash="hashed_sourcer2_password", 
            first_name="Sourcer",
            last_name="Two",
            role="sourcer"
        )
    ]
    
    for user in users:
        async_db_session.add(user)
    
    await async_db_session.commit()
    
    for user in users:
        await async_db_session.refresh(user)
    
    return users


@pytest_asyncio.fixture
async def sample_batches(async_db_session: AsyncSession, sample_users: List[User]) -> List[Batch]:
    """Create sample batches for testing."""
    batches = [
        Batch(
            id=str(uuid.uuid4()),
            user_id=sample_users[0].id,
            name="Test Batch 1",
            status=BatchStatus.COMPLETED,
            items_total=100,
            items_processed=100
        ),
        Batch(
            id=str(uuid.uuid4()),
            user_id=sample_users[1].id,
            name="Test Batch 2", 
            status=BatchStatus.PROCESSING,
            items_total=50,
            items_processed=25
        ),
        Batch(
            id=str(uuid.uuid4()),
            user_id=sample_users[1].id,
            name="Test Batch 3",
            status=BatchStatus.PENDING,
            items_total=75,
            items_processed=0
        )
    ]
    
    for batch in batches:
        async_db_session.add(batch)
    
    await async_db_session.commit()
    
    for batch in batches:
        await async_db_session.refresh(batch)
    
    return batches


@pytest_asyncio.fixture
async def sample_analyses(async_db_session: AsyncSession, sample_batches: List[Batch]) -> List[Analysis]:
    """Create sample analyses for testing."""
    analyses = []
    
    # Create multiple analyses for first batch
    batch1 = sample_batches[0]
    analyses.extend([
        Analysis(
            id=str(uuid.uuid4()),
            batch_id=batch1.id,
            isbn_or_asin="978-0123456789",
            buy_price=Decimal("15.00"),
            fees=Decimal("3.50"),
            expected_sale_price=Decimal("25.00"),
            profit=Decimal("6.50"),
            roi_percent=Decimal("43.33"),
            velocity_score=Decimal("7.2"),
            raw_keepa={"test": "data1"}
        ),
        Analysis(
            id=str(uuid.uuid4()),
            batch_id=batch1.id,
            isbn_or_asin="978-0987654321", 
            buy_price=Decimal("25.00"),
            fees=Decimal("5.00"),
            expected_sale_price=Decimal("45.00"),
            profit=Decimal("15.00"),
            roi_percent=Decimal("60.00"),
            velocity_score=Decimal("8.5"),
            raw_keepa={"test": "data2"}
        ),
        Analysis(
            id=str(uuid.uuid4()),
            batch_id=batch1.id,
            isbn_or_asin="978-0555666777",
            buy_price=Decimal("10.00"),
            fees=Decimal("2.00"), 
            expected_sale_price=Decimal("15.00"),
            profit=Decimal("3.00"),
            roi_percent=Decimal("30.00"),
            velocity_score=Decimal("5.8"),
            raw_keepa={"test": "data3"}
        )
    ])
    
    # Create analyses for second batch
    batch2 = sample_batches[1] 
    analyses.extend([
        Analysis(
            id=str(uuid.uuid4()),
            batch_id=batch2.id,
            isbn_or_asin="978-0111222333",
            buy_price=Decimal("20.00"),
            fees=Decimal("4.00"),
            expected_sale_price=Decimal("40.00"),
            profit=Decimal("16.00"),
            roi_percent=Decimal("80.00"),
            velocity_score=Decimal("9.1"),
            raw_keepa={"test": "data4"}
        ),
        Analysis(
            id=str(uuid.uuid4()),
            batch_id=batch2.id,
            isbn_or_asin="978-0444555666",
            buy_price=Decimal("8.00"),
            fees=Decimal("1.50"),
            expected_sale_price=Decimal("10.00"),
            profit=Decimal("0.50"),
            roi_percent=Decimal("6.25"),
            velocity_score=Decimal("3.2"),
            raw_keepa={"test": "data5"}
        )
    ])
    
    for analysis in analyses:
        async_db_session.add(analysis)
    
    await async_db_session.commit()
    
    for analysis in analyses:
        await async_db_session.refresh(analysis)
    
    return analyses


@pytest.fixture
def user_data():
    """Sample user data for testing."""
    from uuid import uuid4
    return {
        "id": str(uuid4()),
        "email": f"test-{uuid4().hex[:8]}@example.com",
        "password_hash": "hashed_password_123",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture
def batch_data():
    """Sample batch data for testing."""
    return {
        "user_id": "test-user-123",
        "name": "Test Analysis Batch",
        "total_items": 50,
        "strategy_snapshot": {
            "profit_threshold": 20.0,
            "roi_threshold": 35.0,
            "risk_tolerance": "medium"
        }
    }

@pytest.fixture
def analysis_data():
    """Sample analysis data for testing.""" 
    return {
        "isbn": "9781234567890",
        "asin": "B07ABCD123",
        "buy_price": 15.99,
        "expected_sale_price": 24.99,
        "amazon_fees": 3.75,
        "profit": 5.25,
        "roi_percentage": 32.85,
        "velocity_score": 75,
        "keepa_data_raw": {
            "title": "Test Book",
            "category": "Textbook",
            "bsr": 15000
        }
    }


@pytest_asyncio.fixture
async def make_repo(async_db_session):
    """Factory fixture to create repositories with proper model signature."""
    from app.models.batch import Batch
    from app.models.user import User
    from app.models.analysis import Analysis
    from app.repositories.batch_repository import BatchRepository
    from app.repositories.user_repository import UserRepository
    from app.repositories.analysis_repository import AnalysisRepository

    def _make_repo(model_cls):
        """Create a repository instance for the given model class."""
        repo_map = {
            Batch: BatchRepository,
            User: UserRepository,
            Analysis: AnalysisRepository
        }
        repo_cls = repo_map.get(model_cls)
        if not repo_cls:
            raise ValueError(f"No repository mapped for model: {model_cls}")
        return repo_cls(async_db_session, model_cls)

    return _make_repo


@pytest.fixture
def mock_keepa_balance():
    """Mock Keepa service check_api_balance to return test value."""
    from unittest.mock import AsyncMock, patch

    with patch('app.services.keepa_service.KeepaService.check_api_balance', new_callable=AsyncMock) as mock:
        mock.return_value = 1000
        yield mock
