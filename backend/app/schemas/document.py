"""Document upload, extraction, and confirmation shapes."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import CommitmentType, DocumentStatus, Priority


class ExtractedFields(BaseModel):
    """What the model read from a document. Every field is optional and unconfirmed."""

    commitment_type: CommitmentType | None = None
    title: str | None = Field(default=None, max_length=200)
    category: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=2_000)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    start_date: date | None = None
    due_date: date | None = None
    member_name: str | None = Field(default=None, max_length=150)
    confidence: float | None = Field(default=None, ge=0, le=1)
    missing_fields: list[str] = Field(default_factory=list)


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    family_id: UUID
    uploaded_by_member_id: UUID | None
    file_name: str
    file_type: str | None
    mime_type: str | None
    document_type: str | None
    processing_status: DocumentStatus | None
    extracted_data: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class DocumentConfirm(BaseModel):
    """The values the user checked (and possibly corrected) before saving."""

    family_id: UUID
    member_id: UUID | None = None
    commitment_type: CommitmentType
    title: str = Field(min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=2_000)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    start_date: date | None = None
    due_date: date | None = None
    priority: Priority = Priority.MEDIUM
