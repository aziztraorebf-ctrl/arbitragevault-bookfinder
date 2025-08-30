"""Batch schemas for API requests and responses."""

from datetime import datetime
from typing import Optional

from typing import List
from pydantic import BaseModel, Field, field_validator

# from app.models.batch import BatchStatus  # Not needed for string validation


class BatchCreateRequest(BaseModel):
    """Schema for creating new batches."""
    name: str = Field(..., description="Name for the batch")
    description: Optional[str] = Field(None, description="Optional batch description")
    asin_list: List[str] = Field(..., description="List of ISBN/ASIN codes to process")
    config_name: str = Field(..., description="Strategy configuration name")
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Valider que la description fait au moins 3 caractères si fournie."""
        if v is not None and len(v.strip()) < 3:
            raise ValueError("La description doit faire au moins 3 caractères")
        return v


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
    items_successful: Optional[int] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    
    @property
    def progress_percentage(self) -> Optional[float]:
        """Calculate progress percentage."""
        if self.items_total and self.items_total > 0:
            processed = self.items_processed or 0
            return round((processed / self.items_total) * 100, 1)
        return None
    
    class Config:
        from_attributes = True