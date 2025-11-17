"""Phase 8.0 Advanced Analytics tables - ASIN history, run history, decision outcomes

Revision ID: phase_8_0_analytics
Revises: 008835e8f328
Create Date: 2025-11-16 21:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'phase_8_0_analytics'
down_revision = '008835e8f328'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'asin_history',
        sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('asin', sa.String(length=10), nullable=False),
        sa.Column('tracked_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('lowest_fba_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('bsr', sa.Integer(), nullable=True),
        sa.Column('seller_count', sa.Integer(), nullable=True),
        sa.Column('amazon_on_listing', sa.Boolean(), nullable=True),
        sa.Column('fba_seller_count', sa.Integer(), nullable=True),
        sa.Column('extra_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_asin_history_asin_tracked', 'asin_history', ['asin', 'tracked_at'])
    op.create_index('idx_asin_history_tracked_at', 'asin_history', ['tracked_at'])
    op.create_index(op.f('ix_asin_history_asin'), 'asin_history', ['asin'])

    op.create_table(
        'run_history',
        sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('job_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('config_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('total_products_discovered', sa.Integer(), nullable=False),
        sa.Column('total_picks_generated', sa.Integer(), nullable=False),
        sa.Column('success_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('tokens_consumed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('execution_time_seconds', sa.Float(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_run_history_job_id', 'run_history', ['job_id'])
    op.create_index('idx_run_history_executed_at', 'run_history', ['executed_at'])

    op.create_table(
        'decision_outcomes',
        sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('asin', sa.String(length=10), nullable=False),
        sa.Column('decision', sa.String(length=20), nullable=False),
        sa.Column('predicted_roi', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('predicted_velocity', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('predicted_risk_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('actual_outcome', sa.String(length=20), nullable=True),
        sa.Column('actual_roi', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('time_to_sell_days', sa.Integer(), nullable=True),
        sa.Column('outcome_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_decision_outcome_asin', 'decision_outcomes', ['asin'])
    op.create_index('idx_decision_outcome_decision', 'decision_outcomes', ['decision'])
    op.create_index('idx_decision_outcome_created_at', 'decision_outcomes', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_decision_outcome_created_at', table_name='decision_outcomes')
    op.drop_index('idx_decision_outcome_decision', table_name='decision_outcomes')
    op.drop_index('idx_decision_outcome_asin', table_name='decision_outcomes')
    op.drop_table('decision_outcomes')

    op.drop_index('idx_run_history_executed_at', table_name='run_history')
    op.drop_index('idx_run_history_job_id', table_name='run_history')
    op.drop_table('run_history')

    op.drop_index(op.f('ix_asin_history_asin'), table_name='asin_history')
    op.drop_index('idx_asin_history_tracked_at', table_name='asin_history')
    op.drop_index('idx_asin_history_asin_tracked', table_name='asin_history')
    op.drop_table('asin_history')
