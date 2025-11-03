"""add saved_niches table for bookmarks

Revision ID: 008835e8f328
Revises: fix_scoring_cache_pk
Create Date: 2025-11-02 20:35:54.870570

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision = '008835e8f328'
down_revision = 'fix_scoring_cache_pk'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'saved_niches',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('niche_name', sa.String(255), nullable=False, index=True, comment='User-defined name for the niche'),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True, comment='ID of the user who saved this niche'),
        sa.Column('category_id', sa.Integer(), nullable=True, comment='Keepa category ID used for niche discovery'),
        sa.Column('category_name', sa.String(255), nullable=True, comment='Human-readable category name'),
        sa.Column('filters', JSONB, nullable=False, server_default='{}', comment='Complete analysis parameters'),
        sa.Column('last_score', sa.Float(), nullable=True, comment='Last calculated niche score'),
        sa.Column('description', sa.Text(), nullable=True, comment='Optional user notes'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index(
        'ix_saved_niches_user_created',
        'saved_niches',
        ['user_id', 'created_at'],
        postgresql_using='btree'
    )


def downgrade() -> None:
    op.drop_index('ix_saved_niches_user_created', table_name='saved_niches')
    op.drop_table('saved_niches')