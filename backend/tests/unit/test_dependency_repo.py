import uuid
from datetime import date

import pytest

from app.db.Session import AsyncSessionLocal
from app.models.family import Family
from app.repositories.commitment_repository import (
    CommitmentRepository,
)
from app.repositories.dependency_repository import (
    DependencyRepository,
)


@pytest.mark.asyncio
async def test_dependency_crud():

    async with AsyncSessionLocal() as session:

        family = Family(
            name=f"Dependency Test {uuid.uuid4()}",
            timezone="Asia/Kolkata",
        )

        session.add(family)
        await session.flush()

        commitment_repo = CommitmentRepository(session)
        dependency_repo = DependencyRepository(session)

        prerequisite = await commitment_repo.create(
            family_id=family.id,
            title="Complete CBC test",
            category="Medical",
            due_date=date.today(),
        )

        dependent = await commitment_repo.create(
            family_id=family.id,
            title="Doctor review",
            category="Medical",
            due_date=date.today(),
        )

        dependency = await dependency_repo.create(
            source_commitment_id=prerequisite.id,
            target_commitment_id=dependent.id,
        )

        assert dependency.id is not None

        prerequisites = await dependency_repo.get_prerequisites(
            dependent.id
        )

        assert len(prerequisites) == 1

        dependents = await dependency_repo.get_dependents(
            prerequisite.id
        )

        assert len(dependents) == 1

        await session.rollback()