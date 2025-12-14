"""Add saved_niches table

Revision ID: 20251214000001
Revises: 20251026111050
Create Date: 2025-12-14 00:00:01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20251214000001'
down_revision = '20251026111050'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create saved_niches table with proper constraints."""

    op.create_table(
        'saved_niches',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('niche_name', sa.String(255), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('category_name', sa.String(255), nullable=True),
        sa.Column('filters', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('last_score', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        # Primary key
        sa.PrimaryKeyConstraint('id'),

        # Foreign key with CASCADE delete
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE'
        ),

        # CRITICAL: Unique constraint to prevent duplicate niche names per user
        sa.UniqueConstraint('user_id', 'niche_name', name='uq_user_niche_name'),

        # CRITICAL: Check constraint to prevent empty niche names
        sa.CheckConstraint(
            "LENGTH(TRIM(niche_name)) > 0",
            name='ck_niche_name_not_empty'
        )
    )

    # Create indexes for performance
    op.create_index(
        op.f('ix_saved_niches_user_id'),
        'saved_niches',
        ['user_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_saved_niches_niche_name'),
        'saved_niches',
        ['niche_name'],
        unique=False
    )


def downgrade() -> None:
    """Drop saved_niches table."""

    op.drop_index(op.f('ix_saved_niches_niche_name'), table_name='saved_niches')
    op.drop_index(op.f('ix_saved_niches_user_id'), table_name='saved_niches')
    op.drop_table('saved_niches')
