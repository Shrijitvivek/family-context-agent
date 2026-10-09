"""Document upload and confirmation endpoints.

Uploading extracts proposed fields; a commitment is only created by ``/confirm``.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile, status

from app.api.dependencies import DocumentServiceDep, TodayDep
from app.core.config import get_settings
from app.schemas.commitment import CommitmentRead
from app.schemas.document import DocumentConfirm, DocumentRead

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    service: DocumentServiceDep,
    today: TodayDep,
    family_id: Annotated[UUID, Form()],
    file: Annotated[UploadFile, File()],
    member_id: Annotated[UUID | None, Form()] = None,
):
    # Read one byte past the limit so oversized files are rejected without buffering them all.
    limit = get_settings().max_upload_size_mb * 1024 * 1024
    content = await file.read(limit + 1)
    document = await service.upload(
        family_id=family_id,
        member_id=member_id,
        file_name=file.filename or "",
        content_type=file.content_type,
        content=content,    
    )
    return await service.process(family_id, document.id, today)


# List documents for a family, optionally filtered by member.
@router.get("", response_model=list[DocumentRead])
async def list_documents(
    family_id: UUID,
    service: DocumentServiceDep,
    member_id: UUID | None = None,
):
    if member_id is not None:
        return await service.list_by_member(family_id, member_id)

    return await service.list_by_family(family_id)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(document_id: UUID, family_id: UUID, service: DocumentServiceDep):
    return await service.get(family_id, document_id)


@router.post("/{document_id}/process", response_model=DocumentRead)
async def retry_processing(
    document_id: UUID, family_id: UUID, service: DocumentServiceDep, today: TodayDep
):
    return await service.process(family_id, document_id, today)


@router.post(
    "/{document_id}/confirm",
    response_model=CommitmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def confirm_document(
    document_id: UUID, payload: DocumentConfirm, service: DocumentServiceDep
):
    return await service.confirm(document_id, payload)
