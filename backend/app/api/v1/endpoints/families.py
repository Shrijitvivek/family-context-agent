
"""Family endpoints for household management."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.dependencies import FamilyServiceDep
from app.schemas.family import FamilyCreate, FamilyDetail, FamilyRead

router = APIRouter(prefix="/families", tags=["families"])


@router.get("", response_model=list[FamilyRead])
async def list_families(service: FamilyServiceDep):
    return await service.list_families()


@router.post(
    "",
    response_model=FamilyRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_family(
    payload: FamilyCreate,
    service: FamilyServiceDep,
):
    return await service.create_family(payload)


@router.get("/{family_id}", response_model=FamilyDetail)
async def get_family(family_id: UUID, service: FamilyServiceDep):
    return await service.get_detail(family_id)

