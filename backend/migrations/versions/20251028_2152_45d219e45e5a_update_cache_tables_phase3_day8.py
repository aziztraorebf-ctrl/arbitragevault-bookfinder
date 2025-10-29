"""update_cache_tables_phase3_day8

Revision ID: 45d219e45e5a
Revises: add_discovery_cache
Create Date: 2025-10-28 21:52:06.836245

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '45d219e45e5a'
down_revision = 'add_discovery_cache'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # product_discovery_cache: Replace filters_applied with individual columns
    op.drop_column('product_discovery_cache', 'filters_applied')
    op.add_column('product_discovery_cache', sa.Column('domain', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('product_discovery_cache', sa.Column('category', sa.Integer(), nullable=True))
    op.add_column('product_discovery_cache', sa.Column('bsr_min', sa.Integer(), nullable=True))
    op.add_column('product_discovery_cache', sa.Column('bsr_max', sa.Integer(), nullable=True))
    op.add_column('product_discovery_cache', sa.Column('price_min', sa.Float(), nullable=True))
    op.add_column('product_discovery_cache', sa.Column('price_max', sa.Float(), nullable=True))
    op.add_column('product_discovery_cache', sa.Column('count', sa.Integer(), nullable=False, server_default='0'))

    # Remove server defaults after column creation
    op.alter_column('product_discovery_cache', 'domain', server_default=None)
    op.alter_column('product_discovery_cache', 'count', server_default=None)


def downgrade() -> None:
    # Rollback: Restore old structure
    op.drop_column('product_discovery_cache', 'count')
    op.drop_column('product_discovery_cache', 'price_max')
    op.drop_column('product_discovery_cache', 'price_min')
    op.drop_column('product_discovery_cache', 'bsr_max')
    op.drop_column('product_discovery_cache', 'bsr_min')
    op.drop_column('product_discovery_cache', 'category')
    op.drop_column('product_discovery_cache', 'domain')
    op.add_column('product_discovery_cache', sa.Column('filters_applied', sa.JSON(), nullable=True))