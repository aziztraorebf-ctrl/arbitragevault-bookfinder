"""
Service layer for SearchResult operations.
Phase 11 - Centralized search result management.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search_result import SearchResult, SearchSource
from app.schemas.search_result import (
    SearchResultCreate,
    SearchResultUpdate,
    SearchSourceEnum
)

logger = logging.getLogger(__name__)


class SearchResultService:
    """Service for managing search results."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_duplicate(
        self,
        name: str,
        source: SearchSourceEnum
    ) -> Optional[SearchResult]:
        """
        Check if a search result with same name and source exists.
        Returns the existing result if found, None otherwise.
        """
        now = datetime.utcnow()
        query = select(SearchResult).where(
            SearchResult.name == name,
            SearchResult.source == source.value,
            SearchResult.expires_at > now
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        data: SearchResultCreate,
        allow_duplicate: bool = False
    ) -> SearchResult:
        """
        Create a new search result.

        Args:
            data: Search result data
            allow_duplicate: If False, raises ValueError if duplicate exists
        """
        # Check for duplicates unless explicitly allowed
        if not allow_duplicate:
            existing = await self.check_duplicate(data.name, data.source)
            if existing:
                logger.warning(
                    f"Duplicate search result found: name='{data.name}', source='{data.source.value}'"
                )
                raise ValueError(
                    f"A search result with name '{data.name}' from {data.source.value} already exists. "
                    f"Use a different name or delete the existing one."
                )

        search_result = SearchResult.create_from_results(
            name=data.name,
            source=SearchSource(data.source.value),
            products=data.products,
            search_params=data.search_params,
            notes=data.notes
        )

        self.db.add(search_result)
        await self.db.commit()
        await self.db.refresh(search_result)

        logger.info(f"Created search result: {search_result.id} with {search_result.product_count} products")
        return search_result

    async def get_by_id(self, result_id: str) -> Optional[SearchResult]:
        """Get a search result by ID."""
        query = select(SearchResult).where(SearchResult.id == result_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        source: Optional[SearchSourceEnum] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[SearchResult], int]:
        """
        List search results with optional source filter.
        Returns (results, total_count).
        """
        # Base query
        query = select(SearchResult).order_by(SearchResult.created_at.desc())
        count_query = select(func.count(SearchResult.id))

        # Filter by source if provided
        if source:
            query = query.where(SearchResult.source == source.value)
            count_query = count_query.where(SearchResult.source == source.value)

        # Filter out expired results
        now = datetime.utcnow()
        query = query.where(SearchResult.expires_at > now)
        count_query = count_query.where(SearchResult.expires_at > now)

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute queries
        results = await self.db.execute(query)
        count_result = await self.db.execute(count_query)

        return list(results.scalars().all()), count_result.scalar() or 0

    async def update(self, result_id: str, data: SearchResultUpdate) -> Optional[SearchResult]:
        """Update a search result."""
        search_result = await self.get_by_id(result_id)
        if not search_result:
            return None

        if data.name is not None:
            search_result.name = data.name
        if data.notes is not None:
            search_result.notes = data.notes

        await self.db.commit()
        await self.db.refresh(search_result)

        logger.info(f"Updated search result: {result_id}")
        return search_result

    async def delete(self, result_id: str) -> bool:
        """Delete a search result."""
        search_result = await self.get_by_id(result_id)
        if not search_result:
            return False

        await self.db.delete(search_result)
        await self.db.commit()

        logger.info(f"Deleted search result: {result_id}")
        return True

    async def cleanup_expired(self) -> int:
        """
        Delete expired search results.
        Returns number of deleted records.
        """
        now = datetime.utcnow()
        query = delete(SearchResult).where(SearchResult.expires_at <= now)
        result = await self.db.execute(query)
        await self.db.commit()

        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired search results")

        return deleted_count

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored search results."""
        now = datetime.utcnow()

        # Count by source
        stats = {}
        for source in SearchSource:
            count_query = select(func.count(SearchResult.id)).where(
                SearchResult.source == source.value,
                SearchResult.expires_at > now
            )
            result = await self.db.execute(count_query)
            stats[source.value] = result.scalar() or 0

        # Total count
        total_query = select(func.count(SearchResult.id)).where(
            SearchResult.expires_at > now
        )
        total_result = await self.db.execute(total_query)
        stats['total'] = total_result.scalar() or 0

        return stats
