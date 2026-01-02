"""Pydantic schemas for SearchResult API."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class SearchSourceEnum(str, Enum):
    """Enum for search sources."""
    NICHE_DISCOVERY = "niche_discovery"
    AUTOSOURCING = "autosourcing"
    MANUAL_ANALYSIS = "manual_analysis"


class SearchResultCreate(BaseModel):
    """Schema for creating a new search result."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name for this search result"
    )

    source: SearchSourceEnum = Field(
        ...,
        description="Source module of the search"
    )

    products: List[Dict[str, Any]] = Field(
        ...,
        description="Array of product data"
    )

    search_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Original search parameters"
    )

    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional notes about this search"
    )

    @field_validator('name')
    def validate_name(cls, v):
        if v is None:
            raise ValueError('Name is required')
        stripped = v.strip()
        if not stripped:
            raise ValueError('Name cannot be empty')
        return stripped

    @field_validator('products')
    def validate_products(cls, v):
        if not isinstance(v, list):
            raise ValueError('Products must be a list')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Textbooks Analysis 2026-01-01",
                "source": "niche_discovery",
                "products": [
                    {"asin": "B08N5WRWNW", "title": "Example Book", "roi_percent": 35.5}
                ],
                "search_params": {"strategy": "textbook", "category": "Books"},
                "notes": "Good results from textbook strategy"
            }
        }


class SearchResultRead(BaseModel):
    """Schema for reading search result data."""

    id: str = Field(..., description="Unique search result ID")
    name: str = Field(..., description="Search name")
    source: str = Field(..., description="Source module")
    product_count: int = Field(..., description="Number of products")
    search_params: Dict[str, Any] = Field(..., description="Search parameters")
    notes: Optional[str] = Field(None, description="User notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")

    class Config:
        from_attributes = True


class SearchResultDetail(SearchResultRead):
    """Schema for detailed search result with products."""

    products: List[Dict[str, Any]] = Field(..., description="Product data array")

    class Config:
        from_attributes = True


class SearchResultListResponse(BaseModel):
    """Schema for listing search results."""

    results: List[SearchResultRead] = Field(..., description="List of search results")
    total_count: int = Field(..., description="Total number of results")

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Textbooks Analysis",
                        "source": "niche_discovery",
                        "product_count": 15,
                        "search_params": {},
                        "notes": None,
                        "created_at": "2026-01-01T10:30:00Z",
                        "expires_at": "2026-01-31T10:30:00Z"
                    }
                ],
                "total_count": 1
            }
        }


class SearchResultUpdate(BaseModel):
    """Schema for updating a search result."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated name"
    )

    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Updated notes"
    )

    @field_validator('name')
    def validate_name(cls, v):
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError('Name cannot be empty')
            return stripped
        return v
