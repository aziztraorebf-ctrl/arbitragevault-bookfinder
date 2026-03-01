"""add_condition_fields_to_autosourcing_picks

Add used_price, used_offer_count, used_roi_percentage, and condition_signal
columns to autosourcing_picks for condition-based scoring signals.

Revision ID: add_condition_fields
Revises: 20260110_firebase
Create Date: 2026-02-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_condition_fields'
down_revision = '20260110_firebase'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'autosourcing_picks',
        sa.Column('used_price', sa.Float(), nullable=True,
                  comment='Current used price from Keepa stats.current[2]')
    )
    op.add_column(
        'autosourcing_picks',
        sa.Column('used_offer_count', sa.Integer(), nullable=True,
                  comment='Number of used offers from Keepa stats.offerCountUsed')
    )
    op.add_column(
        'autosourcing_picks',
        sa.Column('used_roi_percentage', sa.Float(), nullable=True,
                  comment='ROI percentage calculated at used condition price')
    )
    op.add_column(
        'autosourcing_picks',
        sa.Column('condition_signal', sa.String(20), nullable=True,
                  comment='Derived condition signal: STRONG, MODERATE, WEAK, or UNKNOWN')
    )


def downgrade() -> None:
    op.drop_column('autosourcing_picks', 'condition_signal')
    op.drop_column('autosourcing_picks', 'used_roi_percentage')
    op.drop_column('autosourcing_picks', 'used_offer_count')
    op.drop_column('autosourcing_picks', 'used_price')
