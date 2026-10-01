"""Upload validation and storage-safety unit tests."""

from uuid import uuid4

import pytest
from app.clients.storage import LocalStorage
from app.core.exceptions import InvalidUploadError
from app.utils.files import validate_upload

ALLOWED = frozenset({"application/pdf", "image/jpeg", "image/png"})
PDF = b"%PDF-1.7\n..."
PNG = b"\x89PNG\r\n\x1a\n...."


def check(content: bytes, content_type: str | None, max_bytes: int = 1_000) -> str:
    return validate_upload(content, content_type, allowed_types=ALLOWED, max_bytes=max_bytes)


def test_accepts_supported_types_and_returns_extension() -> None:
    assert check(PDF, "application/pdf") == ".pdf"
    assert check(PNG, "image/png") == ".png"
    assert check(b"\xff\xd8\xff\xe0....", "image/jpeg") == ".jpg"


@pytest.mark.parametrize(
    ("content", "content_type"),
    [
        (b"", "application/pdf"),  # empty
        (PDF, "text/html"),  # unsupported type
        (PDF, None),  # missing type
        (PNG, "application/pdf"),  # signature does not match the declared type
        (b"<script>alert(1)</script>", "image/png"),
    ],
)
def test_rejects_invalid_uploads(content: bytes, content_type: str | None) -> None:
    with pytest.raises(InvalidUploadError):
        check(content, content_type)


def test_rejects_oversized_files() -> None:
    with pytest.raises(InvalidUploadError):
        check(PDF + b"x" * 100, "application/pdf", max_bytes=50)


@pytest.mark.asyncio
async def test_storage_uses_generated_names_and_blocks_traversal(tmp_path) -> None:
    storage = LocalStorage(tmp_path)
    family_id = uuid4()
    key = await storage.save(family_id, ".pdf", PDF)

    assert key.startswith(f"{family_id}/") and key.endswith(".pdf")
    assert await storage.read(key) == PDF
    with pytest.raises(ValueError):
        await storage.read("../../etc/passwd")
