"""
AutoSourcing job validation service.
Validates jobs before execution to prevent token exhaustion.
"""
from typing import Dict, Any
from fastapi import HTTPException
from app.schemas.autosourcing_safeguards import (
    JobValidationResult,
    MAX_TOKENS_PER_JOB,
    MIN_TOKEN_BALANCE_REQUIRED
)
from app.services.autosourcing_cost_estimator import AutoSourcingCostEstimator
from app.services.keepa_service import KeepaService

class AutoSourcingValidator:
    """Validates AutoSourcing jobs against cost and balance limits."""

    def __init__(
        self,
        cost_estimator: AutoSourcingCostEstimator = None,
        keepa_service: KeepaService = None
    ):
        """
        Initialize validator with dependencies.

        Args:
            cost_estimator: Cost estimation service
            keepa_service: Keepa API service for balance checks
        """
        self.cost_estimator = cost_estimator or AutoSourcingCostEstimator()
        self.keepa_service = keepa_service

    async def validate_job_requirements(
        self,
        discovery_config: Dict[str, Any],
        scoring_config: Dict[str, Any]
    ) -> JobValidationResult:
        """
        Validate job requirements before execution.

        Args:
            discovery_config: Discovery configuration
            scoring_config: Scoring configuration

        Returns:
            JobValidationResult with validation outcome

        Raises:
            HTTPException: If job fails validation
        """
        # Estimate token cost
        estimated_tokens = self.cost_estimator.estimate_total_job_cost(discovery_config)

        # Check if cost exceeds limit
        if estimated_tokens > MAX_TOKENS_PER_JOB:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "JOB_TOO_EXPENSIVE",
                    "estimated_tokens": estimated_tokens,
                    "max_allowed": MAX_TOKENS_PER_JOB,
                    "suggestion": "Reduce max_results or narrow filters"
                }
            )

        # Get current token balance
        current_balance = await self.keepa_service.get_token_balance()

        # Check if balance is sufficient
        if current_balance < MIN_TOKEN_BALANCE_REQUIRED:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "INSUFFICIENT_TOKENS",
                    "balance": current_balance,
                    "required": MIN_TOKEN_BALANCE_REQUIRED
                }
            )

        # All checks passed
        return JobValidationResult(
            estimated_tokens=estimated_tokens,
            current_balance=current_balance,
            safe_to_proceed=True,
            warning_message=None
        )
