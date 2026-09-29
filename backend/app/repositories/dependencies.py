from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commitment_dependency import CommitmentDependency


class DependencyRepository:
    """Database operations for commitment dependencies."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        source_commitment_id: UUID,
        target_commitment_id: UUID,
        dependency_type: str = "MUST_COMPLETE_BEFORE",
    ) -> CommitmentDependency:

        dependency = CommitmentDependency(
            source_commitment_id=source_commitment_id,
            target_commitment_id=target_commitment_id,
            dependency_type=dependency_type,
        )

        self.session.add(dependency)

        await self.session.flush()
        await self.session.refresh(dependency)

        return dependency

    async def get_by_id(
        self,
        dependency_id: UUID,
    ) -> CommitmentDependency | None:

        result = await self.session.execute(
            select(CommitmentDependency)
            .where(CommitmentDependency.id == dependency_id)
        )

        return result.scalar_one_or_none()

    async def get_prerequisites(
        self,
        commitment_id: UUID,
    ) -> list[CommitmentDependency]:

        result = await self.session.execute(
            select(CommitmentDependency)
            .where(
                CommitmentDependency.target_commitment_id
                == commitment_id
            )
        )

        return list(result.scalars().all())

    async def get_dependents(
        self,
        commitment_id: UUID,
    ) -> list[CommitmentDependency]:

        result = await self.session.execute(
            select(CommitmentDependency)
            .where(
                CommitmentDependency.source_commitment_id
                == commitment_id
            )
        )

        return list(result.scalars().all())

    async def delete(
        self,
        dependency_id: UUID,
    ) -> bool:

        dependency = await self.get_by_id(dependency_id)

        if dependency is None:
            return False

        await self.session.delete(dependency)
        await self.session.flush()

        return True