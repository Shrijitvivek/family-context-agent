"""store user-selected commitment priority separately

Revision ID: c4d8a2f0916b
Revises: 4b29d74c8a31
"""

from alembic import op
import sqlalchemy as sa


revision = "c4d8a2f0916b"
down_revision = "4b29d74c8a31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "commitments",
        sa.Column("base_priority", sa.String(length=30), nullable=True),
    )
    op.execute("UPDATE commitments SET base_priority = priority")
    op.alter_column(
        "commitments",
        "base_priority",
        existing_type=sa.String(length=30),
        nullable=False,
        server_default="MEDIUM",
    )


def downgrade() -> None:
    op.drop_column("commitments", "base_priority")
