"""merge_autocloud_migrations

Revision ID: bd5d376117d0
Revises: 20260228_apikeys, add_condition_fields, 20260228_webhook
Create Date: 2026-03-02 09:47:32.392576

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bd5d376117d0"
down_revision = ("20260228_apikeys", "add_condition_fields", "20260228_webhook")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
