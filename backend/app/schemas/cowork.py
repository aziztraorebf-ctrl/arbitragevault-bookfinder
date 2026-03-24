"""Pydantic schemas for Cowork API request/response models."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CoworkAutoSourcingStats(BaseModel):
    jobs_last_24h: int
    picks_last_24h: int
    last_run_at: Optional[str]
    last_run_status: Optional[str]


class CoworkDailyReviewStats(BaseModel):
    total_picks: int
    jackpot: int
    stable: int
    revenant: int
    fluke: int
    reject: int


class CoworkDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: str
    app_version: str
    environment: str
    db_healthy: bool
    keepa_configured: bool
    autosourcing: CoworkAutoSourcingStats
    daily_review: CoworkDailyReviewStats


class CoworkFetchAndScoreRequest(BaseModel):
    profile_name: Optional[str] = Field(default=None)
    categories: Optional[List[str]] = Field(default=None)
    max_results: Optional[int] = Field(default=None, ge=1, le=100)
    roi_min: Optional[float] = Field(default=None)


class CoworkFetchAndScoreResponse(BaseModel):
    job_id: str
    status: str
    picks_count: int
    message: str


class CoworkBuyListItem(BaseModel):
    asin: str
    title: Optional[str]
    classification: str
    roi: Optional[float]
    bsr: Optional[int]
    action: str
    first_seen_at: Optional[str]


class CoworkBuyListResponse(BaseModel):
    generated_at: str
    days_back: int
    total_actionable: int
    items: List[CoworkBuyListItem]
