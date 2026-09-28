"""Validated inputs and outputs for commitment creation."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.constants import CommitmentStatus, CommitmentType, Priority, SourceType


def _normalise_code(value: str) -> str:
    normalised = "_".join(value.strip().upper().split())
    if not normalised:
        raise ValueError("category cannot be blank")
    return normalised


class CommitmentCreate(BaseModel):
    """A safe, create-only commitment payload.

    Terminal status changes are deliberately excluded: they belong to the future
    ``update_commitment`` tool, preventing an agent from bypassing lifecycle rules.
    """

    family_id: UUID
    member_id: UUID | None = None
    commitment_type: CommitmentType
    category: str | None = Field(default=None, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2_000)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    start_date: date | None = None
    due_date: date | None = None
    status: CommitmentStatus = CommitmentStatus.PENDING
    priority: Priority = Priority.MEDIUM
    source_type: SourceType = SourceType.TEXT
    document_id: UUID | None = None

    @field_validator("category")
    @classmethod
    def normalise_category(cls, value: str | None) -> str | None:
        return _normalise_code(value) if value is not None else None

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def check_dates_and_document_source(self) -> "CommitmentCreate":
        if self.start_date and self.due_date and self.start_date > self.due_date:
            raise ValueError("start_date must be on or before due_date")
        if self.document_id and self.source_type not in {SourceType.PDF, SourceType.IMAGE}:
            raise ValueError("document_id requires a PDF or IMAGE source_type")
        if self.status not in {
            CommitmentStatus.PENDING,
            CommitmentStatus.SCHEDULED,
            CommitmentStatus.IN_PROGRESS,
        }:
            raise ValueError("create_commitment cannot create a terminal or overdue commitment")
        return self


class CommitmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    family_id: UUID
    member_id: UUID | None
    commitment_type: CommitmentType
    category: str | None
    title: str
    description: str | None
    amount: Decimal | None
    start_date: date | None
    due_date: date | None
    status: CommitmentStatus
    priority: Priority
    source_type: SourceType
    document_id: UUID | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CreateCommitmentToolResult(BaseModel):
    success: Literal[True] = True
    commitment_id: UUID
    status: CommitmentStatus


class SearchCommitmentsQuery(BaseModel):
    """Filters for finding commitments for the family."""

    family_id: UUID
    member_id: UUID | None = None
    commitment_type: CommitmentType | None = None
    status: CommitmentStatus | None = None
    category: str | None = Field(default=None, max_length=50)
    due_before: date | None = None
    due_after: date | None = None
    title_query: str | None = Field(default=None, max_length=200)

    @field_validator("category")
    @classmethod
    def normalise_optional_category(cls, value: str | None) -> str | None:
        return _normalise_code(value) if value is not None else None


class SearchCommitmentsToolResult(BaseModel):
    """A list of matching commitments returned to the agent."""

    success: Literal[True] = True
    commitments: list[CommitmentRead]


class CommitmentUpdate(BaseModel):
    """Payload to update an existing commitment."""

    commitment_id: UUID
    family_id: UUID
    status: CommitmentStatus | None = None
    priority: Priority | None = None
    due_date: date | None = None


class UpdateCommitmentToolResult(BaseModel):
    success: Literal[True] = True
    commitment_id: UUID
    status: CommitmentStatus


class CommitmentDependencyCreate(BaseModel):
    """Payload to link two commitments."""

    family_id: UUID
    source_commitment_id: UUID
    target_commitment_id: UUID
    relationship_type: str = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def check_not_self_referencing(self) -> "CommitmentDependencyCreate":
        if self.source_commitment_id == self.target_commitment_id:
            raise ValueError("source_commitment_id and target_commitment_id cannot be the same")
        return self


class CreateDependencyToolResult(BaseModel):
    success: Literal[True] = True
    message: str = "Dependency created"


class GetFamilyPrioritiesQuery(BaseModel):
    """Filters for finding priority commitments for the family."""

    family_id: UUID


class GetFamilyPrioritiesToolResult(BaseModel):
    success: Literal[True] = True
    commitments: list[CommitmentRead]
