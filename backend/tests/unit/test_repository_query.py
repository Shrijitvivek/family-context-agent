from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.core.exceptions import NotFoundError
from app.repositories.query import build_filters, require_family_scope
from sqlalchemy import column


def test_build_filters_skips_omitted_conditions() -> None:
    conditions = build_filters(column("family_id") == "family", None, column("category") == "food")

    assert len(conditions) == 2
    assert [str(condition) for condition in conditions] == [
        "family_id = :family_id_1",
        "category = :category_1",
    ]


def test_require_family_scope_returns_matching_entity() -> None:
    family_id = uuid4()
    entity = SimpleNamespace(id=uuid4(), family_id=family_id)

    assert require_family_scope(entity, family_id, "Record", entity.id) is entity


def test_require_family_scope_rejects_missing_or_other_family_entity() -> None:
    family_id = uuid4()
    entity_id = uuid4()
    foreign_entity = SimpleNamespace(id=entity_id, family_id=uuid4())

    with pytest.raises(NotFoundError):
        require_family_scope(None, family_id, "Record", entity_id)
    with pytest.raises(NotFoundError):
        require_family_scope(foreign_entity, family_id, "Record", entity_id)