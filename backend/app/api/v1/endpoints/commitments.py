"""Commitment endpoints: bills, tasks, appointments, tests, and deadlines.

Status transitions and duplicate checks live in the service layer.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.dependencies import CommitmentServiceDep, DependencyServiceDep
from app.schemas.commitment import (
    CommitmentCreate,
    CommitmentDependencyCreate,
    CommitmentDependencyRead,
    CommitmentRead,
    CommitmentUpdate,
    CommitmentUpdateRequest,
    SearchCommitmentsQuery,
)

router = APIRouter(prefix="/commitments", tags=["commitments"])


@router.post("", response_model=CommitmentRead, status_code=status.HTTP_201_CREATED)
async def create_commitment(payload: CommitmentCreate, service: CommitmentServiceDep):
    return await service.create(payload)


@router.get("", response_model=list[CommitmentRead])
async def list_commitments(
    query: Annotated[SearchCommitmentsQuery, Query()], service: CommitmentServiceDep
):
    return await service.search(query)


@router.post(
    "/dependencies",
    response_model=CommitmentDependencyRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_dependency(
    payload: CommitmentDependencyCreate, service: DependencyServiceDep
):
    return await service.create(payload)


@router.get("/{commitment_id}", response_model=CommitmentRead)
async def get_commitment(
    commitment_id: UUID, family_id: UUID, service: CommitmentServiceDep
):
    return await service.get(family_id, commitment_id)


@router.patch("/{commitment_id}", response_model=CommitmentRead)
async def update_commitment(
    commitment_id: UUID, payload: CommitmentUpdateRequest, service: CommitmentServiceDep
):
    return await service.update(
        CommitmentUpdate(commitment_id=commitment_id, **payload.model_dump())
    )
