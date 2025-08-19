"""Test configuration and fixtures."""

import asyncio
import tempfile
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.models.base import Base

# Test database URL (SQLite in memory for speed)
TEST_DATABASE_URL = "sqlite:///:memory:"


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


@pytest.fixture
def db_session(test_engine) -> Session:
    """Create database session for testing."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    yield session
    
    # Cleanup
    session.rollback()
    session.close()


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
