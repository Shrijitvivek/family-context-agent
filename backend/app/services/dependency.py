"""Validation and creation of commitment dependencies.

A dependency ``source -> target`` means the source must be completed before the
target. Self-links are rejected by the schema; this service rejects duplicates and
cycles, and the repository rejects links across families.
"""

from collections import defaultdict
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import DependencyCycleError, DuplicateDependencyError, PersistenceError
from app.models.commitment_dependency import CommitmentDependency
from app.repositories.commitment import CommitmentRepository
from app.schemas.commitment import CommitmentDependencyCreate
from app.services.priority import PriorityRefresher


def would_create_cycle(
    edges: list[tuple[UUID, UUID]], source_id: UUID, target_id: UUID
) -> bool:
    """Return True if ``target`` can already reach ``source`` through existing edges."""

    graph: dict[UUID, list[UUID]] = defaultdict(list)
    for edge_source, edge_target in edges:
        graph[edge_source].append(edge_target)

    stack = [target_id]
    seen: set[UUID] = set()
    while stack:
        node = stack.pop()
        if node == source_id:
            return True
        if node in seen:
            continue
        seen.add(node)
        stack.extend(graph[node])
    return False


class DependencyService:
    def __init__(
        self, repository: CommitmentRepository, on_change: PriorityRefresher | None = None
    ) -> None:
        self._repository = repository
        self._on_change = on_change

    async def create(self, payload: CommitmentDependencyCreate) -> CommitmentDependency:
        await self._repository.assert_scope(payload.family_id)
        if await self._repository.dependency_exists(
            payload.source_commitment_id,
            payload.target_commitment_id,
            payload.relationship_type,
        ):
            raise DuplicateDependencyError()

        edges = await self._repository.list_dependency_edges(payload.family_id)
        if would_create_cycle(
            edges, payload.source_commitment_id, payload.target_commitment_id
        ):
            raise DependencyCycleError()

        try:
            dependency = await self._repository.add_dependency(payload)
            await self._repository.commit()
        except SQLAlchemyError as exc:
            await self._repository.rollback()
            raise PersistenceError("create the dependency") from exc
        if self._on_change is not None:
            await self._on_change(payload.family_id)
        return dependency
