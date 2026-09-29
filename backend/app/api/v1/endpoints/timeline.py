"""Chronological timeline endpoint. Formatting stays in the frontend."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import TimelineServiceDep
from app.schemas.commitment import TimelineResponse

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("", response_model=TimelineResponse)
async def get_timeline(
    family_id: UUID,
    service: TimelineServiceDep,
    start_date: date | None = None,
    end_date: date | None = None,
    member_id: UUID | None = None,
):
    return await service.get_timeline(
        family_id, start_date=start_date, end_date=end_date, member_id=member_id
    )
