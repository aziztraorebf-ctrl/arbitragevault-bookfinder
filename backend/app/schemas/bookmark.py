"""Bookmark schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class NicheCreateSchema(BaseModel):
    """Schema for creating a new saved niche."""
    
    niche_name: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="User-defined name for the niche"
    )
    
    category_id: Optional[int] = Field(
        None,
        description="Keepa category ID used for discovery"
    )
    
    category_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Human-readable category name"
    )
    
    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Analysis parameters and filters used"
    )
    
    last_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Last calculated niche score"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional user notes about the niche"
    )

    @field_validator('niche_name')
    def validate_niche_name(cls, v):
        if not v.strip():
            raise ValueError('Niche name cannot be empty')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "niche_name": "Engineering Textbooks",
                "category_id": 13,
                "category_name": "Engineering & Transportation",
                "filters": {
                    "min_price": 20.0,
                    "max_price": 200.0,
                    "max_bsr": 500000,
                    "min_roi": 30.0
                },
                "last_score": 7.4,
                "description": "High-margin engineering textbooks with good rotation"
            }
        }


class NicheReadSchema(BaseModel):
    """Schema for reading saved niche data."""
    
    id: str = Field(..., description="Unique niche ID")
    niche_name: str = Field(..., description="User-defined niche name")
    category_id: Optional[int] = Field(None, description="Keepa category ID")
    category_name: Optional[str] = Field(None, description="Category name")
    filters: Dict[str, Any] = Field(..., description="Analysis parameters")
    last_score: Optional[float] = Field(None, description="Last niche score")
    description: Optional[str] = Field(None, description="User notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "niche_name": "Engineering Textbooks",
                "category_id": 13,
                "category_name": "Engineering & Transportation",
                "filters": {
                    "min_price": 20.0,
                    "max_price": 200.0,
                    "max_bsr": 500000,
                    "min_roi": 30.0
                },
                "last_score": 7.4,
                "description": "High-margin engineering textbooks",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class NicheUpdateSchema(BaseModel):
    """Schema for updating an existing saved niche."""
    
    niche_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated niche name"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Updated description"
    )
    
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated analysis parameters"
    )

    @field_validator('niche_name')
    def validate_niche_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Niche name cannot be empty')
        return v.strip() if v else v

    class Config:
        json_schema_extra = {
            "example": {
                "niche_name": "Updated Engineering Textbooks",
                "description": "Updated description with new insights",
                "filters": {
                    "min_price": 25.0,
                    "max_price": 250.0,
                    "max_bsr": 400000,
                    "min_roi": 35.0
                }
            }
        }


class NicheListResponseSchema(BaseModel):
    """Schema for listing user's saved niches."""
    
    niches: list[NicheReadSchema] = Field(..., description="List of saved niches")
    total_count: int = Field(..., description="Total number of saved niches")
    
    class Config:
        json_schema_extra = {
            "example": {
                "niches": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "niche_name": "Engineering Textbooks",
                        "category_id": 13,
                        "category_name": "Engineering & Transportation",
                        "filters": {"min_price": 20.0, "max_price": 200.0},
                        "last_score": 7.4,
                        "description": "High-margin textbooks",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total_count": 1
            }
        }