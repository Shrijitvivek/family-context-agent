"""Business operation backing the create-commitment agent tool."""

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import DuplicateCommitmentError, PersistenceError
from app.models.commitment import Commitment
from app.repositories.commitment import CommitmentRepository
from app.schemas.commitment import (
    CommitmentCreate,
    CommitmentDependencyCreate,
    CommitmentUpdate,
    GetFamilyPrioritiesQuery,
    SearchCommitmentsQuery,
)


class CommitmentService:
    def __init__(self, repository: CommitmentRepository) -> None:
        self._repository = repository

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
                        "amount": str(candidate.amount) if candidate.amount is not None else None,
                        "due_date": candidate.due_date.isoformat() if candidate.due_date else None,
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
        return commitment

    async def search(self, query: SearchCommitmentsQuery) -> list[Commitment]:
        """Find matching commitments after checking family scope."""
        await self._repository.assert_scope(query.family_id, member_id=query.member_id)
        return await self._repository.search(query)

    async def update(self, payload: CommitmentUpdate) -> Commitment:
        try:
            commitment = await self._repository.update(payload)
            await self._repository.commit()
            return commitment
        except SQLAlchemyError as exc:
            await self._repository.rollback()
            raise PersistenceError("update the commitment") from exc

    async def create_dependency(self, payload: CommitmentDependencyCreate):
        try:
            dependency = await self._repository.add_dependency(payload)
            await self._repository.commit()
            return dependency
        except SQLAlchemyError as exc:
            await self._repository.rollback()
            raise PersistenceError("create the dependency") from exc

    async def get_family_priorities(self, query: GetFamilyPrioritiesQuery) -> list[Commitment]:
        await self._repository.assert_scope(query.family_id)
        return await self._repository.get_priorities(query)
