"""Pydantic schemas for Webhook configuration and payload."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class WebhookConfigCreate(BaseModel):
    url: HttpUrl
    secret: str = ""
    event_types: List[str] = Field(default_factory=lambda: ["autosourcing.job.completed"])
    active: bool = True


class WebhookConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    secret: str = ""
    event_types: List[str] = Field(default_factory=list)
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WebhookPayload(BaseModel):
    event: str
    timestamp: str
    data: Dict[str, Any] = Field(default_factory=dict)
