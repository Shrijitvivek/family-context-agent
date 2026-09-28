"""Safe uploaded-file helpers."""

from app.core.exceptions import InvalidUploadError

# MIME type -> (file signature, stored extension)
_SIGNATURES: dict[str, tuple[bytes, str]] = {
    "application/pdf": (b"%PDF-", ".pdf"),
    "image/jpeg": (b"\xff\xd8\xff", ".jpg"),
    "image/png": (b"\x89PNG\r\n\x1a\n", ".png"),
}


def validate_upload(
    content: bytes,
    content_type: str | None,
    *,
    allowed_types: frozenset[str],
    max_bytes: int,
) -> str:
    """Check type, size, and magic bytes; return the extension to store it under.

    The declared content type is not trusted on its own: the file must also start
    with that type's signature.
    """

    if not content:
        raise InvalidUploadError("The uploaded file is empty.")
    if len(content) > max_bytes:
        raise InvalidUploadError(
            "The uploaded file is too large.", details={"max_bytes": max_bytes}
        )
    if content_type not in allowed_types or content_type not in _SIGNATURES:
        raise InvalidUploadError(
            "Only PDF, JPEG, and PNG files are supported.",
            details={"content_type": content_type},
        )
    signature, extension = _SIGNATURES[content_type]
    if not content.startswith(signature):
        raise InvalidUploadError(
            "The file contents do not match its declared type.",
            details={"content_type": content_type},
        )
    return extension
