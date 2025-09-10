"""API routes for managing user bookmarked niches."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..core.db import get_db_session as get_db
from ..core.auth import get_current_user_id
from ..services.bookmark_service import BookmarkService
from ..schemas.bookmark import (
    NicheCreateSchema,
    NicheReadSchema,
    NicheUpdateSchema,
    NicheListResponseSchema
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/bookmarks",
    tags=["Bookmarks"],
    responses={404: {"description": "Not found"}}
)


@router.post("/niches", response_model=NicheReadSchema, status_code=status.HTTP_201_CREATED)
async def create_saved_niche(
    niche_data: NicheCreateSchema,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new saved niche for the current user.
    
    This endpoint allows users to bookmark discovered niches with their analysis
    parameters for later re-use.
    """
    try:
        bookmark_service = BookmarkService(db)
        saved_niche = bookmark_service.create_niche(current_user_id, niche_data)
        
        logger.info(f"User {current_user_id} created saved niche: {saved_niche.niche_name}")
        return NicheReadSchema.from_orm(saved_niche)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating saved niche: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create saved niche"
        )


@router.get("/niches", response_model=NicheListResponseSchema)
async def list_saved_niches(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get all saved niches for the current user.
    
    Returns a paginated list of the user's bookmarked niches, ordered by 
    creation date (newest first).
    """
    try:
        bookmark_service = BookmarkService(db)
        niches, total_count = bookmark_service.list_niches_by_user(
            current_user_id, skip, limit
        )
        
        niches_data = [NicheReadSchema.from_orm(niche) for niche in niches]
        
        logger.info(f"User {current_user_id} retrieved {len(niches)} saved niches")
        return NicheListResponseSchema(
            niches=niches_data,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Error listing saved niches for user {current_user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve saved niches"
        )


@router.get("/niches/{niche_id}", response_model=NicheReadSchema)
async def get_saved_niche(
    niche_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get a specific saved niche by ID.
    
    Returns the complete details of a saved niche including all analysis
    parameters for potential re-analysis.
    """
    try:
        bookmark_service = BookmarkService(db)
        niche = bookmark_service.get_niche_by_id(current_user_id, niche_id)
        
        if not niche:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved niche not found"
            )
        
        logger.info(f"User {current_user_id} retrieved saved niche: {niche.niche_name}")
        return NicheReadSchema.from_orm(niche)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving saved niche {niche_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve saved niche"
        )


@router.put("/niches/{niche_id}", response_model=NicheReadSchema)
async def update_saved_niche(
    niche_id: str,
    niche_data: NicheUpdateSchema,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update an existing saved niche.
    
    Allows users to modify the name, description, or analysis parameters
    of their saved niches.
    """
    try:
        bookmark_service = BookmarkService(db)
        updated_niche = bookmark_service.update_niche(
            current_user_id, niche_id, niche_data
        )
        
        if not updated_niche:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved niche not found"
            )
        
        logger.info(f"User {current_user_id} updated saved niche: {updated_niche.niche_name}")
        return NicheReadSchema.from_orm(updated_niche)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating saved niche {niche_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update saved niche"
        )


@router.delete("/niches/{niche_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_niche(
    niche_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete a saved niche.
    
    Permanently removes a bookmarked niche from the user's saved collection.
    This action cannot be undone.
    """
    try:
        bookmark_service = BookmarkService(db)
        deleted = bookmark_service.delete_niche(current_user_id, niche_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved niche not found"
            )
        
        logger.info(f"User {current_user_id} deleted saved niche: {niche_id}")
        return  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting saved niche {niche_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete saved niche"
        )


@router.get("/niches/{niche_id}/filters")
async def get_niche_analysis_filters(
    niche_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get the analysis filters from a saved niche for re-running analysis.
    
    This endpoint is useful for the "Relancer l'analyse" functionality,
    returning the exact parameters used when the niche was discovered.
    """
    try:
        bookmark_service = BookmarkService(db)
        filters = bookmark_service.get_niche_filters_for_analysis(
            current_user_id, niche_id
        )
        
        if filters is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved niche not found"
            )
        
        logger.info(f"User {current_user_id} retrieved filters for niche: {niche_id}")
        return {"filters": filters}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving filters for niche {niche_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve niche filters"
        )