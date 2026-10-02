"""Small query helpers shared by repository implementations."""

from typing import Protocol, TypeVar
from uuid import UUID

from sqlalchemy.orm import Mapped
from sqlalchemy.sql.elements import ColumnElement

from app.core.exceptions import NotFoundError


class FamilyScoped(Protocol):
    family_id: Mapped[UUID]


_Entity = TypeVar("_Entity", bound=FamilyScoped)


def build_filters(
    *conditions: ColumnElement[bool] | None,
) -> list[ColumnElement[bool]]:
    """Return the supplied SQL conditions, excluding omitted optional filters."""

    return [condition for condition in conditions if condition is not None]


def require_family_scope(
    entity: _Entity | None, family_id: UUID, entity_name: str, entity_id: UUID
) -> _Entity:
    """Return an entity only if it exists and belongs to the requested family."""

    if entity is None or entity.family_id != family_id:
        raise NotFoundError(entity_name, entity_id)
    return entity