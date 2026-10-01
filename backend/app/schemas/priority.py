"""Attention items produced by the deterministic priority engine."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.constants import NotificationType, Priority
from app.schemas.commitment import CommitmentRead


class AttentionItem(BaseModel):
    """One persisted notification plus the commitment it explains."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    commitment_id: UUID | None
    notification_type: NotificationType
    priority: Priority
    title: str | None
    message: str
    is_read: bool
    created_at: datetime
    commitment: CommitmentRead | None = None


class GetFamilyPrioritiesToolResult(BaseModel):
    """The same attention items the Priorities screen shows."""

    success: Literal[True] = True
    items: list[AttentionItem]


class RecalculationResult(BaseModel):
    family_id: UUID
    marked_overdue: int
    reopened: int
    active_items: int
