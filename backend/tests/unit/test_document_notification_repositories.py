from datetime import UTC
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.db.base import Base
from app.models.family import Family
from app.core.constants import NotificationStatus
from app.core.exceptions import NotFoundError
from app.models.commitment import Commitment
from app.models.document import Document
from app.models.family_member import FamilyMember
from app.models.notification import Notification
from app.repositories.document import DocumentRepository
from app.repositories.notification import NotificationRepository
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import Session, configure_mappers


@pytest.mark.asyncio
async def test_document_repository_scopes_reads_and_persists_changes() -> None:
    family_id = uuid4()
    document = Document(
        id=uuid4(), family_id=family_id, file_name="bill.pdf", file_path="bills/bill.pdf"
    )
    foreign_document = Document(
        id=uuid4(), family_id=uuid4(), file_name="other.pdf", file_path="bills/other.pdf"
    )
    session = MagicMock()
    session.get = AsyncMock(side_effect=[document, foreign_document, None])
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = [document]
    session.execute = AsyncMock(return_value=execute_result)
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    repository = DocumentRepository(session)

    assert await repository.get(family_id, document.id) is document
    with pytest.raises(NotFoundError):
        await repository.get(family_id, foreign_document.id)
    with pytest.raises(NotFoundError):
        await repository.get(family_id, uuid4())

    assert await repository.list_by_family(family_id) == [document]
    statement = session.execute.await_args.args[0]
    assert "documents.family_id =" in str(statement)
    assert "ORDER BY documents.created_at DESC" in str(statement)

    assert await repository.add(document) is document
    assert await repository.save(document) is document
    assert session.add.call_count == 1
    assert session.flush.await_count == 2
    assert session.refresh.await_count == 2

    await repository.commit()
    await repository.rollback()
    session.commit.assert_awaited_once()
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_notification_repository_lists_active_by_family_and_resolves() -> None:
    family_id = uuid4()
    notification = Notification(
        family_id=family_id,
        notification_type="DUE_SOON",
        message="A bill is due soon.",
    )
    session = MagicMock()
    session.scalars = AsyncMock(
        return_value=SimpleNamespace(all=MagicMock(return_value=[notification]))
    )
    session.add = MagicMock()
    session.flush = AsyncMock()
    repository = NotificationRepository(session)

    assert await repository.list_active(family_id) == [notification]
    statement = session.scalars.await_args.args[0]
    sql = str(statement)
    assert "notifications.family_id =" in sql
    assert "notifications.status =" in sql
    assert "ORDER BY notifications.created_at DESC" in sql

    repository.add(notification)
    session.add.assert_called_once_with(notification)
    repository.resolve(notification)
    assert notification.status == NotificationStatus.RESOLVED.value
    assert notification.resolved_at is not None
    assert notification.resolved_at.tzinfo == UTC

    await repository.flush()
    session.flush.assert_awaited_once()


def test_document_and_notification_orm_relationships_configure() -> None:
    configure_mappers()

    document_relationships = inspect(Document).relationships
    member_relationships = inspect(FamilyMember).relationships
    commitment_relationships = inspect(Commitment).relationships
    notification_relationships = inspect(Notification).relationships

    assert document_relationships["family"].back_populates == "documents"
    assert document_relationships["commitments"].back_populates == "document"
    assert document_relationships["uploaded_by_member"].back_populates == "uploaded_documents"
    assert member_relationships["uploaded_documents"].back_populates == "uploaded_by_member"
    assert commitment_relationships["document"].back_populates == "commitments"
    assert commitment_relationships["notifications"].back_populates == "commitment"
    assert notification_relationships["family"].back_populates == "notifications"
    assert notification_relationships["commitment"].back_populates == "notifications"

    uploader_fk = next(iter(Document.__table__.c.uploaded_by_member_id.foreign_keys))
    assert uploader_fk.target_fullname == "family_members.id"
    assert uploader_fk.ondelete == "SET NULL"


def test_document_and_notification_crud_preserves_database_relationships() -> None:
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        family = Family(name="Nair Family")
        member = FamilyMember(name="Asha", relationship_type="PARENT", family=family)
        document = Document(
            family=family,
            uploaded_by_member=member,
            file_name="bill.pdf",
            file_path="family/bill.pdf",
            processing_status="PENDING",
        )
        commitment = Commitment(
            family=family,
            document=document,
            title="Electricity bill",
            category="UTILITIES",
        )
        notification = Notification(
            family=family,
            commitment=commitment,
            notification_type="DUE_SOON",
            message="Electricity bill is due soon.",
        )
        session.add_all([member, document, commitment, notification])
        session.commit()

        document_id = document.id
        commitment_id = commitment.id
        notification_id = notification.id

        loaded_document = session.get(Document, document_id)
        assert loaded_document is not None
        assert loaded_document.family.name == "Nair Family"
        assert loaded_document.uploaded_by_member is not None
        assert loaded_document.uploaded_by_member.name == "Asha"
        assert loaded_document.commitments[0].title == "Electricity bill"

        loaded_notification = session.get(Notification, notification_id)
        assert loaded_notification is not None
        assert loaded_notification.family.name == "Nair Family"
        assert loaded_notification.commitment is not None
        assert loaded_notification.commitment.document_id == document_id

        loaded_document.processing_status = "NEEDS_CONFIRMATION"
        session.commit()
        session.expire_all()
        assert session.get(Document, document_id).processing_status == "NEEDS_CONFIRMATION"

        session.delete(session.get(Document, document_id))
        session.commit()
        session.expire_all()
        assert session.get(Document, document_id) is None
        assert session.get(Commitment, commitment_id).document_id is None

        session.delete(session.get(Notification, notification_id))
        session.commit()
        assert session.get(Notification, notification_id) is None

    engine.dispose()
