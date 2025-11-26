"""add_velocity_score_check_constraints

Revision ID: 05a44b65f62b
Revises: 2f9f6ad2a720
Create Date: 2025-11-23 18:31:52.140893

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05a44b65f62b'
down_revision = '2f9f6ad2a720'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Clean invalid data before adding constraints
    op.execute("DELETE FROM analyses WHERE velocity_score < 0 OR velocity_score > 100")

    # Add CHECK constraints
    op.create_check_constraint(
        "check_velocity_score_min",
        "analyses",
        "velocity_score >= 0"
    )
    op.create_check_constraint(
        "check_velocity_score_max",
        "analyses",
        "velocity_score <= 100"
    )


def downgrade() -> None:
    op.drop_constraint("check_velocity_score_min", "analyses", type_="check")
    op.drop_constraint("check_velocity_score_max", "analyses", type_="check")