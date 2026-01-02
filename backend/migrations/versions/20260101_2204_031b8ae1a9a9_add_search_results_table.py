"""add_search_results_table

Revision ID: 031b8ae1a9a9
Revises: add_competition_fields
Create Date: 2026-01-01 22:04:47.503254

Phase 11 - Centralized search results storage.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '031b8ae1a9a9'
down_revision = 'add_competition_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'search_results',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('source', sa.String(50), nullable=False, index=True),
        sa.Column('search_params', JSONB, nullable=False, server_default='{}'),
        sa.Column('products', JSONB, nullable=False, server_default='[]'),
        sa.Column('product_count', sa.Integer, nullable=False, default=0),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Composite index for common queries
    op.create_index(
        'ix_search_results_source_created',
        'search_results',
        ['source', 'created_at']
    )


def downgrade() -> None:
    op.drop_index('ix_search_results_source_created', table_name='search_results')
    op.drop_table('search_results')
