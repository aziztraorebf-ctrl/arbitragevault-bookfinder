"""
Recherches API Router - Centralized search results management.
Phase 11 - Mes Recherches feature.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.core.auth import get_current_user, CurrentUser
from app.services.search_result_service import SearchResultService
from app.schemas.search_result import (
    SearchResultCreate,
    SearchResultRead,
    SearchResultDetail,
    SearchResultUpdate,
    SearchResultListResponse,
    SearchSourceEnum
)

router = APIRouter(prefix="/recherches", tags=["recherches"])
logger = logging.getLogger(__name__)


def get_service(db: AsyncSession = Depends(get_db_session)) -> SearchResultService:
    """Dependency injection for SearchResultService."""
    return SearchResultService(db)


@router.post("", response_model=SearchResultRead, status_code=status.HTTP_201_CREATED)
async def create_search_result(
    data: SearchResultCreate,
    service: SearchResultService = Depends(get_service),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Save a new search result.

    - **name**: Name for this search
    - **source**: Source module (niche_discovery, autosourcing, manual_analysis)
    - **products**: Array of product data
    - **search_params**: Original search parameters
    - **notes**: Optional notes
    """
    try:
        result = await service.create(data)
        logger.info(f"User {current_user.email} created search result: {result.id}")
        return result
    except Exception as e:
        logger.error(f"Error creating search result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save search result: {str(e)}"
        )


@router.get("", response_model=SearchResultListResponse)
async def list_search_results(
    source: Optional[SearchSourceEnum] = Query(None, description="Filter by source"),
    limit: int = Query(50, ge=1, le=100, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: SearchResultService = Depends(get_service),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List all saved search results.

    - **source**: Optional filter by source module
    - **limit**: Maximum number of results (default 50, max 100)
    - **offset**: Pagination offset
    """
    results, total_count = await service.list_all(source=source, limit=limit, offset=offset)
    return SearchResultListResponse(results=results, total_count=total_count)


@router.get("/stats")
async def get_search_stats(
    service: SearchResultService = Depends(get_service),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get statistics about stored search results."""
    return await service.get_stats()


@router.get("/{result_id}", response_model=SearchResultDetail)
async def get_search_result(
    result_id: str,
    service: SearchResultService = Depends(get_service),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get a specific search result with full product data."""
    result = await service.get_by_id(result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search result {result_id} not found"
        )
    return result


@router.patch("/{result_id}", response_model=SearchResultRead)
async def update_search_result(
    result_id: str,
    data: SearchResultUpdate,
    service: SearchResultService = Depends(get_service),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update a search result (name or notes only)."""
    result = await service.update(result_id, data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search result {result_id} not found"
        )
    return result


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_search_result(
    result_id: str,
    service: SearchResultService = Depends(get_service),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete a search result."""
    deleted = await service.delete(result_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search result {result_id} not found"
        )


@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_expired_results(
    service: SearchResultService = Depends(get_service),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Manually trigger cleanup of expired search results.
    Normally runs automatically, but can be triggered manually.
    """
    deleted_count = await service.cleanup_expired()
    return {"deleted_count": deleted_count, "message": f"Cleaned up {deleted_count} expired results"}
