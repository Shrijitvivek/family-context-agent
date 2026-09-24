"""Shared ORM model for household commitments."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.commitment_dependency import CommitmentDependency
    from app.models.document import Document
    from app.models.family import Family
    from app.models.family_member import FamilyMember
    from app.models.notification import Notification


class Commitment(Base):
    __tablename__ = "commitments"
    __table_args__ = (
        CheckConstraint("amount IS NULL OR amount > 0", name="ck_commitments_amount_positive"),
        Index("ix_commitments_family_status_due", "family_id", "status", "due_date"),
        Index("ix_commitments_family_category", "family_id", "category"),
        Index("ix_commitments_member_due", "member_id", "due_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("families.id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True, index=True
    )
    commitment_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PENDING", server_default="PENDING"
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MEDIUM", server_default="MEDIUM"
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    document_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    family: Mapped["Family"] = relationship(back_populates="commitments")
    member: Mapped["FamilyMember | None"] = relationship(back_populates="commitments")
    document: Mapped["Document | None"] = relationship(back_populates="commitments")
    outgoing_dependencies: Mapped[list["CommitmentDependency"]] = relationship(
        back_populates="source_commitment",
        foreign_keys="CommitmentDependency.source_commitment_id",
    )
    incoming_dependencies: Mapped[list["CommitmentDependency"]] = relationship(
        back_populates="target_commitment",
        foreign_keys="CommitmentDependency.target_commitment_id",
    )
    notifications: Mapped[list["Notification"]] = relationship(back_populates="commitment")
