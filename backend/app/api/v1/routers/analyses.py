"""Analysis endpoints for retrieving and managing book analysis data."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.core.pagination import PaginatedResponse, PaginationParams
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.base_repository import SortOrder
from app.schemas.analysis import AnalysisResponse, AnalysisCreate, TopAnalysisStrategy

router = APIRouter()


@router.get("", response_model=PaginatedResponse[AnalysisResponse])
async def list_analyses(
    batch_id: Optional[str] = Query(None, description="Filter by batch ID"),
    min_roi: Optional[float] = Query(None, ge=0, description="Minimum ROI percentage"),
    max_roi: Optional[float] = Query(None, ge=0, description="Maximum ROI percentage"),
    min_velocity: Optional[float] = Query(None, ge=0, le=1, description="Minimum velocity score"),
    max_velocity: Optional[float] = Query(None, ge=0, le=1, description="Maximum velocity score"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db_session)
) -> PaginatedResponse[AnalysisResponse]:
    """
    Get paginated list of analyses with optional filtering from database.
    
    Now connected to real AnalysisRepository with filtering capabilities.
    """
    try:
        repo = AnalysisRepository(db)
        
        # Build filters
        filters = {}
        if batch_id:
            filters["batch_id"] = batch_id
        if min_roi is not None:
            filters["roi_percent__gte"] = min_roi
        if max_roi is not None:
            filters["roi_percent__lte"] = max_roi
        if min_velocity is not None:
            filters["velocity_score__gte"] = min_velocity
        if max_velocity is not None:
            filters["velocity_score__lte"] = max_velocity
        
        # Get filtered and paginated analyses
        analyses = await repo.get_filtered(
            filters=filters,
            limit=pagination.per_page,
            offset=(pagination.page - 1) * pagination.per_page,
            sort_field="roi_percent",
            sort_order=SortOrder.DESC
        )
        
        # Count total with filters
        total = await repo.count_filtered(filters)
        
        # Convert to response models
        analysis_responses = []
        for analysis in analyses:
            analysis_responses.append(AnalysisResponse(
                id=analysis.id,
                batch_id=analysis.batch_id,
                isbn_or_asin=analysis.isbn_or_asin,
                buy_price=float(analysis.buy_price),
                fees=float(analysis.fees),
                expected_sale_price=float(analysis.expected_sale_price),
                profit=float(analysis.profit),
                roi_percent=float(analysis.roi_percent),
                velocity_score=float(analysis.velocity_score),
                rank_snapshot=analysis.rank_snapshot,
                offers_count=analysis.offers_count,
                created_at=analysis.created_at
            ))
        
        return PaginatedResponse(
            items=analysis_responses,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            pages=(total + pagination.per_page - 1) // pagination.per_page
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analyses: {str(e)}"
        )


@router.get("/top", response_model=list[AnalysisResponse])
async def get_top_analyses(
    batch_id: str = Query(..., description="Batch ID to get top analyses from"),
    strategy: TopAnalysisStrategy = Query(
        TopAnalysisStrategy.ROI, 
        description="Strategy for ranking: roi, velocity, or balanced"
    ),
    limit: int = Query(10, ge=1, le=50, description="Number of top analyses to return"),
    db: AsyncSession = Depends(get_db_session)
) -> list[AnalysisResponse]:
    """
    Get top N analyses from a batch using specified ranking strategy from database.
    
    Now connected to real repository with intelligent sorting.
    """
    try:
        repo = AnalysisRepository(db)
        
        # Determine sort field based on strategy
        if strategy == TopAnalysisStrategy.ROI:
            sort_field = "roi_percent"
        elif strategy == TopAnalysisStrategy.VELOCITY:
            sort_field = "velocity_score"
        else:  # BALANCED
            sort_field = "profit"  # or could be a calculated balanced score
        
        # Get top analyses from the specified batch
        analyses = await repo.get_filtered(
            filters={"batch_id": batch_id},
            limit=limit,
            sort_field=sort_field,
            sort_order=SortOrder.DESC
        )
        
        # Convert to response models
        analysis_responses = []
        for analysis in analyses:
            analysis_responses.append(AnalysisResponse(
                id=analysis.id,
                batch_id=analysis.batch_id,
                isbn_or_asin=analysis.isbn_or_asin,
                buy_price=float(analysis.buy_price),
                fees=float(analysis.fees),
                expected_sale_price=float(analysis.expected_sale_price),
                profit=float(analysis.profit),
                roi_percent=float(analysis.roi_percent),
                velocity_score=float(analysis.velocity_score),
                rank_snapshot=analysis.rank_snapshot,
                offers_count=analysis.offers_count,
                created_at=analysis.created_at
            ))
        
        return analysis_responses
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve top analyses: {str(e)}"
        )


@router.post("", status_code=201, response_model=AnalysisResponse)
async def create_analysis(
    analysis_data: AnalysisCreate,
    db: AsyncSession = Depends(get_db_session)
) -> AnalysisResponse:
    """
    Create a new analysis record in database.
    
    Now connected to real repository with data persistence.
    """
    try:
        repo = AnalysisRepository(db)
        
        # Create analysis in database
        analysis = await repo.create_analysis(
            batch_id=analysis_data.batch_id,
            isbn_or_asin=analysis_data.isbn_or_asin,
            buy_price=analysis_data.buy_price,
            fees=analysis_data.fees,
            expected_sale_price=analysis_data.expected_sale_price,
            profit=analysis_data.profit,
            roi_percent=analysis_data.roi_percent,
            velocity_score=analysis_data.velocity_score,
            rank_snapshot=analysis_data.rank_snapshot,
            offers_count=analysis_data.offers_count,
            raw_keepa=analysis_data.raw_keepa
        )
        
        return AnalysisResponse(
            id=analysis.id,
            batch_id=analysis.batch_id,
            isbn_or_asin=analysis.isbn_or_asin,
            buy_price=float(analysis.buy_price),
            fees=float(analysis.fees),
            expected_sale_price=float(analysis.expected_sale_price),
            profit=float(analysis.profit),
            roi_percent=float(analysis.roi_percent),
            velocity_score=float(analysis.velocity_score),
            rank_snapshot=analysis.rank_snapshot,
            offers_count=analysis.offers_count,
            created_at=analysis.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create analysis: {str(e)}"
        )