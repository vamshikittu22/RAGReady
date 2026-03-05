"""Markdown text extractor.

Returns raw markdown text without conversion. Markdown is already
readable text — stripping formatting would lose section headers
that inform chunking.
"""

from pathlib import Path

from ragready.core.exceptions import ExtractionError
from ragready.ingestion.extractors.base import ExtractedDocument


class MarkdownExtractor:
    """Extract text from Markdown files.

    Returns the raw markdown content as-is, preserving headers
    and formatting that aid downstream chunking.
    """

    supported_extensions: list[str] = [".md", ".markdown"]

    def extract(self, file_path: Path) -> ExtractedDocument:
        """Extract text from a Markdown file.

        Args:
            file_path: Path to the Markdown file.

        Returns:
            ExtractedDocument with raw markdown text and file_size metadata.

        Raises:
            ExtractionError: If the file cannot be read.
        """
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception as e:
            raise ExtractionError(
                f"Failed to read Markdown file '{file_path.name}': {e}"
            ) from e

        return ExtractedDocument(
            text=text,
            metadata={
                "source_file": str(file_path),
                "file_type": "markdown",
                "file_size": file_path.stat().st_size,
            },
        )
