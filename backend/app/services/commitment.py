"""Business operations backing the commitment agent tools and API."""

import re
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.core.constants import CommitmentStatus
from app.core.exceptions import (
    AmbiguousCommitmentError,
    ConflictError,
    DependencyBlockedError,
    DuplicateCommitmentError,
    PersistenceError,
)
from app.models.commitment import Commitment
from app.models.commitment_dependency import CommitmentDependency
from app.repositories.commitment import CommitmentRepository
from app.schemas.commitment import (
    CommitmentCreate,
    CommitmentDependencyCreate,
    CommitmentUpdate,
    SearchCommitmentsQuery,
)
from app.services.dependency import DependencyService
from app.services.priority import PriorityRefresher


_UPDATE_REFERENCE_STOP_WORDS = frozenset(
    {
        "a", "an", "as", "at", "be", "before", "complete", "completed",
        "do", "done", "for", "i", "is", "it", "mark", "marked", "my",
        "of", "on", "our", "paid", "pay", "please", "the", "this", "that",
        "to", "update", "was", "with", "move", "reschedule", "change",
        "today", "yesterday",
    }
)


def _reference_tokens(value: str) -> set[str]:
    if re.search(r"\b(?:move|reschedule|change|set)\b", value, re.IGNORECASE):
        value = re.split(r"\bto\b", value, maxsplit=1, flags=re.IGNORECASE)[0]
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if token not in _UPDATE_REFERENCE_STOP_WORDS
    }


class CommitmentService:
    def __init__(
        self,
        repository: CommitmentRepository,
        on_change: PriorityRefresher | None = None,
    ) -> None:
        self._repository = repository
        self._on_change = on_change

    async def _changed(self, family_id: UUID) -> None:
        if self._on_change is not None:
            await self._on_change(family_id)

    async def create(self, payload: CommitmentCreate) -> Commitment:
        """Create a new commitment unless it duplicates an active family record."""
        await self._repository.assert_scope(
            payload.family_id,
            member_id=payload.member_id,
            document_id=payload.document_id,
        )

        candidates = await self._repository.find_likely_duplicates(
            family_id=payload.family_id,
            title=payload.title,
            commitment_type=payload.commitment_type,
            category=payload.category,
            due_date=payload.due_date,
        )

        if candidates:
            raise DuplicateCommitmentError(
                [
                    {
                        "commitment_id": str(candidate.id),
                        "title": candidate.title,
                        "amount": (
                            str(candidate.amount)
                            if candidate.amount is not None
                            else None
                        ),
                        "due_date": (
                            candidate.due_date.isoformat()
                            if candidate.due_date
                            else None
                        ),
                        "status": candidate.status,
                    }
                    for candidate in candidates
                ]
            )

        commitment = Commitment(
            family_id=payload.family_id,
            member_id=payload.member_id,
            commitment_type=payload.commitment_type.value,
            category=payload.category,
            title=payload.title,
            description=payload.description,
            amount=payload.amount,
            start_date=payload.start_date,
            due_date=payload.due_date,
            status=payload.status.value,
            priority=payload.priority.value,
            source_type=payload.source_type.value,
            document_id=payload.document_id,
        )

        try:
            commitment = await self._repository.add(commitment)
            await self._repository.commit()
        except SQLAlchemyError as exc:
            await self._repository.rollback()
            raise PersistenceError("create the commitment") from exc

        await self._changed(commitment.family_id)
        return commitment

    async def search(
        self,
        query: SearchCommitmentsQuery,
    ) -> list[Commitment]:
        """Find matching commitments after checking family scope."""
        await self._repository.assert_scope(
            query.family_id,
            member_id=query.member_id,
        )

        return await self._repository.search(query)

    async def find_update_candidates(
        self,
        *,
        family_id: UUID,
        member_id: UUID | None,
        reference: str,
    ) -> list[Commitment]:
        """Resolve a chat reference against family/member-scoped items.

        Matching is deliberately conservative: every usable reference term must
        be represented by a candidate. This prefers asking for clarification over
        trusting a model-selected ID.
        """

        candidates = await self.search(
            SearchCommitmentsQuery(
                family_id=family_id,
                member_id=member_id,
            )
        )
        terms = _reference_tokens(reference)
        if not terms:
            return candidates

        matches: list[Commitment] = []
        for item in candidates:
            searchable = " ".join(
                part
                for part in (
                    item.title,
                    item.description or "",
                    item.category or "",
                    item.commitment_type or "",
                    str(item.amount) if item.amount is not None else "",
                    (
                        item.due_date.strftime("%B %d %Y")
                        if item.due_date
                        else ""
                    ),
                )
                if part
            )
            candidate_terms = _reference_tokens(searchable)
            if terms <= candidate_terms:
                matches.append(item)

        return matches

    async def update(self, payload: CommitmentUpdate) -> Commitment:
        """Update a commitment while enforcing lifecycle and dependency rules."""

        # Terminal commitments are immutable through every caller (REST, tools,
        # and internal services). Check before evaluating or applying updates.
        existing = await self._repository.get(
            payload.family_id,
            payload.commitment_id,
        )
        if existing.status in {
            CommitmentStatus.COMPLETED.value,
            CommitmentStatus.CANCELLED.value,
        }:
            raise ConflictError(
                f"'{existing.title}' is already {existing.status} and cannot be modified."
            )

        if (
            payload.status is not None
            and payload.status.value == "COMPLETED"
        ):
            edges = await self._repository.list_dependency_edges(
                payload.family_id
            )

            for source_id, target_id in edges:
                if target_id != payload.commitment_id:
                    continue

                source = await self._repository.get(
                    payload.family_id,
                    source_id,
                )

                if source.status != "COMPLETED":
                    raise DependencyBlockedError(source.title)

        try:
            commitment = await self._repository.update(payload)
            await self._repository.commit()
        except SQLAlchemyError as exc:
            await self._repository.rollback()
            raise PersistenceError("update the commitment") from exc

        await self._changed(payload.family_id)
        return commitment

    async def get(
        self,
        family_id: UUID,
        commitment_id: UUID,
    ) -> Commitment:
        """Get a commitment belonging to the specified family."""
        return await self._repository.get(
            family_id,
            commitment_id,
        )

    async def create_dependency(
        self,
        payload: CommitmentDependencyCreate,
    ) -> CommitmentDependency:
        """Create a dependency after duplicate and cycle checks."""
        return await DependencyService(
            self._repository,
            self._on_change,
        ).create(payload)
