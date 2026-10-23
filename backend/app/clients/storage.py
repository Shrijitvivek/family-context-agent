
"""File storage for uploaded documents."""

from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

from supabase import create_client
from supabase import Client

from app.core.config import get_settings


class StorageClient(Protocol):
    async def save(
        self, family_id: UUID, extension: str, content: bytes
    ) -> str: ...

    async def read(self, key: str) -> bytes: ...


class LocalStorage:
    """Local file storage for development and tests."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = (root or get_settings().upload_path).resolve()

    def _resolve(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if not path.is_relative_to(self._root):
            raise ValueError("Storage key escapes the upload directory.")
        return path

    async def save(
        self, family_id: UUID, extension: str, content: bytes
    ) -> str:
        key = f"{family_id}/{uuid4().hex}{extension}"
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    async def read(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()


class SupabaseStorage:
    """Private Supabase Storage backend."""

    def __init__(
        self,
        url: str | None = None,
        service_role_key: str | None = None,
        bucket: str = "family-documents",
    ) -> None:
        settings = get_settings()
        self._url = url or settings.supabase_url
        self._key = service_role_key or settings.supabase_service_role_key
        self._bucket = bucket

        if not self._url or not self._key:
            raise ValueError("Supabase storage credentials are not configured.")

        self._client: Client = create_client(self._url, self._key)

    async def save(
        self, family_id: UUID, extension: str, content: bytes
    ) -> str:
        key = f"{family_id}/{uuid4().hex}{extension}"
        content_types = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }
        content_type = content_types.get(extension.lower())

        if content_type is None:
            raise ValueError("Unsupported document file type.")

        self._client.storage.from_(self._bucket).upload(
            path=key,
            file=content,
            file_options={
                "content-type": content_type,
                "upsert": "false",
            },
        )
        return key

    async def read(self, key: str) -> bytes:
        return self._client.storage.from_(self._bucket).download(key)
