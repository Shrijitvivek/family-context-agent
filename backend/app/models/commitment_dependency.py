import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CommitmentDependency(Base):
    __tablename__ = "commitment_dependencies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    source_commitment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("commitments.id", ondelete="CASCADE"),
        nullable=False,
    )

    target_commitment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("commitments.id", ondelete="CASCADE"),
        nullable=False,
    )

    dependency_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="MUST_COMPLETE_BEFORE",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    source_commitment = relationship(
        "Commitment",
        foreign_keys=[source_commitment_id],
    )

    target_commitment = relationship(
        "Commitment",
        foreign_keys=[target_commitment_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "source_commitment_id",
            "target_commitment_id",
            "dependency_type",
            name="uq_commitment_dependency",
        ),
        CheckConstraint(
            "source_commitment_id <> target_commitment_id",
            name="ck_no_self_dependency",
        ),
        Index(
            "ix_commitment_dependencies_source",
            "source_commitment_id",
        ),
        Index(
            "ix_commitment_dependencies_target",
            "target_commitment_id",
        ),
    )