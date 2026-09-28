"""Chronological timeline of dated commitments.

Groups by due date only; formatting and labels belong to the frontend.
"""

from datetime import date
from itertools import groupby
from uuid import UUID

from app.repositories.commitment import CommitmentRepository
from app.schemas.commitment import (
    CommitmentRead,
    SearchCommitmentsQuery,
    TimelineDay,
    TimelineResponse,
)


class TimelineService:
    def __init__(self, repository: CommitmentRepository) -> None:
        self._repository = repository

    async def get_timeline(
        self,
        family_id: UUID,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        member_id: UUID | None = None,
    ) -> TimelineResponse:
        await self._repository.assert_scope(family_id, member_id=member_id)
        commitments = await self._repository.search(
            SearchCommitmentsQuery(
                family_id=family_id,
                member_id=member_id,
                due_after=start_date,
                due_before=end_date,
            )
        )
        # The repository already orders by due date; undated items have no place here.
        dated = [c for c in commitments if c.due_date is not None]
        days = [
            TimelineDay(
                day=day,
                commitments=[CommitmentRead.model_validate(c) for c in items],
            )
            for day, items in groupby(dated, key=lambda c: c.due_date)
        ]
        return TimelineResponse(
            family_id=family_id, start_date=start_date, end_date=end_date, days=days
        )
