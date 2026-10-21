
"""Add deterministic per-conversation message ordering."""

from alembic import op
import sqlalchemy as sa


revision = "4d91c2a7e6f0"
down_revision = "a14c8f27b9e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add as nullable first so existing messages can be backfilled.
    op.add_column(
        "messages",
        sa.Column("sequence_number", sa.Integer(), nullable=True),
    )

    # Assign a deterministic sequence to existing messages.
    # Historical ties are resolved by UUID; their original send order
    # cannot be recovered if the timestamps were identical.
    op.execute(
        """
        WITH ranked_messages AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY conversation_id
                    ORDER BY created_at ASC, id ASC
                ) AS new_sequence
            FROM messages
        )
        UPDATE messages AS m
        SET sequence_number = r.new_sequence
        FROM ranked_messages AS r
        WHERE m.id = r.id
        """
    )

    op.alter_column(
        "messages",
        "sequence_number",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.create_unique_constraint(
        "uq_messages_conversation_sequence",
        "messages",
        ["conversation_id", "sequence_number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_messages_conversation_sequence",
        "messages",
        type_="unique",
    )

    op.drop_column("messages", "sequence_number")
