"""
AutoSourcing API endpoints for intelligent product discovery.
Provides REST interface for running searches, managing profiles, and tracking actions.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.services.autosourcing_service import AutoSourcingService
from app.services.keepa_service import KeepaService
from app.models.autosourcing import JobStatus, ActionStatus
from app.core.settings import get_settings

router = APIRouter(prefix="/autosourcing", tags=["AutoSourcing"])

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class DiscoveryConfig(BaseModel):
    """Configuration for product discovery via Keepa."""
    categories: List[str] = Field(..., description="Product categories to search")
    bsr_range: Optional[List[int]] = Field(None, description="BSR range [min, max]")
    price_range: Optional[List[float]] = Field(None, description="Price range [min, max]")
    discount_min: Optional[int] = Field(None, description="Minimum discount percentage")
    availability: Optional[str] = Field("amazon", description="Availability filter")
    max_results: Optional[int] = Field(50, description="Maximum results to discover")

class ScoringConfig(BaseModel):
    """Configuration for advanced scoring thresholds."""
    roi_min: float = Field(30.0, description="Minimum ROI percentage")
    velocity_min: int = Field(70, description="Minimum velocity score")
    stability_min: int = Field(70, description="Minimum stability score") 
    confidence_min: int = Field(70, description="Minimum confidence score")
    rating_required: str = Field("GOOD", description="Minimum overall rating")
    max_results: Optional[int] = Field(20, description="Maximum picks to return")

class RunCustomSearchRequest(BaseModel):
    """Request to run custom AutoSourcing search."""
    profile_name: str = Field(..., description="Name for this search")
    discovery_config: DiscoveryConfig
    scoring_config: ScoringConfig
    profile_id: Optional[UUID] = Field(None, description="Optional saved profile ID")

class CreateProfileRequest(BaseModel):
    """Request to create a new saved profile."""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    discovery_config: DiscoveryConfig
    scoring_config: ScoringConfig
    max_results: int = Field(20, ge=5, le=100)

class UpdateActionRequest(BaseModel):
    """Request to update pick action."""
    action: ActionStatus = Field(..., description="Action to take")
    notes: Optional[str] = Field(None, max_length=500)

class AutoSourcingPickResponse(BaseModel):
    """Response model for AutoSourcing pick."""
    id: UUID
    asin: str
    title: str
    current_price: Optional[float]
    roi_percentage: float
    velocity_score: int
    stability_score: int
    confidence_score: int
    overall_rating: str
    readable_summary: Optional[str]
    bsr: Optional[int]
    category: Optional[str]
    
    # Action tracking
    action_status: ActionStatus
    action_taken_at: Optional[datetime]
    is_purchased: bool
    is_favorite: bool
    is_ignored: bool
    
    created_at: datetime

    class Config:
        from_attributes = True

class AutoSourcingJobResponse(BaseModel):
    """Response model for AutoSourcing job."""
    id: UUID
    profile_name: str
    launched_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    status: JobStatus
    total_tested: int
    total_selected: int
    picks: List[AutoSourcingPickResponse] = []

    class Config:
        from_attributes = True

class SavedProfileResponse(BaseModel):
    """Response model for saved profile."""
    id: UUID
    name: str
    description: Optional[str]
    discovery_config: Dict[str, Any]
    scoring_config: Dict[str, Any]
    max_results: int
    active: bool
    last_used_at: Optional[datetime]
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class OpportunityOfDayResponse(BaseModel):
    """Response model for daily opportunity."""
    pick: AutoSourcingPickResponse
    job_profile: str
    found_at: datetime
    message: str

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_autosourcing_service(
    db: AsyncSession = Depends(get_db_session)
) -> AutoSourcingService:
    """Dependency to get AutoSourcing service."""
    settings = get_settings()
    keepa_service = KeepaService(api_key=settings.keepa_api_key)
    return AutoSourcingService(db, keepa_service)

# ============================================================================
# CORE SEARCH ENDPOINTS
# ============================================================================

@router.post("/run-custom", response_model=AutoSourcingJobResponse)
async def run_custom_search(
    request: RunCustomSearchRequest,
    service: AutoSourcingService = Depends(get_autosourcing_service)
):
    """
    Run custom AutoSourcing search with user-defined criteria.
    
    This endpoint orchestrates the complete discovery pipeline:
    1. Product discovery via Keepa Product Finder
    2. Advanced scoring with v1.5.0 system
    3. Filtering and ranking by user criteria
    4. Duplicate removal and result optimization
    """
    try:
        job = await service.run_custom_search(
            discovery_config=request.discovery_config.dict(),
            scoring_config=request.scoring_config.dict(),
            profile_name=request.profile_name,
            profile_id=request.profile_id
        )
        
        return job
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AutoSourcing search failed: {str(e)}"
        )

@router.get("/latest", response_model=Optional[AutoSourcingJobResponse])
async def get_latest_results(
    service: AutoSourcingService = Depends(get_autosourcing_service)
):
    """Get results from the most recent successful AutoSourcing job."""
    
    job = await service.get_latest_job()
    return job

@router.get("/opportunity-of-day", response_model=Optional[OpportunityOfDayResponse])
async def get_opportunity_of_day(
    service: AutoSourcingService = Depends(get_autosourcing_service)
):
    """Get the best opportunity discovered today across all jobs."""
    
    pick = await service.get_opportunity_of_day()
    
    if not pick:
        return None
        
    return OpportunityOfDayResponse(
        pick=pick,
        job_profile=pick.job.profile_name,
        found_at=pick.job.launched_at,
        message=f"🔥 Today's best opportunity: {pick.roi_percentage:.1f}% ROI"
    )

# ============================================================================
# JOB MANAGEMENT
# ============================================================================

@router.get("/jobs", response_model=List[AutoSourcingJobResponse])
async def get_recent_jobs(
    limit: int = Query(10, ge=1, le=50, description="Number of jobs to return"),
    service: AutoSourcingService = Depends(get_autosourcing_service)
):
    """Get list of recent AutoSourcing jobs with summary info."""
    
    jobs = await service.get_recent_jobs(limit=limit)
    return jobs

@router.get("/jobs/{job_id}", response_model=AutoSourcingJobResponse)
async def get_job_details(
    job_id: UUID,
    service: AutoSourcingService = Depends(get_autosourcing_service)
):
    """Get detailed results for a specific AutoSourcing job."""
    
    job = await service.get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
        
    return job

# ============================================================================
# PROFILE MANAGEMENT
# ============================================================================

@router.get("/profiles", response_model=List[SavedProfileResponse])
async def get_saved_profiles(
    active_only: bool = Query(True, description="Return only active profiles"),
    service: AutoSourcingService = Depends(get_autosourcing_service)
):
    """Get all saved AutoSourcing profiles."""
    
    profiles = await service.get_saved_profiles(active_only=active_only)
    return profiles

@router.post("/profiles", response_model=SavedProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    request: CreateProfileRequest,
    service: AutoSourcingService = Depends(get_autosourcing_service)
):
    """Create a new AutoSourcing profile for reuse."""
    
    try:
        profile = await service.create_profile({
            "name": request.name,
            "description": request.description,
            "discovery_config": request.discovery_config.dict(),
            "scoring_config": request.scoring_config.dict(),
            "max_results": request.max_results
        })
        
        return profile
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create profile: {str(e)}"
        )

# ============================================================================
# QUICK ACTIONS
# ============================================================================

@router.put("/picks/{pick_id}/action", response_model=AutoSourcingPickResponse)
async def update_pick_action(
    pick_id: UUID,
    request: UpdateActionRequest,
    service: AutoSourcingService = Depends(get_autosourcing_service)
):
    """Update user action on a discovered product pick."""
    
    try:
        pick = await service.update_pick_action(
            pick_id=pick_id,
            action=request.action,
            notes=request.notes
        )
        
        return pick
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/my-actions/{action}", response_model=List[AutoSourcingPickResponse])
async def get_picks_by_action(
    action: ActionStatus,
    service: AutoSourcingService = Depends(get_autosourcing_service)
):
    """Get all picks filtered by user action (to_buy, favorite, ignored, etc)."""
    
    picks = await service.get_picks_by_action(action)
    return picks

@router.get("/to-buy", response_model=List[AutoSourcingPickResponse])
async def get_to_buy_list(
    service: AutoSourcingService = Depends(get_autosourcing_service)
):
    """Get all products marked for purchase - convenience endpoint."""
    
    picks = await service.get_picks_by_action(ActionStatus.TO_BUY)
    return picks

@router.get("/favorites", response_model=List[AutoSourcingPickResponse])
async def get_favorites(
    service: AutoSourcingService = Depends(get_autosourcing_service)
):
    """Get all favorite products - convenience endpoint."""
    
    picks = await service.get_picks_by_action(ActionStatus.FAVORITE)
    return picks

# ============================================================================
# STATISTICS & INSIGHTS
# ============================================================================

@router.get("/stats")
async def get_action_stats(
    service: AutoSourcingService = Depends(get_autosourcing_service)
):
    """Get user action statistics and insights."""
    
    # Get counts for each action type
    stats = {}
    
    for action in ActionStatus:
        picks = await service.get_picks_by_action(action)
        stats[action.value] = len(picks)
    
    # Calculate some basic insights
    total_actions = sum(v for k, v in stats.items() if k != "pending")
    to_buy_count = stats.get("to_buy", 0)
    
    return {
        "action_counts": stats,
        "total_actions_taken": total_actions,
        "purchase_pipeline": to_buy_count,
        "engagement_rate": f"{(total_actions / max(stats.get('pending', 1), 1)) * 100:.1f}%"
    }

# ============================================================================
# HEALTH & DEBUG
# ============================================================================

@router.get("/health")
async def autosourcing_health():
    """Health check for AutoSourcing module."""
    
    return {
        "status": "healthy",
        "module": "AutoSourcing",
        "version": "1.0.0",
        "features": [
            "Custom search with Keepa integration",
            "Advanced scoring v1.5.0", 
            "Profile management",
            "Quick actions system",
            "Duplicate detection",
            "Opportunity of the day"
        ],
        "timestamp": datetime.utcnow()
    }