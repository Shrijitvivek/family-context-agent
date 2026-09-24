"""SQLAlchemy declarative base.

Import ``app.models`` before reading ``Base.metadata`` (as Alembic does) so the
implemented models are registered without introducing a circular import.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class shared by all ORM models."""
