"""
Core validators — shared input and file validation helpers.
"""
from __future__ import annotations

import re

from django.core.exceptions import ValidationError


# ---------------------------------------------------------------------------
# MIME-type allowlists
# ---------------------------------------------------------------------------
ALLOWED_IMAGE_MIMES = {'image/jpeg', 'image/png', 'image/webp'}
ALLOWED_RESUME_MIMES = {'application/pdf'}
ALLOWED_CHAT_MIMES = ALLOWED_IMAGE_MIMES | ALLOWED_RESUME_MIMES | {'text/plain'}

_MB = 1024 * 1024


def _sniff_mime(file) -> str:
    """
    Read the first 1 KB of a file to detect its MIME type.
    Falls back gracefully when python-magic is not installed.
    """
    try:
        import magic  # type: ignore
        header = file.read(1024)
        file.seek(0)
        return magic.from_buffer(header, mime=True)
    except ImportError:
        # python-magic not available — skip MIME check in development
        file.seek(0)
        return 'application/octet-stream'


def validate_image(file, max_mb: int = 5) -> None:
    """Raise ValidationError if *file* is not an allowed image or exceeds *max_mb* MB."""
    mime = _sniff_mime(file)
    if mime not in ALLOWED_IMAGE_MIMES:
        raise ValidationError(
            f"Unsupported file type '{mime}'. "
            f"Allowed types: JPEG, PNG, WebP."
        )
    if file.size > max_mb * _MB:
        raise ValidationError(f"Image must be under {max_mb} MB.")


def validate_resume(file, max_mb: int = 5) -> None:
    """Raise ValidationError if *file* is not a PDF or exceeds *max_mb* MB."""
    mime = _sniff_mime(file)
    if mime not in ALLOWED_RESUME_MIMES:
        raise ValidationError("Only PDF files are accepted for resumes.")
    if file.size > max_mb * _MB:
        raise ValidationError(f"Resume must be under {max_mb} MB.")


def validate_chat_file(file, max_mb: int = 10) -> None:
    """Raise ValidationError if *file* is not in the chat allowlist or exceeds *max_mb* MB."""
    mime = _sniff_mime(file)
    if mime not in ALLOWED_CHAT_MIMES:
        raise ValidationError("Unsupported file type for chat upload.")
    if file.size > max_mb * _MB:
        raise ValidationError(f"File must be under {max_mb} MB.")


def sanitize_filename(name: str) -> str:
    """Remove dangerous characters from a filename and cap its length."""
    safe = re.sub(r'[^\w\s\-.]', '', name)
    return safe[:100]
