"""Controlled commitment tools exposed to the Family Context Agent."""

from app.core.constants import CommitmentStatus
from app.schemas.commitment import (
    CommitmentCreate,
    CommitmentRead,
    CommitmentUpdate,
    CreateCommitmentToolResult,
    SearchCommitmentsQuery,
    SearchCommitmentsToolResult,
    UpdateCommitmentToolResult,
)
from app.services.commitment import CommitmentService


async def create_commitment(
    service: CommitmentService, payload: CommitmentCreate
) -> CreateCommitmentToolResult:
    """Create one scoped commitment after duplicate detection.

    A likely duplicate is returned as a structured conflict by the service so the
    agent can clarify with the family instead of silently creating another bill or
    appointment.
    """

    commitment = await service.create(payload)
    return CreateCommitmentToolResult(
        commitment_id=commitment.id,
        status=CommitmentStatus(commitment.status),
    )


async def search_commitments(
    service: CommitmentService, query: SearchCommitmentsQuery
) -> SearchCommitmentsToolResult:
    """Find commitments matching the agent's filters."""

    results = await service.search(query)
    return SearchCommitmentsToolResult(
        commitments=[CommitmentRead.model_validate(c) for c in results]
    )


async def update_commitment(
    service: CommitmentService, payload: CommitmentUpdate
) -> UpdateCommitmentToolResult:
    """Update an existing commitment."""
    commitment = await service.update(payload)
    return UpdateCommitmentToolResult(
        commitment_id=commitment.id,
        status=CommitmentStatus(commitment.status),
    )

