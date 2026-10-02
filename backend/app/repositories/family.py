"""Database access for households and family members."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.repositories.query import build_filters, require_family_scope


class FamilyRepository:
    """Member queries are always scoped to one family."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_families(self) -> list[Family]:
        statement = select(Family).order_by(Family.created_at.asc())
        return list((await self._session.scalars(statement)).all())

    async def get_family(self, family_id: UUID) -> Family:
        family = await self._session.get(Family, family_id)
        if family is None:
            raise NotFoundError("Family", family_id)
        return family

    async def list_members(
        self, family_id: UUID, *, include_inactive: bool = False
    ) -> list[FamilyMember]:
        conditions = build_filters(
            FamilyMember.family_id == family_id,
            FamilyMember.is_active.is_(True) if not include_inactive else None,
        )
        statement = select(FamilyMember).where(*conditions).order_by(FamilyMember.name.asc())
        return list((await self._session.scalars(statement)).all())

    async def get_member(self, family_id: UUID, member_id: UUID) -> FamilyMember:
        member = await self._session.get(FamilyMember, member_id)
        return require_family_scope(member, family_id, "Family member", member_id)

    async def add_member(self, member: FamilyMember) -> FamilyMember:
        self._session.add(member)
        await self._session.flush()
        await self._session.refresh(member)
        return member

    async def delete_family(self, family_id: UUID) -> None:
        """Delete a household; the database cascades to every family-scoped row."""

        await self._session.execute(delete(Family).where(Family.id == family_id))

    async def add_all(self, instances: list[object]) -> None:
        self._session.add_all(instances)
        await self._session.flush()

    async def refresh(self, instance: object) -> None:
        await self._session.refresh(instance)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
