"""
Schemas for AutoSourcing safeguards and cost estimation.
Defines validation models and protection constants.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


# Protection Constants
MAX_TOKENS_PER_JOB = 200
MAX_PRODUCTS_PER_SEARCH = 10
TIMEOUT_PER_JOB = 120
MIN_TOKEN_BALANCE_REQUIRED = 50


class JobValidationResult(BaseModel):
    """Result of job requirement validation."""
    estimated_tokens: int = Field(..., description="Estimated token cost")
    current_balance: int = Field(..., description="Current Keepa balance")
    safe_to_proceed: bool = Field(..., description="Whether job can proceed")
    warning_message: Optional[str] = Field(None, description="Warning if unsafe")


class CostEstimateRequest(BaseModel):
    """Request to estimate job token cost."""
    discovery_config: Dict[str, Any] = Field(..., description="Discovery parameters")


class CostEstimateResponse(BaseModel):
    """Response with cost estimation details."""
    estimated_tokens: int
    current_balance: int
    safe_to_proceed: bool
    warning_message: Optional[str] = None
    max_allowed: int = MAX_TOKENS_PER_JOB
    suggestion: Optional[str] = None
