"""fix_scoring_cache_schema

Revision ID: fix_scoring_cache_pk
Revises: 45d219e45e5a
Create Date: 2025-11-01 14:10:00.000000

Fixes mismatch between model and database schema:
- Model expects 'id' as primary key (autoincrement)
- Database has 'cache_key' as primary key
- Solution: Drop cache_key PK, add id column with autoincrement
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_scoring_cache_pk'
down_revision = '45d219e45e5a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Migrate product_scoring_cache to match model schema:
    1. Drop existing cache_key primary key
    2. Add id column as new primary key with autoincrement
    3. Add missing columns: keepa_data, config_hash, analysis_version
    """
    # Note: On production with data, you'd need to backup first
    # For now, we drop and recreate since cache is ephemeral

    # Drop old indexes
    op.drop_index('idx_scoring_expires_at', table_name='product_scoring_cache')
    op.drop_index('idx_scoring_asin', table_name='product_scoring_cache')
    op.drop_index('idx_scoring_roi', table_name='product_scoring_cache')
    op.drop_index('idx_scoring_velocity', table_name='product_scoring_cache')

    # Drop table and recreate with correct schema
    op.drop_table('product_scoring_cache')

    # Recreate with correct schema matching model
    op.create_table(
        'product_scoring_cache',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('asin', sa.String(20), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('bsr', sa.Integer(), nullable=False),
        sa.Column('roi_percent', sa.Float(), nullable=False),
        sa.Column('velocity_score', sa.Float(), nullable=False),
        sa.Column('recommendation', sa.String(50), nullable=False),
        sa.Column('keepa_data', sa.JSON(), nullable=True),
        sa.Column('config_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('analysis_version', sa.String(20), nullable=False, server_default='1.0')
    )

    # Recreate indexes
    op.create_index('idx_scoring_cache_asin_expiry', 'product_scoring_cache', ['asin', 'expires_at'])
    op.create_index('idx_scoring_cache_recommendation', 'product_scoring_cache', ['recommendation'])
    op.create_index('idx_scoring_cache_roi', 'product_scoring_cache', ['roi_percent'])


def downgrade() -> None:
    """
    Rollback to old schema with cache_key as primary key
    """
    # Drop new indexes
    op.drop_index('idx_scoring_cache_roi', table_name='product_scoring_cache')
    op.drop_index('idx_scoring_cache_recommendation', table_name='product_scoring_cache')
    op.drop_index('idx_scoring_cache_asin_expiry', table_name='product_scoring_cache')

    # Drop table and restore old schema
    op.drop_table('product_scoring_cache')

    # Restore old schema
    op.create_table(
        'product_scoring_cache',
        sa.Column('cache_key', sa.String(255), primary_key=True),
        sa.Column('asin', sa.String(20), nullable=False),
        sa.Column('roi_percent', sa.Float(), nullable=False),
        sa.Column('velocity_score', sa.Float(), nullable=False),
        sa.Column('recommendation', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('bsr', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('hit_count', sa.Integer(), default=0, nullable=False)
    )

    # Restore old indexes
    op.create_index('idx_scoring_expires_at', 'product_scoring_cache', ['expires_at'])
    op.create_index('idx_scoring_asin', 'product_scoring_cache', ['asin'])
    op.create_index('idx_scoring_roi', 'product_scoring_cache', ['roi_percent'])
    op.create_index('idx_scoring_velocity', 'product_scoring_cache', ['velocity_score'])
