"""Add firebase_uid to users table

Revision ID: 20260110_firebase
Revises: 20251214000001
Create Date: 2026-01-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260110_firebase"
down_revision: Union[str, None] = "20251214000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add firebase_uid column
    op.add_column(
        "users",
        sa.Column("firebase_uid", sa.String(128), nullable=True)
    )

    # Create unique index on firebase_uid
    op.create_index(
        "ix_users_firebase_uid",
        "users",
        ["firebase_uid"],
        unique=True
    )

    # Make password_hash nullable (for Firebase-only users)
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.Text(),
        nullable=True
    )


def downgrade() -> None:
    # Remove index
    op.drop_index("ix_users_firebase_uid", table_name="users")

    # Remove firebase_uid column
    op.drop_column("users", "firebase_uid")

    # Revert password_hash to non-nullable
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.Text(),
        nullable=False
    )
