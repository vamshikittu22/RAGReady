"""Plaintext file extractor.

Reads plain text files with UTF-8 encoding, falling back to
latin-1 if UTF-8 decoding fails.
"""

from pathlib import Path

from ragready.core.exceptions import ExtractionError
from ragready.ingestion.extractors.base import ExtractedDocument


class PlaintextExtractor:
    """Extract text from plain text files.

    Attempts UTF-8 encoding first, falls back to latin-1 if
    UTF-8 decoding fails.
    """

    supported_extensions: list[str] = [".txt", ".text"]

    def extract(self, file_path: Path) -> ExtractedDocument:
        """Extract text from a plaintext file.

        Args:
            file_path: Path to the text file.

        Returns:
            ExtractedDocument with file content and file_size metadata.

        Raises:
            ExtractionError: If the file cannot be read.
        """
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = file_path.read_text(encoding="latin-1")
            except Exception as e:
                raise ExtractionError(
                    f"Failed to read text file '{file_path.name}' "
                    f"with UTF-8 or latin-1 encoding: {e}"
                ) from e
        except Exception as e:
            raise ExtractionError(
                f"Failed to read text file '{file_path.name}': {e}"
            ) from e

        return ExtractedDocument(
            text=text,
            metadata={
                "source_file": str(file_path),
                "file_type": "plaintext",
                "file_size": file_path.stat().st_size,
            },
        )
