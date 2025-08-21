"""Pagination utilities and types."""

from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar('T')


class Page(BaseModel, Generic[T]):
    """Paginated response container."""
    
    # Allow arbitrary types (like SQLAlchemy models)
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