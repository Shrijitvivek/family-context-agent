"""Database access for uploaded documents."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.query import require_family_scope


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, family_id: UUID, document_id: UUID) -> Document:
        document = await self._session.get(Document, document_id)
        return require_family_scope(document, family_id, "Document", document_id)

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
