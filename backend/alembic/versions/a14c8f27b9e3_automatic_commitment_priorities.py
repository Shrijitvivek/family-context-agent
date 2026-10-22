"""Make commitment priorities automatic and optional for terminal items.

Revision ID: a14c8f27b9e3
Revises: c4d8a2f0916b
"""

from alembic import op
import sqlalchemy as sa


revision = "a14c8f27b9e3"
down_revision = "c4d8a2f0916b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE commitments SET priority = NULL "
        "WHERE status IN ('COMPLETED', 'CANCELLED')"
    )
    op.drop_column("commitments", "base_priority")
    op.alter_column(
        "commitments",
        "priority",
        existing_type=sa.String(length=30),
        nullable=True,
        server_default=None,
    )


def downgrade() -> None:
    op.execute(
        "UPDATE commitments SET priority = 'LOW' "
        "WHERE priority IS NULL"
    )
    op.alter_column(
        "commitments",
        "priority",
        existing_type=sa.String(length=30),
        nullable=False,
        server_default="MEDIUM",
    )
    op.add_column(
        "commitments",
        sa.Column(
            "base_priority",
            sa.String(length=30),
            nullable=False,
            server_default="MEDIUM",
        ),
    )
    op.execute("UPDATE commitments SET base_priority = priority")
