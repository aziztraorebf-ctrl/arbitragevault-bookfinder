"""Batch schemas for API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# from app.models.batch import BatchStatus  # Not needed for string validation


class BatchStatusUpdate(BaseModel):
    """Schema for updating batch status."""
    status: str = Field(..., description="New batch status")
    error_message: Optional[str] = Field(None, description="Error message if status is FAILED")


class BatchResponse(BaseModel):
    """Schema for batch responses."""
    id: str
    name: str
    status: str
    items_total: Optional[int]
    items_processed: Optional[int]
    items_successful: Optional[int]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str]
    
    @property
    def progress_percentage(self) -> Optional[float]:
        """Calculate progress percentage."""
        if self.items_total and self.items_total > 0:
            processed = self.items_processed or 0
            return round((processed / self.items_total) * 100, 1)
        return None
    
    class Config:
        from_attributes = True