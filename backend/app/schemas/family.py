"""Validated inputs and outputs for households and family members."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_required(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("value cannot be blank")
    return value


class FamilyMemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    relationship_type: str = Field(default="OTHER", min_length=1, max_length=50)
    display_role: str | None = Field(default=None, max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return _strip_required(value)

    @field_validator("relationship_type")
    @classmethod
    def normalise_relationship(cls, value: str) -> str:
        return "_".join(_strip_required(value).upper().split())


class FamilyMemberUpdate(BaseModel):
    """Partial update; omitted fields are left unchanged."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    relationship_type: str | None = Field(default=None, min_length=1, max_length=50)
    display_role: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        return _strip_required(value) if value is not None else None

    @field_validator("relationship_type")
    @classmethod
    def normalise_relationship(cls, value: str | None) -> str | None:
        return "_".join(_strip_required(value).upper().split()) if value is not None else None


class FamilyMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    family_id: UUID
    name: str
    relationship_type: str
    display_role: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FamilyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    timezone: str
    created_at: datetime
    updated_at: datetime


class FamilyDetail(FamilyRead):
    """A household with the active members used for reference resolution."""

    members: list[FamilyMemberRead]
