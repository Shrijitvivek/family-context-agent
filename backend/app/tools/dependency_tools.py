"""Dependency agent tools exposed to the Family Context Agent.

The MVP supports a single relationship: the source commitment must be completed
before the target. Duplicate and cycle checks live in the dependency service.
"""

from uuid import UUID

from pydantic import field_validator

from app.core.constants import DependencyType
from app.schemas.commitment import (
    CommitmentDependencyCreate,
    CreateDependencyToolResult,
)
from app.services.commitment import CommitmentService


class CreateDependencyInput(CommitmentDependencyCreate):
    """``create_dependency`` arguments; the relationship defaults to the MVP type."""

    relationship_type: str = DependencyType.MUST_COMPLETE_BEFORE.value

    @field_validator("relationship_type", mode="before")
    @classmethod
    def only_must_complete_before(cls, value: object) -> str:
        normalised = "_".join(str(value or "").strip().upper().split())
        if normalised not in ("", DependencyType.MUST_COMPLETE_BEFORE.value):
            raise ValueError("only MUST_COMPLETE_BEFORE dependencies are supported")
        return DependencyType.MUST_COMPLETE_BEFORE.value


class CreateDependencyResult(CreateDependencyToolResult):
    dependency_id: UUID
    source_commitment_id: UUID
    target_commitment_id: UUID
    relationship_type: DependencyType


async def create_dependency(
    service: CommitmentService, payload: CommitmentDependencyCreate
) -> CreateDependencyResult:
    """Record that the source commitment must be completed before the target."""

    source = await service.get(payload.family_id, payload.source_commitment_id)
    target = await service.get(payload.family_id, payload.target_commitment_id)
    dependency = await service.create_dependency(payload)
    return CreateDependencyResult(
        dependency_id=dependency.id,
        source_commitment_id=payload.source_commitment_id,
        target_commitment_id=payload.target_commitment_id,
        relationship_type=DependencyType.MUST_COMPLETE_BEFORE,
        message=f"'{source.title}' must now be completed before '{target.title}'.",
    )
