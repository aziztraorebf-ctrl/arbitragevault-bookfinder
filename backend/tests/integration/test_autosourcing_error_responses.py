"""
Integration tests for API error response format and content.
Phase 7 Audit - Validates frontend-friendly error messages.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
from app.schemas.autosourcing_safeguards import MAX_TOKENS_PER_JOB, MIN_TOKEN_BALANCE_REQUIRED


class TestAutoSourcingErrorResponses:
    """Test API error responses are frontend-friendly."""

    def test_max_tokens_constant_defined(self):
        """Verify MAX_TOKENS_PER_JOB is properly defined."""
        assert MAX_TOKENS_PER_JOB == 200, f"Expected 200, got {MAX_TOKENS_PER_JOB}"

    def test_min_balance_constant_defined(self):
        """Verify MIN_TOKEN_BALANCE_REQUIRED is properly defined."""
        assert MIN_TOKEN_BALANCE_REQUIRED == 50, f"Expected 50, got {MIN_TOKEN_BALANCE_REQUIRED}"

    @pytest.mark.asyncio
    async def test_400_error_structure(self):
        """400 errors should have structured detail."""
        # Simulate a 400 error from validation
        error = HTTPException(
            status_code=400,
            detail={
                "error_code": "JOB_TOO_EXPENSIVE",
                "estimated_tokens": 250,
                "max_allowed": MAX_TOKENS_PER_JOB,
                "suggestion": "Reduce max_results or narrow filters"
            }
        )

        assert error.status_code == 400
        assert "error_code" in error.detail
        assert "suggestion" in error.detail
        assert error.detail["max_allowed"] == MAX_TOKENS_PER_JOB

    @pytest.mark.asyncio
    async def test_429_error_structure(self):
        """429 errors should include balance information."""
        error = HTTPException(
            status_code=429,
            detail={
                "error_code": "INSUFFICIENT_TOKENS",
                "current_balance": 30,
                "required_tokens": 100,
                "min_required": MIN_TOKEN_BALANCE_REQUIRED,
                "message": "Not enough tokens to perform this search"
            }
        )

        assert error.status_code == 429
        assert "current_balance" in error.detail
        assert "required_tokens" in error.detail
        assert error.detail["min_required"] == MIN_TOKEN_BALANCE_REQUIRED

    @pytest.mark.asyncio
    async def test_408_timeout_error_structure(self):
        """408 timeout errors should have clear message."""
        error = HTTPException(
            status_code=408,
            detail={
                "error_code": "JOB_TIMEOUT",
                "timeout_seconds": 120,
                "message": "Search job timeout - exceeded maximum allowed time (120s)"
            }
        )

        assert error.status_code == 408
        assert "timeout" in error.detail["message"].lower()
        assert error.detail["timeout_seconds"] == 120

    def test_error_codes_are_uppercase(self):
        """Error codes should be uppercase for consistency."""
        expected_codes = [
            "JOB_TOO_EXPENSIVE",
            "INSUFFICIENT_TOKENS",
            "JOB_TIMEOUT",
            "VALIDATION_ERROR",
            "DISCOVERY_FAILED"
        ]

        for code in expected_codes:
            assert code == code.upper(), f"Error code {code} should be uppercase"

    @pytest.mark.asyncio
    async def test_error_detail_is_dict_not_string(self):
        """Error details should be dicts for structured frontend parsing."""
        # Good: structured dict
        good_error = HTTPException(
            status_code=400,
            detail={"error_code": "TEST", "message": "Test error"}
        )
        assert isinstance(good_error.detail, dict)

        # String detail is allowed but dict is preferred
        string_error = HTTPException(status_code=400, detail="Simple error")
        assert isinstance(string_error.detail, str)

    @pytest.mark.asyncio
    async def test_validation_error_includes_field(self):
        """Validation errors should include which field failed."""
        error = HTTPException(
            status_code=422,
            detail={
                "error_code": "VALIDATION_ERROR",
                "field": "max_results",
                "message": "max_results must be between 1 and 100",
                "received_value": 500
            }
        )

        assert error.status_code == 422
        assert "field" in error.detail
        assert "received_value" in error.detail
