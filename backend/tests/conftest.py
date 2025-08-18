"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.db import get_database_session
from app.core.settings import get_settings
from app.main import app
from app.models.base import Base

# Test database URL (SQLite in memory for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

settings = get_settings()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=settings.db_echo,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden database session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_database_session] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "John",
        "last_name": "Doe",
        "role": "SOURCER",
    }


@pytest.fixture
def admin_user_data():
    """Sample admin user data for testing."""
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "first_name": "Admin",
        "last_name": "User",
        "role": "ADMIN",
    }


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, user_data):
    """Create a test user in the database."""
    from app.core.security import hash_password
    from app.repositories.user_repo import UserRepository

    user_repo = UserRepository(db_session)

    user = await user_repo.create_user(
        email=user_data["email"],
        password_hash=hash_password(user_data["password"]),
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        role=user_data["role"],
        is_verified=True,
    )

    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, admin_user_data):
    """Create a test admin user in the database."""
    from app.core.security import hash_password
    from app.repositories.user_repo import UserRepository

    user_repo = UserRepository(db_session)

    admin = await user_repo.create_user(
        email=admin_user_data["email"],
        password_hash=hash_password(admin_user_data["password"]),
        first_name=admin_user_data["first_name"],
        last_name=admin_user_data["last_name"],
        role=admin_user_data["role"],
        is_verified=True,
    )

    return admin


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user, user_data):
    """Get authentication headers for test user."""
    # Login to get access token
    login_data = {"username": user_data["email"], "password": user_data["password"]}

    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200

    token_data = response.json()
    access_token = token_data["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(client: AsyncClient, admin_user, admin_user_data):
    """Get authentication headers for admin user."""
    # Login to get access token
    login_data = {
        "username": admin_user_data["email"],
        "password": admin_user_data["password"],
    }

    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200

    token_data = response.json()
    access_token = token_data["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


class TestHelpers:
    """Helper functions for tests."""

    @staticmethod
    def assert_user_response(user_data: dict, response_data: dict):
        """Assert user response matches expected data."""
        assert response_data["email"] == user_data["email"]
        assert response_data["first_name"] == user_data["first_name"]
        assert response_data["last_name"] == user_data["last_name"]
        assert response_data["role"] == user_data["role"]
        assert "id" in response_data
        assert "created_at" in response_data
        assert "password" not in response_data
        assert "password_hash" not in response_data

    @staticmethod
    def assert_error_response(response_data: dict, expected_status: int):
        """Assert error response structure."""
        assert "detail" in response_data or "message" in response_data
        assert response_data.get("status_code", expected_status) == expected_status


@pytest.fixture
def helpers():
    """Provide test helper functions."""
    return TestHelpers
