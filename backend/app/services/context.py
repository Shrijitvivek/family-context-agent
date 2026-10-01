"""Household context assembly for the agent.

PostgreSQL stays the source of truth: each turn the agent receives a small, fresh
snapshot (members, active commitments, open prerequisites) instead of relying on
model memory. IDs are included so the model can reference existing records
instead of guessing them.
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.core.constants import ACTIVE_COMMITMENT_STATUSES
from app.repositories.commitment import CommitmentRepository
from app.repositories.family import FamilyRepository
from app.schemas.commitment import SearchCommitmentsQuery

MAX_COMMITMENTS_IN_CONTEXT = 25


class MemberContext(BaseModel):
    id: UUID
    name: str
    relationship_type: str


class CommitmentContext(BaseModel):
    id: UUID
    title: str
    commitment_type: str | None
    status: str
    priority: str
    due_date: date | None
    member_id: UUID | None


class HouseholdContext(BaseModel):
    family_id: UUID
    family_name: str
    speaking_member: MemberContext | None
    members: list[MemberContext]
    active_commitments: list[CommitmentContext]
    dependencies: list[tuple[UUID, UUID]]

    def to_prompt(self) -> str:
        """Render as compact text for a system message."""

        lines = [f"Household: {self.family_name}"]
        if self.speaking_member:
            lines.append(
                f"The person speaking is {self.speaking_member.name} "
                f"({self.speaking_member.relationship_type})."
            )
        lines.append("Members:")
        lines += [f"- {m.name} ({m.relationship_type}) id={m.id}" for m in self.members]

        lines.append("Active commitments (soonest first):")
        if not self.active_commitments:
            lines.append("- none")
        for c in self.active_commitments:
            due = c.due_date.isoformat() if c.due_date else "no due date"
            lines.append(
                f"- {c.title} [{c.commitment_type}, {c.status}, {c.priority}, {due}] id={c.id}"
            )

        titles = {c.id: c.title for c in self.active_commitments}
        open_links = [
            (titles[s], titles[t]) for s, t in self.dependencies if s in titles and t in titles
        ]
        if open_links:
            lines.append("Prerequisites (first must finish before second):")
            lines += [f"- {s} -> {t}" for s, t in open_links]
        return "\n".join(lines)


class ContextService:
    def __init__(self, families: FamilyRepository, commitments: CommitmentRepository) -> None:
        self._families = families
        self._commitments = commitments

    async def build(self, family_id: UUID, member_id: UUID | None = None) -> HouseholdContext:
        family = await self._families.get_family(family_id)
        members = [
            MemberContext(id=m.id, name=m.name, relationship_type=m.relationship_type)
            for m in await self._families.list_members(family_id)
        ]
        speaking = next((m for m in members if m.id == member_id), None)

        # The repository orders by due date (undated last), so truncation keeps the soonest.
        active = [
            c
            for c in await self._commitments.search(SearchCommitmentsQuery(family_id=family_id))
            if c.status in ACTIVE_COMMITMENT_STATUSES
        ][:MAX_COMMITMENTS_IN_CONTEXT]

        return HouseholdContext(
            family_id=family.id,
            family_name=family.name,
            speaking_member=speaking,
            members=members,
            active_commitments=[
                CommitmentContext(
                    id=c.id,
                    title=c.title,
                    commitment_type=c.commitment_type,
                    status=c.status,
                    priority=c.priority,
                    due_date=c.due_date,
                    member_id=c.member_id,
                )
                for c in active
            ],
            dependencies=await self._commitments.list_dependency_edges(family_id),
        )
