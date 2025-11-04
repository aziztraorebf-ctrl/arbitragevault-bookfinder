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
