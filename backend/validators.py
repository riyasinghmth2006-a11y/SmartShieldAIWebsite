"""Input validation and file integrity checks for SmartShield AI."""

import os
from typing import Tuple
from backend.config import (
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_IMAGE_SIZE_BYTES,
    MAX_NEWS_TEXT_LENGTH,
    MAX_SCAM_TEXT_LENGTH,
    MIN_NEWS_TEXT_LENGTH,
    MIN_SCAM_TEXT_LENGTH,
)


class ValidationError(Exception):
    """Raised when user input violates validation criteria."""
    pass


def validate_scam_input(content: str, mode: str) -> str:
    """Validate and normalize user input for scam analysis."""
    if not isinstance(content, str):
        raise ValidationError("Input content must be a string.")

    cleaned = content.strip()

    if len(cleaned) < MIN_SCAM_TEXT_LENGTH:
        raise ValidationError(
            f"Input is too short. Please provide at least {MIN_SCAM_TEXT_LENGTH} characters."
        )

    if len(cleaned) > MAX_SCAM_TEXT_LENGTH:
        raise ValidationError(
            f"Input exceeds maximum allowed length of {MAX_SCAM_TEXT_LENGTH} characters."
        )

    return cleaned


def validate_news_input(text: str) -> str:
    """Validate and normalize text for fake news analysis."""
    if not isinstance(text, str):
        raise ValidationError("News text must be a string.")

    cleaned = text.strip()

    if len(cleaned) < MIN_NEWS_TEXT_LENGTH:
        raise ValidationError(
            f"Please enter at least a full sentence ({MIN_NEWS_TEXT_LENGTH}+ characters) to analyze."
        )

    if len(cleaned) > MAX_NEWS_TEXT_LENGTH:
        raise ValidationError(
            f"Article text exceeds maximum allowed length of {MAX_NEWS_TEXT_LENGTH} characters."
        )

    return cleaned


def validate_image_file(filename: str, content: bytes) -> Tuple[str, str]:
    """
    Validate uploaded image filename extension, byte size, and magic bytes.
    Returns (sanitized_extension, mime_type) if valid.
    """
    if not filename or not isinstance(filename, str):
        raise ValidationError("Invalid filename provided.")

    # Prevent directory traversal in filename
    safe_name = os.path.basename(filename)
    parts = safe_name.rsplit(".", 1)
    if len(parts) < 2:
        raise ValidationError("File has no extension.")

    ext = parts[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Invalid file type .{ext}. Allowed image types are: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}."
        )

    file_size = len(content)
    if file_size == 0:
        raise ValidationError("Uploaded file is empty (0 bytes).")

    if file_size > MAX_IMAGE_SIZE_BYTES:
        max_mb = MAX_IMAGE_SIZE_BYTES // (1024 * 1024)
        raise ValidationError(f"File size exceeds maximum allowed limit of {max_mb} MB.")

    # Magic byte verification to prevent disguised executables/scripts
    if ext == "png":
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValidationError("File content does not match standard PNG format headers.")
        mime = "image/png"
    elif ext in {"jpg", "jpeg"}:
        if not (content.startswith(b"\xff\xd8\xff") or content.startswith(b"\xff\xd8")):
            raise ValidationError("File content does not match standard JPEG format headers.")
        mime = "image/jpeg"
    elif ext == "webp":
        if len(content) < 12 or content[:4] != b"RIFF" or content[8:12] != b"WEBP":
            raise ValidationError("File content does not match standard WEBP format headers.")
        mime = "image/webp"
    else:
        raise ValidationError(f"Unsupported format: .{ext}")

    return ext, mime
