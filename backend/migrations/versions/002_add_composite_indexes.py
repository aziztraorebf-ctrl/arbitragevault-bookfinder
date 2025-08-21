"""Add composite indexes for performance optimization.

Revision ID: 002
Revises: 001
Create Date: 2025-08-19 13:36:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002_add_composite_indexes'
down_revision = '4a0c777df81d'  # add_batch_and_analysis_tables
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add composite indexes for query optimization."""
    
    # Index for common filter patterns
    op.create_index(
        'idx_analyses_batch_roi',
        'analyses',
        ['batch_id', 'roi_percent'],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_analyses_batch_velocity',
        'analyses',
        ['batch_id', 'velocity_score'],
        postgresql_using='btree'
    )
    
    # Index for profit-based queries
    op.create_index(
        'idx_analyses_batch_profit',
        'analyses',
        ['batch_id', 'profit'],
        postgresql_using='btree'
    )
    
    # Index for multi-column sorting with stable tiebreak
    op.create_index(
        'idx_analyses_roi_id',
        'analyses',
        ['roi_percent', 'id'],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_analyses_velocity_id',
        'analyses',
        ['velocity_score', 'id'],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_analyses_profit_id',
        'analyses',
        ['profit', 'id'],
        postgresql_using='btree'
    )


def downgrade() -> None:
    """Remove composite indexes."""
    
    op.drop_index('idx_analyses_profit_id', table_name='analyses')
    op.drop_index('idx_analyses_velocity_id', table_name='analyses')
    op.drop_index('idx_analyses_roi_id', table_name='analyses')
    op.drop_index('idx_analyses_batch_profit', table_name='analyses')
    op.drop_index('idx_analyses_batch_velocity', table_name='analyses')
    op.drop_index('idx_analyses_batch_roi', table_name='analyses')