"""Family-member endpoints used for contextual references ("Amma", "Kavya")."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.dependencies import FamilyServiceDep
from app.schemas.family import FamilyMemberCreate, FamilyMemberRead, FamilyMemberUpdate

router = APIRouter(prefix="/families/{family_id}/members", tags=["members"])


@router.get("", response_model=list[FamilyMemberRead])
async def list_members(
    family_id: UUID, service: FamilyServiceDep, include_inactive: bool = False
):
    return await service.list_members(family_id, include_inactive=include_inactive)


@router.post("", response_model=FamilyMemberRead, status_code=status.HTTP_201_CREATED)
async def add_member(
    family_id: UUID, payload: FamilyMemberCreate, service: FamilyServiceDep
):
    return await service.add_member(family_id, payload)


@router.patch("/{member_id}", response_model=FamilyMemberRead)
async def update_member(
    family_id: UUID,
    member_id: UUID,
    payload: FamilyMemberUpdate,
    service: FamilyServiceDep,
):
    return await service.update_member(family_id, member_id, payload)
