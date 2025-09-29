"""Schemas for batch-related requests and responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from .base import TimestampedResponse


class BatchCreate(BaseModel):
    """Schema for creating a new batch."""
    name: str = Field(..., min_length=1, max_length=255, description="Batch name")
    description: Optional[str] = Field(None, max_length=1000, description="Batch description")


class BatchUpdate(BaseModel):
    """Schema for updating a batch."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Batch name")
    description: Optional[str] = Field(None, max_length=1000, description="Batch description")


class BatchSearch(BaseModel):
    """Schema for searching batches."""
    name: Optional[str] = Field(None, description="Search in batch name")
    status: Optional[str] = Field(None, description="Filter by status")
    user_id: Optional[str] = Field(None, description="Filter by user ID")


class BatchStatusUpdate(BaseModel):
    """Schema for updating batch status."""
    status: str = Field(..., description="New batch status")
    error_message: Optional[str] = Field(None, description="Error message if status is FAILED")


class BatchResponse(BaseModel):
    """Schema for batch responses."""
    id: str
    name: str
    description: Optional[str] = None
    status: str
    items_total: Optional[int] = None
    items_processed: Optional[int] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    strategy_snapshot: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    
    @property
    def progress_percentage(self) -> Optional[float]:
        """Calculate progress percentage."""
        if self.items_total and self.items_total > 0:
            processed = self.items_processed or 0
            return round((processed / self.items_total) * 100, 1)
        return None
    
    class Config:
        from_attributes = True


class BatchListResponse(BaseModel):
    """Schema for batch list responses."""
    items: List[BatchResponse]
    total: int
    page: int
    per_page: int
    pages: int


class BatchAnalysisStatus(BaseModel):
    """Schema for batch analysis status."""
    batch_id: str
    status: str
    items_total: int
    items_processed: int
    items_successful: int
    progress_percentage: float
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None