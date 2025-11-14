"""
Tests for AutoSourcing job validation service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.autosourcing_validator import AutoSourcingValidator
from app.schemas.autosourcing_safeguards import (
    MAX_TOKENS_PER_JOB,
    MIN_TOKEN_BALANCE_REQUIRED
)
from fastapi import HTTPException

@pytest.fixture
def mock_cost_estimator():
    """Mock cost estimator."""
    estimator = MagicMock()
    estimator.estimate_total_job_cost = MagicMock(return_value=150)
    return estimator

@pytest.fixture
def mock_keepa_service():
    """Mock Keepa service for balance checks."""
    service = MagicMock()
    service.get_token_balance = AsyncMock(return_value=1000)
    return service

@pytest.fixture
def validator(mock_cost_estimator, mock_keepa_service):
    """Fixture for validator instance with mocked dependencies."""
    return AutoSourcingValidator(
        cost_estimator=mock_cost_estimator,
        keepa_service=mock_keepa_service
    )

@pytest.mark.asyncio
async def test_validate_job_success(validator, mock_cost_estimator):
    """Test successful job validation when cost and balance are acceptable."""
    discovery_config = {"categories": ["books"], "max_results": 50}
    scoring_config = {}

    # Mock: estimated cost = 150 tokens, balance = 1000 tokens
    result = await validator.validate_job_requirements(discovery_config, scoring_config)

    assert result.estimated_tokens == 150
    assert result.current_balance == 1000
    assert result.safe_to_proceed is True
    assert result.warning_message is None

@pytest.mark.asyncio
async def test_validate_job_rejects_expensive_jobs(validator, mock_cost_estimator):
    """Test validation rejects jobs exceeding MAX_TOKENS_PER_JOB."""
    discovery_config = {"categories": ["books"], "max_results": 500}
    scoring_config = {}

    # Mock estimator to return cost > MAX_TOKENS_PER_JOB
    mock_cost_estimator.estimate_total_job_cost.return_value = 250

    with pytest.raises(HTTPException) as exc_info:
        await validator.validate_job_requirements(discovery_config, scoring_config)

    assert exc_info.value.status_code == 400
    assert "JOB_TOO_EXPENSIVE" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_validate_job_rejects_insufficient_balance(validator, mock_keepa_service):
    """Test validation rejects jobs when token balance too low."""
    discovery_config = {"categories": ["books"], "max_results": 20}
    scoring_config = {}

    # Mock balance below MIN_TOKEN_BALANCE_REQUIRED
    mock_keepa_service.get_token_balance.return_value = 30

    with pytest.raises(HTTPException) as exc_info:
        await validator.validate_job_requirements(discovery_config, scoring_config)

    assert exc_info.value.status_code == 429
    assert "INSUFFICIENT_TOKENS" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_validate_job_provides_helpful_error_details(validator, mock_cost_estimator):
    """Test error responses include actionable details."""
    discovery_config = {"categories": ["books"], "max_results": 500}

    mock_cost_estimator.estimate_total_job_cost.return_value = 300

    with pytest.raises(HTTPException) as exc_info:
        await validator.validate_job_requirements(discovery_config, scoring_config={})

    detail = exc_info.value.detail
    assert "estimated_tokens" in detail
    assert "max_allowed" in detail
    assert "suggestion" in detail
