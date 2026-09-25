"""add family id to commitment dependencies

Revision ID: YOUR_REVISION_ID
Revises: 971ee29960f6
"""

from alembic import op
import sqlalchemy as sa


revision = "YOUR_REVISION_ID"
down_revision = "971ee29960f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "commitment_dependencies",
        sa.Column(
            "family_id",
            sa.Uuid(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_commitment_dependencies_family_id_families",
        "commitment_dependencies",
        "families",
        ["family_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_commitment_dependencies_family_id",
        "commitment_dependencies",
        ["family_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_commitment_dependencies_family_id",
        table_name="commitment_dependencies",
    )

    op.drop_constraint(
        "fk_commitment_dependencies_family_id_families",
        "commitment_dependencies",
        type_="foreignkey",
    )

    op.drop_column(
        "commitment_dependencies",
        "family_id",
    )