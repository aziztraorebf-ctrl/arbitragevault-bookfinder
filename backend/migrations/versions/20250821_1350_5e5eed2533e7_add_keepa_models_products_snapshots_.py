"""Add Keepa models: products, snapshots, calc_metrics, identifier_log

Revision ID: 5e5eed2533e7
Revises: 002_add_composite_indexes
Create Date: 2025-08-21 13:50:19.887233

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5e5eed2533e7'
down_revision = '002_add_composite_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create keepa_products table
    op.create_table(
        'keepa_products',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('asin', sa.String(10), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('brand', sa.String(200), nullable=True),
        sa.Column('manufacturer', sa.String(200), nullable=True),
        sa.Column('package_height', sa.Numeric(10, 2), nullable=True),
        sa.Column('package_length', sa.Numeric(10, 2), nullable=True),
        sa.Column('package_width', sa.Numeric(10, 2), nullable=True),
        sa.Column('package_weight', sa.Numeric(10, 3), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('domain', sa.Integer(), nullable=False, default=1),
        sa.Column('original_identifier', sa.String(20), nullable=True),
        sa.Column('identifier_type', sa.String(10), nullable=True),
        sa.Column('last_keepa_sync', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asin')
    )
    op.create_index(op.f('ix_keepa_products_asin'), 'keepa_products', ['asin'], unique=True)
    
    # Create keepa_snapshots table
    op.create_table(
        'keepa_snapshots',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data_window_days', sa.Integer(), nullable=False, default=30),
        sa.Column('current_buybox_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('current_amazon_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('current_fba_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('current_fbm_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('current_bsr', sa.Integer(), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metrics_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('offers_count', sa.Integer(), nullable=True),
        sa.Column('buybox_seller_type', sa.String(20), nullable=True),
        sa.Column('is_prime_eligible', sa.String(10), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['keepa_products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_keepa_snapshots_product_id'), 'keepa_snapshots', ['product_id'], unique=False)
    op.create_index(op.f('ix_keepa_snapshots_snapshot_date'), 'keepa_snapshots', ['snapshot_date'], unique=False)
    op.create_index(op.f('ix_keepa_snapshots_current_bsr'), 'keepa_snapshots', ['current_bsr'], unique=False)
    
    # Create calc_metrics table
    op.create_table(
        'calc_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('snapshot_id', sa.String(), nullable=True),
        sa.Column('estimated_sell_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('estimated_buy_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('amazon_fees_total', sa.Numeric(10, 2), nullable=True),
        sa.Column('net_profit', sa.Numeric(10, 2), nullable=True),
        sa.Column('roi_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('margin_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('referral_fee', sa.Numeric(8, 2), nullable=True),
        sa.Column('closing_fee', sa.Numeric(8, 2), nullable=True),
        sa.Column('fba_fee', sa.Numeric(8, 2), nullable=True),
        sa.Column('inbound_shipping', sa.Numeric(8, 2), nullable=True),
        sa.Column('prep_fee', sa.Numeric(8, 2), nullable=True),
        sa.Column('target_buy_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('breakeven_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('velocity_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('rank_percentile_30d', sa.Numeric(5, 2), nullable=True),
        sa.Column('rank_drops_30d', sa.Integer(), nullable=True),
        sa.Column('buybox_uptime_30d', sa.Numeric(5, 2), nullable=True),
        sa.Column('offers_volatility', sa.Numeric(5, 2), nullable=True),
        sa.Column('demand_consistency', sa.Numeric(5, 2), nullable=True),
        sa.Column('price_volatility', sa.Numeric(5, 2), nullable=True),
        sa.Column('competition_level', sa.Numeric(5, 2), nullable=True),
        sa.Column('fee_config_used', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('calculation_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('calculation_version', sa.String(10), nullable=False, default='1.0'),
        sa.ForeignKeyConstraint(['product_id'], ['keepa_products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['snapshot_id'], ['keepa_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calc_metrics_product_id'), 'calc_metrics', ['product_id'], unique=False)
    op.create_index(op.f('ix_calc_metrics_snapshot_id'), 'calc_metrics', ['snapshot_id'], unique=False)
    op.create_index(op.f('ix_calc_metrics_net_profit'), 'calc_metrics', ['net_profit'], unique=False)
    op.create_index(op.f('ix_calc_metrics_roi_percentage'), 'calc_metrics', ['roi_percentage'], unique=False)
    op.create_index(op.f('ix_calc_metrics_velocity_score'), 'calc_metrics', ['velocity_score'], unique=False)
    
    # Create identifier_resolution_log table
    op.create_table(
        'identifier_resolution_log',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('original_identifier', sa.String(20), nullable=False),
        sa.Column('identifier_type', sa.String(10), nullable=False),
        sa.Column('resolved_asin', sa.String(10), nullable=True),
        sa.Column('resolution_status', sa.String(20), nullable=False),
        sa.Column('keepa_product_code', sa.Integer(), nullable=True),
        sa.Column('keepa_domain', sa.Integer(), nullable=False, default=1),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('attempted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_identifier_resolution_log_original_identifier'), 'identifier_resolution_log', ['original_identifier'], unique=False)
    op.create_index(op.f('ix_identifier_resolution_log_resolved_asin'), 'identifier_resolution_log', ['resolved_asin'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('identifier_resolution_log')
    op.drop_table('calc_metrics')
    op.drop_table('keepa_snapshots')
    op.drop_table('keepa_products')