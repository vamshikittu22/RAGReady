"""Metadata utilities for document ingestion.

Provides deterministic hashing, document ID generation, and file type detection.
"""

import hashlib
from pathlib import Path

from ragready.core.exceptions import ExtractionError

# Supported file extensions mapped to canonical type names.
_EXTENSION_MAP: dict[str, str] = {
    ".pdf": "pdf",
    ".md": "markdown",
    ".markdown": "markdown",
    ".html": "html",
    ".htm": "html",
    ".txt": "plaintext",
    ".text": "plaintext",
}


def compute_content_hash(text: str) -> str:
    """Compute a truncated SHA-256 hash of text content.

    Args:
        text: The text to hash.

    Returns:
        First 16 hex characters of the SHA-256 digest.
    """
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def compute_document_id(filename: str, content_hash: str) -> str:
    """Generate a deterministic document ID from filename and content hash.

    Args:
        filename: The document filename.
        content_hash: A hash of the document content.

    Returns:
        First 16 hex characters of SHA-256("{filename}:{content_hash}").
    """
    raw = f"{filename}:{content_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def detect_file_type(file_path: Path) -> str:
    """Detect the document type from a file's extension.

    Args:
        file_path: Path to the file.

    Returns:
        A canonical type string ("pdf", "markdown", "html", "plaintext").

    Raises:
        ExtractionError: If the extension is not supported.
    """
    ext = file_path.suffix.lower()
    if ext not in _EXTENSION_MAP:
        supported = ", ".join(sorted(_EXTENSION_MAP.keys()))
        raise ExtractionError(
            f"Unsupported file extension '{ext}'. Supported: {supported}"
        )
    return _EXTENSION_MAP[ext]
