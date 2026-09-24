"""Family ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.commitment import Commitment
    from app.models.commitment_dependency import CommitmentDependency
    from app.models.document import Document
    from app.models.expense import Expense
    from app.models.family_member import FamilyMember
    from app.models.notification import Notification


class Family(Base):
    __tablename__ = "families"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Asia/Kolkata")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    members: Mapped[list["FamilyMember"]] = relationship(back_populates="family")
    expenses: Mapped[list["Expense"]] = relationship(back_populates="family")
    commitments: Mapped[list["Commitment"]] = relationship(back_populates="family")
    documents: Mapped[list["Document"]] = relationship(back_populates="family")
    dependencies: Mapped[list["CommitmentDependency"]] = relationship(back_populates="family")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="family")
