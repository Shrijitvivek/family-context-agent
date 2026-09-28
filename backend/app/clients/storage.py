"""File storage for uploaded documents.

Files are stored under generated names only, so user-supplied filenames can never
choose a path. ``LocalStorage`` is the development backend; an object-store backend
can implement the same protocol later.
"""

from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

from app.core.config import get_settings


class StorageClient(Protocol):
    async def save(self, family_id: UUID, extension: str, content: bytes) -> str: ...

    async def read(self, key: str) -> bytes: ...


class LocalStorage:
    def __init__(self, root: Path | None = None) -> None:
        self._root = (root or get_settings().upload_path).resolve()

    def _resolve(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if not path.is_relative_to(self._root):
            raise ValueError("Storage key escapes the upload directory.")
        return path

    async def save(self, family_id: UUID, extension: str, content: bytes) -> str:
        """Store bytes and return a relative storage key."""

        key = f"{family_id}/{uuid4().hex}{extension}"
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    async def read(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()
