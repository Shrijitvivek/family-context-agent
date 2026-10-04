"""Business operations for households and family members."""

from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import PersistenceError
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.repositories.family import FamilyRepository
from app.schemas.family import (
    FamilyDetail,
    FamilyMemberCreate,
    FamilyMemberRead,
    FamilyMemberUpdate,
)


class FamilyService:
    def __init__(self, repository: FamilyRepository) -> None:
        self._repository = repository

    async def list_families(self) -> list[Family]:
        return await self._repository.list_families()

    async def get_detail(self, family_id: UUID) -> FamilyDetail:
        """Load the household and the active members the agent can refer to."""

        family = await self._repository.get_family(family_id)
        members = await self._repository.list_members(family_id)
        return FamilyDetail(
            id=family.id,
            name=family.name,
            timezone=family.timezone,
            created_at=family.created_at,
            updated_at=family.updated_at,
            members=[FamilyMemberRead.model_validate(member) for member in members],
        )

    async def list_members(
        self, family_id: UUID, *, include_inactive: bool = False
    ) -> list[FamilyMember]:
        await self._repository.get_family(family_id)
        return await self._repository.list_members(family_id, include_inactive=include_inactive)

    async def add_member(self, family_id: UUID, payload: FamilyMemberCreate) -> FamilyMember:
        await self._repository.get_family(family_id)
        member = FamilyMember(
            family_id=family_id,
            name=payload.name,
            relationship_type=payload.relationship_type,
            display_role=payload.display_role,
        )
        try:
            member = await self._repository.add_member(member)
            await self._repository.commit()
        except SQLAlchemyError as exc:
            await self._repository.rollback()
            raise PersistenceError("add the family member") from exc
        return member

    async def update_member(
        self, family_id: UUID, member_id: UUID, payload: FamilyMemberUpdate
    ) -> FamilyMember:
        member = await self._repository.get_member(family_id, member_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(member, field, value)
        try:
            await self._repository.commit()
            await self._repository.refresh(member)
        except SQLAlchemyError as exc:
            await self._repository.rollback()
            raise PersistenceError("update the family member") from exc
        return member
