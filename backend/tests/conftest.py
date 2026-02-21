"""Test configuration and fixtures."""

import asyncio
import tempfile
import os
import uuid
from typing import AsyncGenerator, List
from httpx import AsyncClient, ASGITransport
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
# AutoSourcing models use a different Base (app.core.db.Base)
from app.core.db import Base as CoreBase
from app.models.autosourcing import AutoSourcingJob, AutoSourcingPick, SavedProfile, JobStatus

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

    # Create all tables (both Base classes)
    Base.metadata.create_all(bind=engine)
    CoreBase.metadata.create_all(bind=engine)
    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    CoreBase.metadata.drop_all(bind=engine)


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

    # Create tables fresh for each test (both Base classes)
    async with async_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(CoreBase.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(CoreBase.metadata.create_all)

    # Create session with expire_on_commit=False to avoid lazy loading issues
    async_session = AsyncSessionClass(bind=async_test_engine, expire_on_commit=False)

    yield async_session

    # Cleanup
    await async_session.rollback()
    await async_session.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing FastAPI app."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


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
def mock_keepa_balance():
    """Mock Keepa service check_api_balance to return test value."""
    from unittest.mock import AsyncMock, patch

    with patch('app.services.keepa_service.KeepaService.check_api_balance', new_callable=AsyncMock) as mock:
        mock.return_value = 1000
        yield mock
