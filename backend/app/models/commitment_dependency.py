"""Directed prerequisite links between commitments."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.commitment import Commitment
    from app.models.family import Family


class CommitmentDependency(Base):
    __tablename__ = "commitment_dependencies"
    __table_args__ = (
        CheckConstraint(
            "source_commitment_id <> target_commitment_id",
            name="ck_commitment_dependencies_no_self_reference",
        ),
        UniqueConstraint(
            "source_commitment_id",
            "target_commitment_id",
            "relationship_type",
            name="uq_commitment_dependencies_edge",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("families.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_commitment_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("commitments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_commitment_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("commitments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    family: Mapped["Family"] = relationship(back_populates="dependencies")
    source_commitment: Mapped["Commitment"] = relationship(
        back_populates="outgoing_dependencies",
        foreign_keys=[source_commitment_id],
    )
    target_commitment: Mapped["Commitment"] = relationship(
        back_populates="incoming_dependencies",
        foreign_keys=[target_commitment_id],
    )
