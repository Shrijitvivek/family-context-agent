"""Commitment dependency service.

TODO:
- Validate and create MUST_COMPLETE_BEFORE relationships.
- Reject cycles, self-dependencies, and links across families.
"""


from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dependency_repository import DependencyRepository


class DependencyService:
    """Business logic for commitment dependencies."""

    def __init__(self, session: AsyncSession):
        self.repository = DependencyRepository(session)
        self.session = session

    async def create_dependency(
        self,
        source_commitment_id: UUID,
        target_commitment_id: UUID,
        dependency_type: str = "MUST_COMPLETE_BEFORE",
    ):

        if source_commitment_id == target_commitment_id:
            raise ValueError(
                "A commitment cannot depend on itself."
            )

        dependency = await self.repository.create(
            source_commitment_id=source_commitment_id,
            target_commitment_id=target_commitment_id,
            dependency_type=dependency_type,
        )

        await self.session.commit()

        return dependency

    async def get_prerequisites(
        self,
        commitment_id: UUID,
    ):

        return await self.repository.get_prerequisites(
            commitment_id
        )

    async def get_dependents(
        self,
        commitment_id: UUID,
    ):

        return await self.repository.get_dependents(
            commitment_id
        )

    async def delete_dependency(
        self,
        dependency_id: UUID,
    ):

        deleted = await self.repository.delete(
            dependency_id
        )

        if not deleted:
            raise ValueError("Dependency not found.")

        await self.session.commit()

        return True