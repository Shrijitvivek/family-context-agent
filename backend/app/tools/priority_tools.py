"""Family priority agent tools exposed to the Family Context Agent."""

from app.schemas.commitment import (
    CommitmentRead,
    GetFamilyPrioritiesQuery,
    GetFamilyPrioritiesToolResult,
)
from app.services.commitment import CommitmentService


async def get_family_priorities(
    service: CommitmentService, query: GetFamilyPrioritiesQuery
) -> GetFamilyPrioritiesToolResult:
    """Get upcoming and priority commitments for a family."""
    results = await service.get_family_priorities(query)
    return GetFamilyPrioritiesToolResult(
        commitments=[CommitmentRead.model_validate(c) for c in results]
    )
