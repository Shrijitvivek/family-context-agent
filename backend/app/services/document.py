"""PDF and image processing.

Upload -> validate -> store -> extract text -> model proposes fields ->
user confirms -> commitment is created. The model's output is only a proposal:
nothing reaches the commitments table without ``confirm``.
"""

import base64
import io
import logging
from datetime import date
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from pypdf import PdfReader
from sqlalchemy.exc import SQLAlchemyError

from app.clients.ai_model import AIModelClient
from app.clients.storage import StorageClient
from app.core.constants import CommitmentType, DocumentStatus, SourceType
from app.core.exceptions import (
    AIModelError,
    DocumentStateError,
    FamilyContextError,
    PersistenceError,
)
from app.models.commitment import Commitment
from app.models.document import Document
from app.repositories.commitment import CommitmentRepository
from app.repositories.document import DocumentRepository
from app.schemas.commitment import CommitmentCreate
from app.schemas.document import DocumentConfirm, ExtractedFields
from app.services.commitment import CommitmentService
from app.utils.files import validate_upload

logger = logging.getLogger(__name__)

MAX_PDF_PAGES = 20
MAX_TEXT_CHARS = 12_000

EXTRACTION_PROMPT = f"""
You read household documents (bills, appointment letters, lab test slips, school
notices, renewal reminders) and return ONE JSON object with these keys:

commitment_type: one of {", ".join(t.value for t in CommitmentType)}, or null
title: short name such as "KSEB Electricity Bill", or null
category: short code such as ELECTRICITY, MEDICAL, SCHOOL_FEES, or null
description: one sentence, or null
amount: number without currency symbol, or null
start_date: YYYY-MM-DD, or null
due_date: YYYY-MM-DD, or null
member_name: the family member the document is for, or null
confidence: 0 to 1, how sure you are overall
missing_fields: list of keys you could not find

Use null for anything not clearly present. Never guess amounts or dates.
Return only the JSON object.
""".strip()


def extract_pdf_text(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))
        pages = reader.pages[:MAX_PDF_PAGES]
        text = "\n".join((page.extract_text() or "") for page in pages)
    except Exception as exc:  # malformed PDFs raise many unrelated exception types
        logger.info("pdf_text_extraction_failed", extra={"error": type(exc).__name__})
        return ""
    return text.strip()[:MAX_TEXT_CHARS]


def parse_extracted_fields(raw: dict[str, Any]) -> ExtractedFields:
    """Keep every valid field; drop (and report) any the model got wrong."""

    known = {k: v for k, v in raw.items() if k in ExtractedFields.model_fields}
    try:
        return ExtractedFields.model_validate(known)
    except ValidationError as exc:
        invalid = {str(error["loc"][0]) for error in exc.errors() if error["loc"]}
        cleaned = {k: v for k, v in known.items() if k not in invalid}
        fields = ExtractedFields.model_validate(cleaned)
        fields.missing_fields = sorted(set(fields.missing_fields) | invalid)
        return fields


class DocumentService:
    def __init__(
        self,
        documents: DocumentRepository,
        commitments: CommitmentRepository,
        commitment_service: CommitmentService,
        storage: StorageClient,
        model: AIModelClient,
        *,
        allowed_types: frozenset[str],
        max_bytes: int,
    ) -> None:
        self._documents = documents
        self._commitments = commitments
        self._commitment_service = commitment_service
        self._storage = storage
        self._model = model
        self._allowed_types = allowed_types
        self._max_bytes = max_bytes

    async def get(self, family_id: UUID, document_id: UUID) -> Document:
        return await self._documents.get(family_id, document_id)

    async def upload(
        self,
        *,
        family_id: UUID,
        member_id: UUID | None,
        file_name: str,
        content_type: str | None,
        content: bytes,
    ) -> Document:
        extension = validate_upload(
            content, content_type, allowed_types=self._allowed_types, max_bytes=self._max_bytes
        )
        await self._commitments.assert_scope(family_id, member_id=member_id)
        key = await self._storage.save(family_id, extension, content)
        document = Document(
            family_id=family_id,
            uploaded_by_member_id=member_id,
            file_name=file_name[:255] or f"upload{extension}",
            file_path=key,
            file_type=extension.lstrip(".").upper(),
            mime_type=content_type,
            processing_status=DocumentStatus.PENDING.value,
        )
        try:
            document = await self._documents.add(document)
            await self._documents.commit()
        except SQLAlchemyError as exc:
            await self._documents.rollback()
            raise PersistenceError("save the uploaded document") from exc
        return document

    async def process(self, family_id: UUID, document_id: UUID, today: date) -> Document:
        """Extract proposed commitment fields. Always ends in a terminal-for-now status."""

        document = await self._documents.get(family_id, document_id)
        if document.processing_status not in (
            DocumentStatus.PENDING.value,
            DocumentStatus.FAILED.value,
        ):
            raise DocumentStateError(document.processing_status, "process")

        content = await self._storage.read(document.file_path)
        user_content: str | list[dict[str, Any]]
        if document.mime_type == "application/pdf":
            text = extract_pdf_text(content)
            if not text:
                # Scanned PDFs have no text layer and there is no OCR step in the MVP.
                return await self._finish(
                    document,
                    DocumentStatus.UNREADABLE,
                    {"error": "No readable text was found in this PDF."},
                )
            document.extracted_text = text
            user_content = f"Today is {today.isoformat()}.\n\nDocument text:\n{text}"
        else:
            encoded = base64.b64encode(content).decode("ascii")
            user_content = [
                {"type": "text", "text": f"Today is {today.isoformat()}. Read this document."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{document.mime_type};base64,{encoded}"},
                },
            ]

        try:
            raw = await self._model.complete_json(
                [
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": user_content},
                ]
            )
        except AIModelError as exc:
            return await self._finish(document, DocumentStatus.FAILED, {"error": str(exc)})

        fields = parse_extracted_fields(raw)
        document.document_type = fields.commitment_type.value if fields.commitment_type else None
        return await self._finish(
            document, DocumentStatus.NEEDS_CONFIRMATION, fields.model_dump(mode="json")
        )

    async def _finish(
        self, document: Document, status: DocumentStatus, data: dict[str, Any]
    ) -> Document:
        document.processing_status = status.value
        document.extracted_data = data
        try:
            document = await self._documents.save(document)
            await self._documents.commit()
        except SQLAlchemyError as exc:
            await self._documents.rollback()
            raise PersistenceError("update the document") from exc
        return document

    async def confirm(self, document_id: UUID, payload: DocumentConfirm) -> Commitment:
        """Create the commitment from user-confirmed values, atomically with the status."""

        document = await self._documents.get(payload.family_id, document_id)
        if document.processing_status != DocumentStatus.NEEDS_CONFIRMATION.value:
            raise DocumentStateError(document.processing_status, "confirm")

        source = SourceType.PDF if document.mime_type == "application/pdf" else SourceType.IMAGE
        # Staged in the same session: CommitmentService.create commits both together,
        # and a rejected create (e.g. duplicate) leaves the document unconfirmed.
        document.processing_status = DocumentStatus.CONFIRMED.value
        try:
            return await self._commitment_service.create(
                CommitmentCreate(
                    **payload.model_dump(),
                    source_type=source,
                    document_id=document.id,
                )
            )
        except FamilyContextError:
            document.processing_status = DocumentStatus.NEEDS_CONFIRMATION.value
            raise
