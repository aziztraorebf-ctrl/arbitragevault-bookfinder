"""Batch endpoints for managing analysis batches."""

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.db import get_db_session
from app.core.pagination import PaginatedResponse, PaginationParams
from app.repositories.batch_repository import BatchRepository
from app.schemas.batch import BatchResponse, BatchStatusUpdate
from app.models.batch import BatchStatus

router = APIRouter()


@router.get("", response_model=PaginatedResponse[BatchResponse])
async def list_batches(
    pagination: PaginationParams = Depends()
) -> PaginatedResponse[BatchResponse]:
    """
    Get paginated list of analysis batches.
    
    PHASE 1 STUB: Returns empty list for now, validates API structure.
    Will be connected to real repository in Phase 2.
    """
    return PaginatedResponse(
        items=[],
        total=0,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=0
    )


@router.get("/{batch_id}")
async def get_batch(
    batch_id: str = Path(..., description="Batch ID")
) -> dict:
    """Get specific batch by ID with status and progress information."""
    
    # PHASE 1 STUB: Return mock batch data
    return {
        "id": batch_id,
        "name": f"Sample Batch {batch_id}",
        "status": "pending",
        "items_total": 100,
        "items_processed": 0,
        "message": "Batch lookup validated - Phase 1 stub",
        "phase": "PHASE_1_STUB"
    }


@router.patch("/{batch_id}/status")
async def update_batch_status(
    status_update: BatchStatusUpdate,
    batch_id: str = Path(..., description="Batch ID")
) -> dict:
    """
    Update batch status with proper state transitions.
    
    PHASE 1 STUB: Validates state transition logic only.
    Will be connected to real repository in Phase 2.
    """
    new_status = status_update.status
    
    # Validate that status is valid BatchStatus enum
    from app.models.batch import BatchStatus
    
    valid_statuses = [s.value for s in BatchStatus]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {new_status}. Valid options: {valid_statuses}"
        )
    
    return {
        "batch_id": batch_id,
        "old_status": "pending",
        "new_status": new_status,  # new_status is already a string
        "error_message": status_update.error_message,
        "message": "Status transition validated - Phase 1 stub",
        "phase": "PHASE_1_STUB"
    }