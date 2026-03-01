"""API key request/response schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CreateAPIKeyRequest(BaseModel):
    """Request to create a new API key."""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: List[str] = Field(default_factory=lambda: ["read"])
    expires_at: Optional[datetime] = None


class UpdateAPIKeyRequest(BaseModel):
    """Request to update an existing API key."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    scopes: Optional[List[str]] = None


class APIKeyResponse(BaseModel):
    """API key data response (without raw key)."""
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreatedResponse(BaseModel):
    """Response after creating an API key (includes raw key once)."""
    id: str
    name: str
    key_prefix: str
    raw_key: str
    scopes: List[str]
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyDeleteResponse(BaseModel):
    """Response after deleting an API key."""
    detail: str = "API key deleted successfully"
