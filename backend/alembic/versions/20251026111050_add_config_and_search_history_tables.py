"""Add config and search history tables

Revision ID: 20251026111050
Revises:
Create Date: 2025-10-26 11:10:50

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20251026111050'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create configuration and search history tables."""

    # Create configurations table
    op.create_table(
        'configurations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('fees', sa.JSON(), nullable=False),
        sa.Column('roi', sa.JSON(), nullable=False),
        sa.Column('velocity', sa.JSON(), nullable=False),
        sa.Column('data_quality', sa.JSON(), nullable=False),
        sa.Column('product_finder', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_configurations_name'), 'configurations', ['name'], unique=True)
    op.create_index(op.f('ix_configurations_is_active'), 'configurations', ['is_active'], unique=False)

    # Create category_overrides table
    op.create_table(
        'category_overrides',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('config_id', sa.String(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('category_name', sa.String(), nullable=False),
        sa.Column('fees', sa.JSON(), nullable=True),
        sa.Column('roi', sa.JSON(), nullable=True),
        sa.Column('velocity', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['config_id'], ['configurations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_category_overrides_category_id'), 'category_overrides', ['category_id'], unique=False)

    # Create users table if not exists (simplified for MVP)
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create search_history table
    op.create_table(
        'search_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('search_type', sa.String(), nullable=False),
        sa.Column('search_params', sa.JSON(), nullable=False),
        sa.Column('results_count', sa.Integer(), nullable=True),
        sa.Column('asins_found', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('keepa_tokens_used', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('cache_hit', sa.String(), nullable=True),
        sa.Column('asins_selected', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('asins_purchased', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_history_user_id'), 'search_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_search_history_search_type'), 'search_history', ['search_type'], unique=False)
    op.create_index(op.f('ix_search_history_created_at'), 'search_history', ['created_at'], unique=False)
    op.create_index(op.f('ix_search_history_expires_at'), 'search_history', ['expires_at'], unique=False)

    # Create saved_searches table
    op.create_table(
        'saved_searches',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('search_type', sa.String(), nullable=False),
        sa.Column('search_params', sa.JSON(), nullable=False),
        sa.Column('use_count', sa.Integer(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saved_searches_user_id'), 'saved_searches', ['user_id'], unique=False)


def downgrade() -> None:
    """Drop configuration and search history tables."""

    # Drop saved_searches
    op.drop_index(op.f('ix_saved_searches_user_id'), table_name='saved_searches')
    op.drop_table('saved_searches')

    # Drop search_history
    op.drop_index(op.f('ix_search_history_expires_at'), table_name='search_history')
    op.drop_index(op.f('ix_search_history_created_at'), table_name='search_history')
    op.drop_index(op.f('ix_search_history_search_type'), table_name='search_history')
    op.drop_index(op.f('ix_search_history_user_id'), table_name='search_history')
    op.drop_table('search_history')

    # Drop users
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Drop category_overrides
    op.drop_index(op.f('ix_category_overrides_category_id'), table_name='category_overrides')
    op.drop_table('category_overrides')

    # Drop configurations
    op.drop_index(op.f('ix_configurations_is_active'), table_name='configurations')
    op.drop_index(op.f('ix_configurations_name'), table_name='configurations')
    op.drop_table('configurations')