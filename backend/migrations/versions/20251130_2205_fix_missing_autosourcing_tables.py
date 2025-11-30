"""fix_missing_autosourcing_tables

CRITICAL FIX: Recreate tables that were incorrectly dropped by migration 2f9f6ad2a720.
The migration 2f9f6ad2a720 had upgrade/downgrade functions inversed for autosourcing tables.

Missing tables recreated:
- saved_profiles (required by autosourcing_jobs FK)
- autosourcing_jobs
- autosourcing_picks
- run_history
- asin_history (Phase 8.0 analytics)
- decision_outcomes (Phase 8.0 analytics)

Revision ID: fix_autosourcing_tables
Revises: 05a44b65f62b
Create Date: 2025-11-30 22:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'fix_autosourcing_tables'
down_revision = '05a44b65f62b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types first (if they don't exist)
    # Check and create jobstatus enum
    conn = op.get_bind()

    # Create jobstatus enum if not exists
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'jobstatus'"))
    if not result.fetchone():
        op.execute("CREATE TYPE jobstatus AS ENUM ('PENDING', 'RUNNING', 'SUCCESS', 'ERROR', 'CANCELLED')")

    # Create actionstatus enum if not exists
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'actionstatus'"))
    if not result.fetchone():
        op.execute("CREATE TYPE actionstatus AS ENUM ('PENDING', 'TO_BUY', 'FAVORITE', 'IGNORED', 'ANALYZING')")

    # 1. Create saved_profiles first (parent table for autosourcing_jobs FK)
    op.create_table('saved_profiles',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.VARCHAR(length=100), nullable=False),
        sa.Column('description', sa.TEXT(), nullable=True),
        sa.Column('discovery_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('scoring_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('max_results', sa.INTEGER(), server_default=sa.text('20'), nullable=False),
        sa.Column('active', sa.BOOLEAN(), server_default=sa.text('true'), nullable=False),
        sa.Column('last_used_at', postgresql.TIMESTAMP(), nullable=True),
        sa.Column('usage_count', sa.INTEGER(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='saved_profiles_pkey'),
        sa.UniqueConstraint('name', name='saved_profiles_name_key')
    )
    op.create_index('idx_saved_profiles_name', 'saved_profiles', ['name'], unique=False)
    op.create_index('idx_saved_profiles_active', 'saved_profiles', ['active'], unique=False)
    op.create_index('idx_saved_profiles_last_used', 'saved_profiles', ['last_used_at'], unique=False)
    op.create_index('idx_saved_profiles_created', 'saved_profiles', ['created_at'], unique=False)

    # 2. Create autosourcing_jobs (depends on saved_profiles)
    op.create_table('autosourcing_jobs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('profile_name', sa.VARCHAR(length=100), nullable=False),
        sa.Column('profile_id', sa.UUID(), nullable=True),
        sa.Column('launched_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', postgresql.TIMESTAMP(), nullable=True),
        sa.Column('duration_ms', sa.INTEGER(), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'RUNNING', 'SUCCESS', 'ERROR', 'CANCELLED', name='jobstatus', create_type=False), server_default=sa.text("'PENDING'::jobstatus"), nullable=False),
        sa.Column('total_tested', sa.INTEGER(), server_default=sa.text('0'), nullable=False),
        sa.Column('total_selected', sa.INTEGER(), server_default=sa.text('0'), nullable=False),
        sa.Column('discovery_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('scoring_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('error_message', sa.TEXT(), nullable=True),
        sa.Column('error_count', sa.INTEGER(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['saved_profiles.id'], name='autosourcing_jobs_profile_id_fkey', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='autosourcing_jobs_pkey')
    )
    op.create_index('idx_autosourcing_jobs_status', 'autosourcing_jobs', ['status'], unique=False)
    op.create_index('idx_autosourcing_jobs_profile_name', 'autosourcing_jobs', ['profile_name'], unique=False)
    op.create_index('idx_autosourcing_jobs_launched_at', 'autosourcing_jobs', ['launched_at'], unique=False)

    # 3. Create autosourcing_picks (depends on autosourcing_jobs)
    op.create_table('autosourcing_picks',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('asin', sa.VARCHAR(length=20), nullable=False),
        sa.Column('title', sa.VARCHAR(length=500), nullable=False),
        sa.Column('current_price', sa.DOUBLE_PRECISION(), nullable=True),
        sa.Column('estimated_buy_cost', sa.DOUBLE_PRECISION(), nullable=True),
        sa.Column('profit_net', sa.DOUBLE_PRECISION(), nullable=True),
        sa.Column('roi_percentage', sa.DOUBLE_PRECISION(), nullable=False),
        sa.Column('velocity_score', sa.INTEGER(), nullable=False),
        sa.Column('stability_score', sa.INTEGER(), nullable=False),
        sa.Column('confidence_score', sa.INTEGER(), nullable=False),
        sa.Column('overall_rating', sa.VARCHAR(length=20), nullable=False),
        sa.Column('bsr', sa.INTEGER(), nullable=True),
        sa.Column('category', sa.VARCHAR(length=100), nullable=True),
        sa.Column('readable_summary', sa.TEXT(), nullable=True),
        sa.Column('action_status', postgresql.ENUM('PENDING', 'TO_BUY', 'FAVORITE', 'IGNORED', 'ANALYZING', name='actionstatus', create_type=False), server_default=sa.text("'PENDING'::actionstatus"), nullable=False),
        sa.Column('action_taken_at', postgresql.TIMESTAMP(), nullable=True),
        sa.Column('action_notes', sa.TEXT(), nullable=True),
        sa.Column('is_purchased', sa.BOOLEAN(), server_default=sa.text('false'), nullable=False),
        sa.Column('is_favorite', sa.BOOLEAN(), server_default=sa.text('false'), nullable=False),
        sa.Column('is_ignored', sa.BOOLEAN(), server_default=sa.text('false'), nullable=False),
        sa.Column('analysis_requested', sa.BOOLEAN(), server_default=sa.text('false'), nullable=False),
        sa.Column('deep_analysis_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('priority_tier', sa.VARCHAR(length=10), server_default=sa.text("'WATCH'::character varying"), nullable=False),
        sa.Column('tier_reason', sa.TEXT(), nullable=True),
        sa.Column('is_featured', sa.BOOLEAN(), server_default=sa.text('false'), nullable=False),
        sa.Column('scheduler_run_id', sa.VARCHAR(length=50), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['autosourcing_jobs.id'], name='autosourcing_picks_job_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='autosourcing_picks_pkey')
    )
    op.create_index('idx_autosourcing_picks_job_id', 'autosourcing_picks', ['job_id'], unique=False)
    op.create_index('idx_autosourcing_picks_asin', 'autosourcing_picks', ['asin'], unique=False)
    op.create_index('idx_autosourcing_picks_roi', 'autosourcing_picks', ['roi_percentage'], unique=False)
    op.create_index('idx_autosourcing_picks_velocity', 'autosourcing_picks', ['velocity_score'], unique=False)
    op.create_index('idx_autosourcing_picks_stability', 'autosourcing_picks', ['stability_score'], unique=False)
    op.create_index('idx_autosourcing_picks_confidence', 'autosourcing_picks', ['confidence_score'], unique=False)
    op.create_index('idx_autosourcing_picks_overall_rating', 'autosourcing_picks', ['overall_rating'], unique=False)
    op.create_index('idx_autosourcing_picks_action_status', 'autosourcing_picks', ['action_status'], unique=False)
    op.create_index('idx_autosourcing_picks_is_purchased', 'autosourcing_picks', ['is_purchased'], unique=False)
    op.create_index('idx_autosourcing_picks_is_favorite', 'autosourcing_picks', ['is_favorite'], unique=False)
    op.create_index('idx_autosourcing_picks_is_ignored', 'autosourcing_picks', ['is_ignored'], unique=False)
    op.create_index('idx_autosourcing_picks_is_featured', 'autosourcing_picks', ['is_featured'], unique=False)
    op.create_index('idx_autosourcing_picks_priority_tier', 'autosourcing_picks', ['priority_tier'], unique=False)
    op.create_index('idx_autosourcing_picks_scheduler_run_id', 'autosourcing_picks', ['scheduler_run_id'], unique=False)
    op.create_index('idx_autosourcing_picks_created_at', 'autosourcing_picks', ['created_at'], unique=False)

    # 4. Create run_history (for AutoScheduler tracking)
    op.create_table('run_history',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('config_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('total_products_discovered', sa.INTEGER(), nullable=False),
        sa.Column('total_picks_generated', sa.INTEGER(), nullable=False),
        sa.Column('success_rate', sa.NUMERIC(precision=5, scale=2), nullable=True),
        sa.Column('tokens_consumed', sa.INTEGER(), server_default=sa.text('0'), nullable=False),
        sa.Column('execution_time_seconds', sa.DOUBLE_PRECISION(), nullable=True),
        sa.Column('executed_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='run_history_pkey')
    )
    op.create_index('idx_run_history_job_id', 'run_history', ['job_id'], unique=False)
    op.create_index('idx_run_history_executed_at', 'run_history', ['executed_at'], unique=False)

    # 5. Create asin_history (Phase 8.0 analytics - historical tracking)
    op.create_table('asin_history',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('asin', sa.VARCHAR(length=10), nullable=False),
        sa.Column('tracked_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('price', sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column('lowest_fba_price', sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column('bsr', sa.INTEGER(), nullable=True),
        sa.Column('seller_count', sa.INTEGER(), nullable=True),
        sa.Column('amazon_on_listing', sa.BOOLEAN(), nullable=True),
        sa.Column('fba_seller_count', sa.INTEGER(), nullable=True),
        sa.Column('extra_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='asin_history_pkey')
    )
    op.create_index('idx_asin_history_asin', 'asin_history', ['asin'], unique=False)
    op.create_index('idx_asin_history_tracked_at', 'asin_history', ['tracked_at'], unique=False)
    op.create_index('idx_asin_history_asin_tracked', 'asin_history', ['asin', 'tracked_at'], unique=False)

    # 6. Create decision_outcomes (Phase 8.0 analytics - decision tracking)
    op.create_table('decision_outcomes',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('asin', sa.VARCHAR(length=10), nullable=False),
        sa.Column('decision', sa.VARCHAR(length=20), nullable=False),
        sa.Column('predicted_roi', sa.NUMERIC(precision=5, scale=2), nullable=True),
        sa.Column('predicted_velocity', sa.NUMERIC(precision=5, scale=2), nullable=True),
        sa.Column('predicted_risk_score', sa.NUMERIC(precision=5, scale=2), nullable=True),
        sa.Column('actual_outcome', sa.VARCHAR(length=20), nullable=True),
        sa.Column('actual_roi', sa.NUMERIC(precision=5, scale=2), nullable=True),
        sa.Column('time_to_sell_days', sa.INTEGER(), nullable=True),
        sa.Column('outcome_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('notes', sa.TEXT(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='decision_outcomes_pkey')
    )
    op.create_index('idx_decision_outcome_asin', 'decision_outcomes', ['asin'], unique=False)
    op.create_index('idx_decision_outcome_decision', 'decision_outcomes', ['decision'], unique=False)
    op.create_index('idx_decision_outcome_created_at', 'decision_outcomes', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (children first)
    op.drop_index('idx_run_history_executed_at', table_name='run_history')
    op.drop_index('idx_run_history_job_id', table_name='run_history')
    op.drop_table('run_history')

    op.drop_index('idx_autosourcing_picks_created_at', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_scheduler_run_id', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_priority_tier', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_is_featured', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_is_ignored', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_is_favorite', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_is_purchased', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_action_status', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_overall_rating', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_confidence', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_stability', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_velocity', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_roi', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_asin', table_name='autosourcing_picks')
    op.drop_index('idx_autosourcing_picks_job_id', table_name='autosourcing_picks')
    op.drop_table('autosourcing_picks')

    op.drop_index('idx_autosourcing_jobs_launched_at', table_name='autosourcing_jobs')
    op.drop_index('idx_autosourcing_jobs_profile_name', table_name='autosourcing_jobs')
    op.drop_index('idx_autosourcing_jobs_status', table_name='autosourcing_jobs')
    op.drop_table('autosourcing_jobs')

    op.drop_index('idx_saved_profiles_created', table_name='saved_profiles')
    op.drop_index('idx_saved_profiles_last_used', table_name='saved_profiles')
    op.drop_index('idx_saved_profiles_active', table_name='saved_profiles')
    op.drop_index('idx_saved_profiles_name', table_name='saved_profiles')
    op.drop_table('saved_profiles')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS actionstatus")
    op.execute("DROP TYPE IF EXISTS jobstatus")
