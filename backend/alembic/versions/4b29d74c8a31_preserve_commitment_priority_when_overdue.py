"""Preserve baseline priority while a commitment is overdue.

Revision ID: 4b29d74c8a31
Revises: 21e74b44cfea
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "4b29d74c8a31"
down_revision: str | None = "21e74b44cfea"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "commitments",
        sa.Column("priority_before_overdue", sa.String(length=30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("commitments", "priority_before_overdue")
