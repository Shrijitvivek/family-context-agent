"""Database access for uploaded documents."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, family_id: UUID, document_id: UUID) -> Document:
        document = await self._session.get(Document, document_id)
        if document is None or document.family_id != family_id:
            raise NotFoundError("Document", document_id)
        return document

    async def list_by_family(
        self,
        family_id: UUID,
    ) -> list[Document]:
        result = await self._session.execute(
            select(Document)
            .where(Document.family_id == family_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def add(self, document: Document) -> Document:
        self._session.add(document)
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def save(self, document: Document) -> Document:
        """Flush pending changes and reload server-generated columns."""

        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
