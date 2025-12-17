"""add_competition_fields_to_autosourcing_picks

Phase 7 Audit Fix: Add fba_seller_count and amazon_on_listing columns
to track competition data in AutoSourcing picks.

Revision ID: add_competition_fields
Revises: fix_autosourcing_tables
Create Date: 2025-12-16 21:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_competition_fields'
down_revision = 'fix_autosourcing_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add competition tracking columns to autosourcing_picks
    # Phase 7: Same data as Phase 6 Niche Discovery
    op.add_column(
        'autosourcing_picks',
        sa.Column('fba_seller_count', sa.Integer(), nullable=True,
                  comment='Number of FBA sellers on the listing')
    )
    op.add_column(
        'autosourcing_picks',
        sa.Column('amazon_on_listing', sa.Boolean(), nullable=True,
                  comment='True if Amazon sells this product directly')
    )


def downgrade() -> None:
    op.drop_column('autosourcing_picks', 'amazon_on_listing')
    op.drop_column('autosourcing_picks', 'fba_seller_count')
