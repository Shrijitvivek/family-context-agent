"""Add missing notification fields.

Revision ID: 006f7b6834c3
Revises: YOUR_REVISION_ID
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "006f7b6834c3"
down_revision: str | None = "YOUR_REVISION_ID"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("priority", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("title", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=True,
            server_default="ACTIVE",
        ),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_notifications_family_commitment_active",
        "notifications",
        ["family_id", "commitment_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notifications_family_commitment_active",
        table_name="notifications",
    )
    op.drop_column("notifications", "resolved_at")
    op.drop_column("notifications", "status")
    op.drop_column("notifications", "title")
    op.drop_column("notifications", "priority")