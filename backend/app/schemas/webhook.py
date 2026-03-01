"""Pydantic schemas for Webhook configuration and payload."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class WebhookConfigCreate(BaseModel):
    url: HttpUrl
    secret: str = ""
    event_types: List[str] = Field(default_factory=lambda: ["autosourcing.job.completed"])
    active: bool = True


class WebhookConfigResponse(BaseModel):
    id: int
    url: str
    secret: str = ""
    event_types: List[str] = Field(default_factory=list)
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WebhookPayload(BaseModel):
    event: str
    timestamp: str
    data: Dict[str, Any] = Field(default_factory=dict)
