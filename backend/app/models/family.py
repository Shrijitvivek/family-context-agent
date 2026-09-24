import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Family(Base):
    __tablename__ = "families"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Asia/Kolkata",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    members = relationship(
        "FamilyMember",
        back_populates="family",
        cascade="all, delete-orphan",
    )

    expenses = relationship(
        "Expense",
        back_populates="family",
        cascade="all, delete-orphan",
    )

    commitments = relationship(
        "Commitment",
        back_populates="family",
        cascade="all, delete-orphan",
    )

    documents = relationship(
        "Document",
        back_populates="family",
        cascade="all, delete-orphan",
    )