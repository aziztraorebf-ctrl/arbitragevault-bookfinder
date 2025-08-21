"""Pagination utilities and types."""

from typing import Generic, List, TypeVar, Optional
from fastapi import Query
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response container."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    items: List[T] = Field(..., description="List of items in this page")
    total: int = Field(..., description="Total number of items across all pages", ge=0)
    page: int = Field(..., description="Current page number", ge=1)
    per_page: int = Field(..., description="Items per page", ge=1)
    pages: int = Field(..., description="Total number of pages", ge=0)


class PaginationParams:
    """Pagination parameters dependency."""
    
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page"),
        sort_by: str = Query("id", description="Sort by field"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
    ):
        self.page = page
        self.per_page = per_page
        self.sort_by = sort_by
        self.sort_order = sort_order
        
    @property
    def offset(self) -> int:
        """Calculate offset from page and per_page."""
        return (self.page - 1) * self.per_page
        
    @property
    def limit(self) -> int:
        """Get limit (per_page)."""
        return self.per_page


class Page(BaseModel, Generic[T]):
    """Legacy paginated response container (kept for compatibility)."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    items: List[T] = Field(..., description="List of items in this page")
    total: int = Field(..., description="Total number of items across all pages", ge=0)
    offset: int = Field(..., description="Number of items skipped", ge=0)
    limit: int = Field(..., description="Maximum number of items per page", gt=0)
    has_next: bool = Field(..., description="Whether there are more pages after this one")
    has_prev: bool = Field(..., description="Whether there are pages before this one")

    @classmethod
    def create(cls, items: List[T], total: int, offset: int, limit: int) -> "Page[T]":
        """Create a Page instance with computed has_next/has_prev flags."""
        has_next = offset + len(items) < total
        has_prev = offset > 0
        
        return cls(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
            has_next=has_next,
            has_prev=has_prev
        )