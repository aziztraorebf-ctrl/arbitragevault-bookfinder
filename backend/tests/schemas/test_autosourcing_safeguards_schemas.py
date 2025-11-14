"""
Tests for AutoSourcing safeguards schemas.
"""
import pytest
from pydantic import ValidationError
from app.schemas.autosourcing_safeguards import (
    JobValidationResult,
    CostEstimateRequest,
    CostEstimateResponse,
    MAX_TOKENS_PER_JOB,
    MAX_PRODUCTS_PER_SEARCH,
    TIMEOUT_PER_JOB,
    MIN_TOKEN_BALANCE_REQUIRED
)


def test_constants_have_correct_values():
    """Verify safeguard constants are set to production values."""
    assert MAX_TOKENS_PER_JOB == 200
    assert MAX_PRODUCTS_PER_SEARCH == 10
    assert TIMEOUT_PER_JOB == 120
    assert MIN_TOKEN_BALANCE_REQUIRED == 50


def test_job_validation_result_creation():
    """Test JobValidationResult schema validation."""
    result = JobValidationResult(
        estimated_tokens=150,
        current_balance=1000,
        safe_to_proceed=True,
        warning_message=None
    )
    assert result.estimated_tokens == 150
    assert result.current_balance == 1000
    assert result.safe_to_proceed is True


def test_job_validation_result_with_warning():
    """Test JobValidationResult with warning message."""
    result = JobValidationResult(
        estimated_tokens=250,
        current_balance=1000,
        safe_to_proceed=False,
        warning_message="Exceeds MAX_TOKENS_PER_JOB (200)"
    )
    assert result.safe_to_proceed is False
    assert "Exceeds" in result.warning_message


def test_cost_estimate_request_validation():
    """Test CostEstimateRequest schema accepts discovery config."""
    request = CostEstimateRequest(
        discovery_config={
            "categories": ["books"],
            "max_results": 50
        }
    )
    assert "categories" in request.discovery_config
    assert request.discovery_config["max_results"] == 50


def test_cost_estimate_response_structure():
    """Test CostEstimateResponse with all fields."""
    response = CostEstimateResponse(
        estimated_tokens=75,
        current_balance=500,
        safe_to_proceed=True,
        warning_message=None,
        max_allowed=200,
        suggestion=None
    )
    assert response.estimated_tokens == 75
    assert response.max_allowed == 200
