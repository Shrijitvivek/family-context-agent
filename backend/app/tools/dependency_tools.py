"""Dependency agent tools exposed to the Family Context Agent."""

from app.schemas.commitment import (
    CommitmentDependencyCreate,
    CreateDependencyToolResult,
)
from app.services.commitment import CommitmentService


async def create_dependency(
    service: CommitmentService, payload: CommitmentDependencyCreate
) -> CreateDependencyToolResult:
    """Create a dependency relationship between commitments."""
    await service.create_dependency(payload)
    return CreateDependencyToolResult()
