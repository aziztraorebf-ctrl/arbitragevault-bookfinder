"""add discovery cache tables for phase 3

Revision ID: add_discovery_cache
Revises: d44da14df6c4
Create Date: 2025-10-27 10:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = 'add_discovery_cache'
down_revision = '2f821440fee5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Table 1: product_discovery_cache (TTL 24h)
    # Cache pour les résultats de découverte de produits
    op.create_table(
        'product_discovery_cache',
        sa.Column('cache_key', sa.String(255), primary_key=True),
        sa.Column('asins', postgresql.JSON, nullable=False, comment='Liste des ASINs découverts'),
        sa.Column('filters_applied', postgresql.JSON, nullable=True, comment='Filtres utilisés pour la recherche'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False, comment='TTL 24h par défaut'),
        sa.Column('hit_count', sa.Integer, default=0, nullable=False, comment='Nombre de fois que ce cache a été utilisé')
    )
    op.create_index('idx_discovery_expires_at', 'product_discovery_cache', ['expires_at'])
    op.create_index('idx_discovery_created_at', 'product_discovery_cache', ['created_at'])

    # Table 2: product_scoring_cache (TTL 6h)
    # Cache pour les scores ROI/Velocity calculés
    op.create_table(
        'product_scoring_cache',
        sa.Column('cache_key', sa.String(255), primary_key=True),
        sa.Column('asin', sa.String(20), nullable=False),
        sa.Column('roi_percent', sa.Float, nullable=False),
        sa.Column('velocity_score', sa.Float, nullable=False),
        sa.Column('recommendation', sa.String(50), nullable=False, comment='STRONG_BUY, BUY, CONSIDER, SKIP'),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('price', sa.Float, nullable=True),
        sa.Column('bsr', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False, comment='TTL 6h par défaut'),
        sa.Column('hit_count', sa.Integer, default=0, nullable=False)
    )
    op.create_index('idx_scoring_expires_at', 'product_scoring_cache', ['expires_at'])
    op.create_index('idx_scoring_asin', 'product_scoring_cache', ['asin'])
    op.create_index('idx_scoring_roi', 'product_scoring_cache', ['roi_percent'])
    op.create_index('idx_scoring_velocity', 'product_scoring_cache', ['velocity_score'])

    # Table 3: search_history (Analytics, pas de TTL)
    # Historique des recherches pour analytics
    op.create_table(
        'search_history',
        sa.Column('id', sa.String(36), primary_key=True, default=sa.func.gen_random_uuid()),
        sa.Column('user_id', sa.String(36), nullable=True, comment='Future auth - actuellement NULL'),
        sa.Column('search_type', sa.String(50), nullable=False, comment='discovery, scoring, autosourcing'),
        sa.Column('filters', postgresql.JSON, nullable=False, comment='Filtres appliqués'),
        sa.Column('results_count', sa.Integer, nullable=False),
        sa.Column('source', sa.String(50), nullable=True, comment='frontend, api, manual'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False)
    )
    op.create_index('idx_history_created_at', 'search_history', ['created_at'])
    op.create_index('idx_history_user_id', 'search_history', ['user_id'])
    op.create_index('idx_history_search_type', 'search_history', ['search_type'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_history_search_type', 'search_history')
    op.drop_index('idx_history_user_id', 'search_history')
    op.drop_index('idx_history_created_at', 'search_history')
    op.drop_table('search_history')

    op.drop_index('idx_scoring_velocity', 'product_scoring_cache')
    op.drop_index('idx_scoring_roi', 'product_scoring_cache')
    op.drop_index('idx_scoring_asin', 'product_scoring_cache')
    op.drop_index('idx_scoring_expires_at', 'product_scoring_cache')
    op.drop_table('product_scoring_cache')

    op.drop_index('idx_discovery_created_at', 'product_discovery_cache')
    op.drop_index('idx_discovery_expires_at', 'product_discovery_cache')
    op.drop_table('product_discovery_cache')