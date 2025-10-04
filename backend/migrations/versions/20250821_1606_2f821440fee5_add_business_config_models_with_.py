"""Add business config models with hierarchical overrides and audit trail

Revision ID: 2f821440fee5
Revises: 5e5eed2533e7
Create Date: 2025-08-21 16:06:09.355577

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json

# revision identifiers, used by Alembic.
revision = '2f821440fee5'
down_revision = '5e5eed2533e7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create business_config table
    op.create_table(
        'business_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('scope', sa.String(50), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['parent_id'], ['business_config.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        # Constraints
        sa.CheckConstraint(
            "(scope = 'global' AND id = 1) OR (scope != 'global')",
            name='single_global_config'
        ),
        sa.CheckConstraint(
            "scope ~ '^(global|domain:[0-9]+|category:[a-z_]+)$'",
            name='valid_scope_format'
        )
    )
    op.create_index(op.f('ix_business_config_scope'), 'business_config', ['scope'], unique=False)
    op.create_index(op.f('ix_business_config_parent_id'), 'business_config', ['parent_id'], unique=False)
    
    # Create config_changes table  
    op.create_table(
        'config_changes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('config_id', sa.Integer(), nullable=False),
        sa.Column('old_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('diff_jsonpatch', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('changed_by', sa.String(100), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('change_source', sa.String(20), nullable=False, default='api'),
        sa.Column('old_version', sa.Integer(), nullable=True),
        sa.Column('new_version', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['config_id'], ['business_config.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_config_changes_config_id'), 'config_changes', ['config_id'], unique=False)
    
    # Seed global configuration
    default_config = {
        "roi": {
            "target_pct_default": 30.0,
            "min_for_buy": 15.0,
            "excellent_threshold": 50.0,
            "good_threshold": 30.0,
            "fair_threshold": 15.0
        },
        "combined_score": {
            "roi_weight": 0.6,
            "velocity_weight": 0.4
        },
        "fees": {
            "buffer_pct_default": 5.0,
            "books": {
                "referral_fee_pct": 15.0,
                "closing_fee": 1.80,
                "fba_fee_base": 2.50,
                "fba_fee_per_lb": 0.40,
                "inbound_shipping": 0.40,
                "prep_fee": 0.20
            }
        },
        "velocity": {
            "fast_threshold": 80.0,
            "medium_threshold": 60.0,
            "slow_threshold": 40.0,
            "benchmarks": {
                "books": 100000,
                "media": 50000,
                "default": 150000
            }
        },
        "recommendation_rules": [
            {
                "label": "STRONG BUY",
                "min_roi": 30.0,
                "min_velocity": 70.0,
                "description": "High profit, fast moving"
            },
            {
                "label": "BUY",
                "min_roi": 20.0,
                "min_velocity": 50.0,
                "description": "Good opportunity"
            },
            {
                "label": "CONSIDER",
                "min_roi": 15.0,
                "min_velocity": 0.0,
                "description": "Monitor for better entry"
            },
            {
                "label": "PASS",
                "min_roi": 0.0,
                "min_velocity": 0.0,
                "description": "Low profit/slow moving"
            }
        ],
        "demo_asins": [
            "B00FLIJJSA",
            "B08N5WRWNW", 
            "B07FNW9FGJ"
        ],
        "meta": {
            "version": "1.0.0",
            "created_by": "migration_seed",
            "description": "Default business configuration seeded from migration"
        }
    }
    
    # Insert global config
    op.execute(
        sa.text("""
            INSERT INTO business_config (id, scope, data, version, description, is_active, created_at, updated_at)
            VALUES (1, 'global', :config_data, 1, 'Global business configuration', true, now(), now())
        """).bindparams(config_data=json.dumps(default_config))
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('config_changes')
    op.drop_table('business_config')