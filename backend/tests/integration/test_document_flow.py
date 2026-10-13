"""Document upload, extraction, confirmation, and persistence integration tests."""

import io
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import httpx
import pytest
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import delete, func, select

from app.api.dependencies import get_document_service, get_today
from app.clients.storage import LocalStorage
from app.core.constants import DocumentStatus
from app.core.exceptions import AIModelError
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.commitment import Commitment
from app.models.document import Document
from app.models.family import Family
from app.models.family_member import FamilyMember
from app.repositories.commitment import CommitmentRepository
from app.repositories.document import DocumentRepository
from app.services.commitment import CommitmentService
from app.services.document import DocumentService


TODAY = date(2026, 10, 13)


class ScriptedBillExtractor:
    def __init__(self) -> None:
        self.calls: list[tuple[list[dict], str | None]] = []
        self.vision_model = "scripted-vision-model"

    async def complete_json(self, messages, *, model=None):
        self.calls.append((messages, model))
        return {
            "commitment_type": "BILL",
            "title": "KSEB Electricity Bill",
            "category": "ELECTRICITY",
            "description": "Monthly electricity bill",
            "amount": "3240.00",
            "due_date": "2026-10-18",
            "confidence": 0.99,
            "missing_fields": [],
        }


class FailingBillExtractor:
    def __init__(self) -> None:
        self.calls = 0
        self.vision_model = "scripted-vision-model"

    async def complete_json(self, _messages, *, model=None):
        self.calls += 1
        raise AIModelError("scripted extraction failure")


def _bill_png() -> bytes:
    """Build a small, valid synthetic bill image without a checked-in fixture."""

    image = Image.new("RGB", (520, 180), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((16, 20), "KSEB ELECTRICITY BILL", fill="black", font=font)
    draw.text((16, 60), "Amount: Rs 3240.00", fill="black", font=font)
    draw.text((16, 100), "Due date: 2026-10-18", fill="black", font=font)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _document_service(session, storage_root, model) -> DocumentService:
    commitments = CommitmentRepository(session)
    return DocumentService(
        documents=DocumentRepository(session),
        commitments=commitments,
        commitment_service=CommitmentService(commitments),
        storage=LocalStorage(storage_root),
        model=model,  # type: ignore[arg-type]
        allowed_types=frozenset({"application/pdf", "image/jpeg", "image/png"}),
        max_bytes=1_000_000,
    )


@asynccontextmanager
async def _document_api(service):
    async def provide_document_service():
        return service

    async def provide_today():
        return TODAY

    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_document_service] = provide_document_service
    app.dependency_overrides[get_today] = provide_today
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


@pytest.mark.asyncio(loop_scope="session")
async def test_document_upload_extraction_confirmation_creates_linked_commitment(
    tmp_path,
) -> None:
    family_id, member_id = uuid4(), uuid4()
    model = ScriptedBillExtractor()

    async with AsyncSessionLocal() as session:
        session.add_all(
            [
                Family(id=family_id, name="Document Flow Integration Family"),
                FamilyMember(
                    id=member_id,
                    family_id=family_id,
                    name="Test Member",
                    relationship_type="PARENT",
                ),
            ]
        )
        await session.flush()
        service = _document_service(session, tmp_path, model)

        try:
            async with _document_api(service) as client:
                upload = await client.post(
                    "/api/v1/documents",
                    data={"family_id": str(family_id), "member_id": str(member_id)},
                    files={"file": ("kseb_bill.png", _bill_png(), "image/png")},
                )
                assert upload.status_code == 201
                uploaded = upload.json()
                document_id = UUID(uploaded["id"])
                assert uploaded["processing_status"] == DocumentStatus.NEEDS_CONFIRMATION.value
                assert uploaded["document_type"] == "BILL"
                assert uploaded["extracted_data"]["title"] == "KSEB Electricity Bill"
                assert uploaded["extracted_data"]["amount"] == "3240.00"
                assert uploaded["extracted_data"]["due_date"] == "2026-10-18"
                assert len(model.calls) == 1
                assert model.calls[0][0][-1]["content"][1]["type"] == "image_url"

                before_confirmation = await session.scalar(
                    select(func.count(Commitment.id)).where(
                        Commitment.family_id == family_id
                    )
                )
                assert before_confirmation == 0

                confirmation = await client.post(
                    f"/api/v1/documents/{document_id}/confirm",
                    json={
                        "family_id": str(family_id),
                        "member_id": str(member_id),
                        "commitment_type": "BILL",
                        "title": "KSEB Electricity Bill",
                        "category": "ELECTRICITY",
                        "description": "Monthly electricity bill",
                        "amount": "3240.00",
                        "due_date": "2026-10-18",
                        "priority": "MEDIUM",
                    },
                )
                assert confirmation.status_code == 201

            commitments = list(
                (
                    await session.scalars(
                        select(Commitment).where(Commitment.family_id == family_id)
                    )
                ).all()
            )
            assert len(commitments) == 1
            commitment = commitments[0]
            assert commitment.title == "KSEB Electricity Bill"
            assert commitment.commitment_type == "BILL"
            assert commitment.category == "ELECTRICITY"
            assert commitment.amount == Decimal("3240.00")
            assert commitment.due_date == date(2026, 10, 18)
            assert commitment.status == "PENDING"
            assert commitment.family_id == family_id
            assert commitment.member_id == member_id
            assert commitment.document_id == document_id

            document = await session.scalar(
                select(Document).where(Document.id == document_id)
            )
            assert document is not None
            assert document.family_id == family_id
            assert document.uploaded_by_member_id == member_id
            assert document.processing_status == DocumentStatus.CONFIRMED.value
        finally:
            await session.rollback()
            await session.execute(delete(Family).where(Family.id == family_id))
            await session.commit()


@pytest.mark.asyncio(loop_scope="session")
async def test_document_extraction_failure_does_not_create_commitment(tmp_path) -> None:
    family_id = uuid4()
    model = FailingBillExtractor()

    async with AsyncSessionLocal() as session:
        session.add(Family(id=family_id, name="Document Failure Integration Family"))
        await session.flush()
        service = _document_service(session, tmp_path, model)

        try:
            async with _document_api(service) as client:
                upload = await client.post(
                    "/api/v1/documents",
                    data={"family_id": str(family_id)},
                    files={"file": ("kseb_bill.png", _bill_png(), "image/png")},
                )
                assert upload.status_code == 201
                document_id = UUID(upload.json()["id"])
                assert upload.json()["processing_status"] == DocumentStatus.FAILED.value
                assert model.calls == 1

            commitment_count = await session.scalar(
                select(func.count(Commitment.id)).where(
                    Commitment.family_id == family_id
                )
            )
            assert commitment_count == 0
            document = await session.scalar(
                select(Document).where(Document.id == document_id)
            )
            assert document is not None
            assert document.processing_status == DocumentStatus.FAILED.value
        finally:
            await session.rollback()
            await session.execute(delete(Family).where(Family.id == family_id))
            await session.commit()
