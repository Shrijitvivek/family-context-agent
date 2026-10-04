"""Family endpoints for the demo household."""

from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import FamilyServiceDep
from app.schemas.family import FamilyDetail, FamilyRead

router = APIRouter(prefix="/families", tags=["families"])


@router.get("", response_model=list[FamilyRead])
async def list_families(service: FamilyServiceDep):
    return await service.list_families()


@router.get("/{family_id}", response_model=FamilyDetail)
async def get_family(family_id: UUID, service: FamilyServiceDep):
    return await service.get_detail(family_id)
