"""Database access for attention items (notifications)."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import NotificationStatus
from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self, family_id: UUID) -> list[Notification]:
        statement = (
            select(Notification)
            .where(
                Notification.family_id == family_id,
                Notification.status == NotificationStatus.ACTIVE.value,
            )
            .order_by(Notification.created_at.desc())
        )
        return list((await self._session.scalars(statement)).all())

    def add(self, notification: Notification) -> None:
        self._session.add(notification)

    @staticmethod
    def resolve(notification: Notification) -> None:
        notification.status = NotificationStatus.RESOLVED.value
        notification.resolved_at = datetime.now(UTC)

    async def flush(self) -> None:
        await self._session.flush()
