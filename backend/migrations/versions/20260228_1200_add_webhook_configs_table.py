"""Add webhook_configs table

Revision ID: 20260228_webhook
Revises: 20260110_firebase
Create Date: 2026-02-28 12:00:00

Webhook configuration table for external notification delivery when AutoSourcing jobs complete.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "20260228_webhook"
down_revision: Union[str, None] = "20260110_firebase"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "webhook_configs",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("secret", sa.String(255), nullable=False, server_default=""),
        sa.Column("event_types", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "user_id",
            UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Index on user_id for fast lookups
    op.create_index(
        "ix_webhook_configs_user_id",
        "webhook_configs",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_webhook_configs_user_id", table_name="webhook_configs")
    op.drop_table("webhook_configs")
