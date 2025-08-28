"""Batch endpoints for managing analysis batches."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.db import get_db_session
from app.core.pagination import PaginatedResponse, PaginationParams
from app.repositories.batch_repository import BatchRepository
from app.repositories.base_repository import SortOrder
from app.schemas.batch import BatchResponse, BatchStatusUpdate, BatchCreateRequest
from app.models.batch import BatchStatus

router = APIRouter()


@router.post("", status_code=201, response_model=BatchResponse)
async def create_batch(
    batch_request: BatchCreateRequest,
    db: AsyncSession = Depends(get_db_session)
) -> BatchResponse:
    """Create a new analysis batch in database."""
    
    try:
        repo = BatchRepository(db)
        
        # For now, use a default user ID (user auth will be added later)
        default_user_id = "default-user"
        
        batch = await repo.create_batch(
            user_id=default_user_id,
            name=batch_request.name,
            description=batch_request.description,
            items_total=len(batch_request.asin_list),
            strategy_snapshot={"config_name": batch_request.config_name}  # Store strategy config
        )
        
        return BatchResponse(
            id=batch.id,
            name=batch.name,
            status=batch.status.value,
            items_total=batch.items_total,
            items_processed=batch.items_processed,
            created_at=batch.created_at,
            started_at=batch.started_at,
            finished_at=batch.finished_at,
            progress_percentage=batch.progress_percentage
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create batch: {str(e)}"
        )


@router.get("", response_model=PaginatedResponse[BatchResponse])
async def list_batches(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db_session)
) -> PaginatedResponse[BatchResponse]:
    """
    Get paginated list of analysis batches from database.
    
    Now connected to real BatchRepository with database persistence.
    """
    try:
        repo = BatchRepository(db)
        
        # Get paginated batches (for now, get all user batches - user auth will be added later)
        batches = await repo.get_all(
            limit=pagination.per_page,
            offset=(pagination.page - 1) * pagination.per_page,
            sort_field="created_at",
            sort_order=SortOrder.DESC
        )
        
        # Count total batches
        total = await repo.count()
        
        # Convert to response models
        batch_responses = []
        for batch in batches:
            batch_responses.append(BatchResponse(
                id=batch.id,
                name=batch.name,
                status=batch.status.value,
                items_total=batch.items_total,
                items_processed=batch.items_processed,
                created_at=batch.created_at,
                started_at=batch.started_at,
                finished_at=batch.finished_at,
                progress_percentage=batch.progress_percentage
            ))
        
        return PaginatedResponse(
            items=batch_responses,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            pages=(total + pagination.per_page - 1) // pagination.per_page
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve batches: {str(e)}"
        )


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: str = Path(..., description="Batch ID"),
    db: AsyncSession = Depends(get_db_session)
) -> BatchResponse:
    """Get specific batch by ID with status and progress information from database."""
    
    try:
        repo = BatchRepository(db)
        batch = await repo.get_by_id(batch_id)
        
        if not batch:
            raise HTTPException(
                status_code=404,
                detail=f"Batch with ID {batch_id} not found"
            )
        
        return BatchResponse(
            id=batch.id,
            name=batch.name,
            status=batch.status.value,
            items_total=batch.items_total,
            items_processed=batch.items_processed,
            created_at=batch.created_at,
            started_at=batch.started_at,
            finished_at=batch.finished_at,
            progress_percentage=batch.progress_percentage
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve batch: {str(e)}"
        )


@router.patch("/{batch_id}/status", response_model=BatchResponse)
async def update_batch_status(
    status_update: BatchStatusUpdate,
    batch_id: str = Path(..., description="Batch ID"),
    db: AsyncSession = Depends(get_db_session)
) -> BatchResponse:
    """
    Update batch status with proper state transitions in database.
    
    Now connected to real repository with state validation.
    """
    try:
        repo = BatchRepository(db)
        
        # Get existing batch
        batch = await repo.get_by_id(batch_id)
        if not batch:
            raise HTTPException(
                status_code=404,
                detail=f"Batch with ID {batch_id} not found"
            )
        
        # Convert string status to enum
        from app.models.batch import BatchStatus
        try:
            new_status_enum = BatchStatus(status_update.status)
        except ValueError:
            valid_statuses = [s.value for s in BatchStatus]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status_update.status}. Valid options: {valid_statuses}"
            )
        
        # Update batch status using repository method
        updated_batch = await repo.update_batch_status(
            batch_id=batch_id,
            new_status=new_status_enum,
            error_message=status_update.error_message
        )
        
        return BatchResponse(
            id=updated_batch.id,
            name=updated_batch.name,
            status=updated_batch.status.value,
            items_total=updated_batch.items_total,
            items_processed=updated_batch.items_processed,
            created_at=updated_batch.created_at,
            started_at=updated_batch.started_at,
            finished_at=updated_batch.finished_at,
            progress_percentage=updated_batch.progress_percentage
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update batch status: {str(e)}"
        )