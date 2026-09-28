"""Notification lifecycle: one active item per (commitment, type), kept in sync."""

from typing import TYPE_CHECKING
from uuid import UUID

from app.core.constants import NotificationStatus
from app.models.notification import Notification
from app.repositories.notification import NotificationRepository

if TYPE_CHECKING:
    from app.services.priority import Assessment


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self._repository = repository

    async def list_active(self, family_id: UUID) -> list[Notification]:
        return await self._repository.list_active(family_id)

    async def sync(self, family_id: UUID, assessments: list["Assessment"]) -> int:
        """Upsert current attention items and resolve ones that no longer apply.

        Does not commit; the caller owns the transaction. Returns the number of
        active items after syncing.
        """

        wanted = {(a.commitment_id, a.notification_type.value): a for a in assessments}
        existing: dict[tuple[UUID | None, str], Notification] = {}
        for notification in await self._repository.list_active(family_id):
            key = (notification.commitment_id, notification.notification_type)
            if key in existing or key not in wanted:
                # Stale or duplicate items are resolved, never deleted.
                self._repository.resolve(notification)
            else:
                existing[key] = notification

        for key, assessment in wanted.items():
            notification = existing.get(key)
            if notification is None:
                self._repository.add(
                    Notification(
                        family_id=family_id,
                        commitment_id=assessment.commitment_id,
                        notification_type=assessment.notification_type.value,
                        priority=assessment.priority.value,
                        title=assessment.title,
                        message=assessment.message,
                        status=NotificationStatus.ACTIVE.value,
                        is_read=False,
                    )
                )
                continue
            if notification.message != assessment.message:
                # The situation changed (e.g. "due tomorrow" -> "due today"): surface it again.
                notification.is_read = False
            notification.priority = assessment.priority.value
            notification.title = assessment.title
            notification.message = assessment.message

        await self._repository.flush()
        return len(wanted)
