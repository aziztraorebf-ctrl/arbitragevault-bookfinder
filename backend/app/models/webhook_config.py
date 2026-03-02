"""Webhook configuration model for external notification delivery."""

from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, JSONType


class WebhookConfig(Base):
    """
    Stores webhook configuration per user.

    Each user can have one webhook config that controls where
    notifications are sent when AutoSourcing jobs complete.
    """

    __tablename__ = "webhook_configs"

    # Target URL for webhook delivery (HTTPS endpoint)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    # HMAC signing secret for payload verification
    secret: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    # List of event types to subscribe to (e.g., ["autosourcing.job.completed"])
    event_types: Mapped[List] = mapped_column(JSONType, nullable=False, default=list)

    # Whether this webhook config is active
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Owner of this webhook config
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
