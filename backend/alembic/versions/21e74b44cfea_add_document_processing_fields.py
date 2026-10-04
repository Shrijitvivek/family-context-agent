"""add document processing fields

Revision ID: 21e74b44cfea

Revises: 006f7b6834c3

Create Date: 2026-10-03 16:21:59.139353

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "21e74b44cfea"
down_revision: Union[str, Sequence[str], None] = "006f7b6834c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "uploaded_by_member_id",
            sa.Uuid(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "documents_uploaded_by_member_id_fkey",
        "documents",
        "family_members",
        ["uploaded_by_member_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "documents",
        sa.Column(
            "file_type",
            sa.String(length=20),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "extracted_data",
            sa.JSON(),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "processing_status",
            sa.String(length=30),
            nullable=True,
            server_default="PENDING",
        ),
    )


def downgrade() -> None:
    op.drop_column("documents", "processing_status")
    op.drop_column("documents", "extracted_data")
    op.drop_column("documents", "file_type")

    op.drop_constraint(
        "documents_uploaded_by_member_id_fkey",
        "documents",
        type_="foreignkey",
    )

    op.drop_column("documents", "uploaded_by_member_id")