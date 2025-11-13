"""Tests for AutoSourcing service token control."""
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.autosourcing_service import AutoSourcingService
from app.core.exceptions import InsufficientTokensError


@pytest.fixture
def mock_keepa_sufficient():
    """Mock KeepaService with sufficient balance."""
    keepa = Mock()
    keepa.can_perform_action = AsyncMock(return_value={
        "can_proceed": True,
        "current_balance": 300,
        "required_tokens": 200,
        "action": "auto_sourcing_job"
    })
    return keepa


@pytest.fixture
def mock_keepa_insufficient():
    """Mock KeepaService with insufficient balance."""
    keepa = Mock()
    keepa.can_perform_action = AsyncMock(return_value={
        "can_proceed": False,
        "current_balance": 50,
        "required_tokens": 200,
        "action": "auto_sourcing_job"
    })
    return keepa


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.add = Mock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    # Mock execute() for selectinload reload pattern
    # Return a result with scalar_one() that returns a mock job
    mock_result = AsyncMock()
    mock_job = AsyncMock()
    mock_job.picks = []  # Empty picks list
    mock_result.scalar_one = Mock(return_value=mock_job)
    db.execute = AsyncMock(return_value=mock_result)

    return db


@pytest.fixture
def autosourcing_service(mock_keepa_sufficient, mock_db):
    """Create AutoSourcingService with mocked dependencies."""
    service = AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa_sufficient)
    return service


@pytest.mark.asyncio
async def test_run_custom_search_checks_tokens_before_execution(mock_keepa_sufficient, mock_db):
    """Test run_custom_search checks tokens before starting job."""
    service = AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa_sufficient)

    # Mock the actual discovery logic to prevent real execution
    service._discover_products = AsyncMock(return_value=[])
    service._score_and_filter_products = AsyncMock(return_value=[])
    service._remove_recent_duplicates = AsyncMock(return_value=[])

    await service.run_custom_search(
        profile_name="test",
        discovery_config={},
        scoring_config={}
    )

    # Verify token check was called
    mock_keepa_sufficient.can_perform_action.assert_called_once_with("auto_sourcing_job")


@pytest.mark.asyncio
async def test_run_custom_search_raises_error_when_insufficient(mock_keepa_insufficient, mock_db):
    """Test run_custom_search raises InsufficientTokensError when tokens low."""
    service = AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa_insufficient)

    with pytest.raises(InsufficientTokensError) as exc_info:
        await service.run_custom_search(
            profile_name="test",
            discovery_config={},
            scoring_config={}
        )

    # Verify error details
    assert exc_info.value.details["current_balance"] == 50
    assert exc_info.value.details["required_tokens"] == 200
    assert exc_info.value.details["endpoint"] == "auto_sourcing_job"


@pytest.mark.asyncio
async def test_run_custom_search_logs_skip_when_insufficient(mock_keepa_insufficient, mock_db, caplog):
    """Test run_custom_search logs proper message when skipping."""
    service = AutoSourcingService(db_session=mock_db, keepa_service=mock_keepa_insufficient)

    with pytest.raises(InsufficientTokensError):
        await service.run_custom_search(
            profile_name="test",
            discovery_config={},
            scoring_config={}
        )

    # Verify log message
    assert "Insufficient tokens for AutoSourcing job" in caplog.text


@pytest.mark.asyncio
async def test_run_custom_search_returns_job_with_accessible_picks():
    """
    Test that run_custom_search returns job with picks relationship loaded.

    Regression test for MissingGreenlet error when FastAPI serializes response.
    The picks relationship MUST be eagerly loaded before returning from service,
    otherwise accessing job.picks after session commit raises MissingGreenlet.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.pool import StaticPool
    from app.models.base import Base
    from app.models.autosourcing import AutoSourcingJob, AutoSourcingPick

    # Create isolated async test engine for ONLY AutoSourcing tables
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )

    # Create only AutoSourcing tables (not business_config with JSONB)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[
            AutoSourcingJob.__table__,
            AutoSourcingPick.__table__
        ])

    # Create session with expire_on_commit=False
    async_session = AsyncSession(bind=engine, expire_on_commit=False)

    try:
        # Create mock KeepaService with sufficient tokens
        mock_keepa = Mock()
        mock_keepa.can_perform_action = AsyncMock(return_value={
            "can_proceed": True,
            "current_balance": 300,
            "required_tokens": 200,
            "action": "auto_sourcing_job"
        })

        # Create service with real async DB session
        service = AutoSourcingService(db_session=async_session, keepa_service=mock_keepa)

        # Mock internal methods to avoid Keepa API calls
        service._discover_products = AsyncMock(return_value=["B001TEST", "B002TEST"])
        service._score_and_filter_products = AsyncMock(return_value=[])
        service._remove_recent_duplicates = AsyncMock(return_value=[])

        # Execute run_custom_search
        job = await service.run_custom_search(
            profile_name="TDD Test Job",
            discovery_config={"categories": ["Books"]},
            scoring_config={"roi_min": 20}
        )

        # CRITICAL ASSERTION: Accessing job.picks should NOT raise MissingGreenlet
        # This will FAIL before fix because picks is lazy-loaded and session is closed
        try:
            picks_list = job.picks
            assert isinstance(picks_list, list), "job.picks should return a list"
        except Exception as e:
            if "MissingGreenlet" in str(e) or "greenlet_spawn" in str(e):
                pytest.fail(f"MissingGreenlet error when accessing job.picks: {e}")
            else:
                raise
    finally:
        await async_session.close()
        await engine.dispose()
