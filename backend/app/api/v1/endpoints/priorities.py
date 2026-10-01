"""Family priority endpoints: attention items with human-readable reasons."""

from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import PriorityServiceDep, TodayDep
from app.schemas.priority import AttentionItem, RecalculationResult

router = APIRouter(prefix="/priorities", tags=["priorities"])


@router.get("", response_model=list[AttentionItem])
async def get_attention_items(family_id: UUID, service: PriorityServiceDep):
    return await service.attention_items(family_id)


@router.post("/recalculate", response_model=RecalculationResult)
async def recalculate(family_id: UUID, service: PriorityServiceDep, today: TodayDep):
    return await service.recalculate(family_id, today)
