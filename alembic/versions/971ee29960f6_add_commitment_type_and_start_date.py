"""add commitment type and start date

Revision ID: 971ee29960f6
Revises: bf4ca76fe433
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "971ee29960f6"
down_revision = "bf4ca76fe433"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "commitments",
        sa.Column(
            "commitment_type",
            sa.String(length=50),
            nullable=True,
            server_default="BILL",
        ),
    )

    op.add_column(
        "commitments",
        sa.Column(
            "start_date",
            sa.Date(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("commitments", "start_date")
    op.drop_column("commitments", "commitment_type")