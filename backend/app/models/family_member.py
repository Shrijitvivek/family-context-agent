"""Family-member ORM model used to scope expenses and commitments."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.commitment import Commitment
    from app.models.expense import Expense
    from app.models.family import Family


class FamilyMember(Base):
    __tablename__ = "family_members"
    __table_args__ = (Index("ix_family_members_family_name", "family_id", "name"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("families.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    relationship_name: Mapped[str | None] = mapped_column("relationship", String(50), nullable=True)
    display_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    family: Mapped["Family"] = relationship(back_populates="members")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="member")
    commitments: Mapped[list["Commitment"]] = relationship(back_populates="member")
