"""Batch endpoints for managing analysis batches."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.db import get_db_session
from app.core.pagination import PaginatedResponse, PaginationParams
from app.repositories.batch_repository import BatchRepository
from app.repositories.base_repository import SortOrder
from app.schemas.batch import BatchResponse, BatchStatusUpdate, BatchCreateRequest
from app.models.batch import Batch, BatchStatus

router = APIRouter()

# Configuration du logger pour les batches
logger = logging.getLogger("arbitragevault.batch")


@router.post("", status_code=201, response_model=BatchResponse)
async def create_batch(
    batch_request: BatchCreateRequest,
    db: AsyncSession = Depends(get_db_session)
) -> BatchResponse:
    """Create a new analysis batch in database."""
    
    try:
        # SQLAlchemy 2.0 + asyncpg: Verify session is active before use
        if not db.is_active:
            raise HTTPException(
                status_code=503,
                detail="Database session not active. Please retry."
            )
        
        repo = BatchRepository(db, Batch)
        
        # For now, use a default user ID (user auth will be added later)
        default_user_id = "default-user"
        
        batch = await repo.create_batch(
            user_id=default_user_id,
            name=batch_request.name,
            description=batch_request.description,
            items_total=len(batch_request.asin_list),
            strategy_snapshot={"config_name": batch_request.config_name}  # Store strategy config
        )
        
        # Log création batch avec succès
        logger.info(f"Batch créé avec succès: {batch.id}")
        
        return BatchResponse.model_validate(batch)
        
    except Exception as e:
        # Log l'erreur de création batch
        logger.error(f"Erreur lors de la création du batch: {str(e)}")
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
        # SQLAlchemy 2.0 + asyncpg: Verify session is active before use
        if not db.is_active:
            raise HTTPException(
                status_code=503,
                detail="Database session not active. Please retry."
            )
        
        repo = BatchRepository(db, Batch)
        
        # Get paginated batches (for now, get all user batches - user auth will be added later)
        batches = await repo.get_all(
            limit=pagination.per_page,
            offset=(pagination.page - 1) * pagination.per_page,
            sort_field="created_at",
            sort_order=SortOrder.DESC
        )
        
        # Count total batches
        total = await repo.count()
        
        # Convert to response models using from_attributes pattern
        batch_responses = []
        for batch in batches:
            batch_responses.append(BatchResponse.model_validate(batch))
        
        return PaginatedResponse(
            items=batch_responses,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve batches: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve batches: {str(e)}"
        )


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: str = Path(..., description="Batch ID"),
    db: AsyncSession = Depends(get_db_session)
) -> BatchResponse:
    """Get a specific batch by ID."""
    
    try:
        if not db.is_active:
            raise HTTPException(
                status_code=503,
                detail="Database session not active. Please retry."
            )
        
        repo = BatchRepository(db, Batch)
        batch = await repo.get_by_id(batch_id)
        
        if not batch:
            raise HTTPException(
                status_code=404,
                detail=f"Batch {batch_id} not found"
            )
        
        return BatchResponse.model_validate(batch)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch {batch_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batch: {str(e)}"
        )


@router.patch("/{batch_id}/status", response_model=BatchResponse)
async def update_batch_status(
    status_update: BatchStatusUpdate,
    batch_id: str = Path(..., description="Batch ID"),
    db: AsyncSession = Depends(get_db_session)
) -> BatchResponse:
    """Update batch status with validation."""
    
    try:
        if not db.is_active:
            raise HTTPException(
                status_code=503,
                detail="Database session not active. Please retry."
            )
        
        repo = BatchRepository(db, Batch)
        
        # Validate status value
        try:
            new_status = BatchStatus(status_update.status.upper())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status_update.status}. Must be one of: {[s.value for s in BatchStatus]}"
            )
        
        # Update batch status
        updated_batch = await repo.transition_status(
            batch_id=batch_id,
            new_status=new_status
        )
        
        if not updated_batch:
            raise HTTPException(
                status_code=404,
                detail=f"Batch {batch_id} not found"
            )
        
        logger.info(f"Batch {batch_id} status updated to {new_status.value}")
        
        return BatchResponse.model_validate(updated_batch)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update batch {batch_id} status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update batch status: {str(e)}"
        )