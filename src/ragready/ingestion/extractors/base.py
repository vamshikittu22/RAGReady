"""Base extractor interface and registry for document text extraction."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from ragready.core.exceptions import ExtractionError


class ExtractedDocument(BaseModel):
    """Result of text extraction from a document.

    Attributes:
        text: The extracted plain text content.
        metadata: Extraction metadata (source_file, file_type, page_count, etc.)
    """

    text: str
    metadata: dict


@runtime_checkable
class BaseExtractor(Protocol):
    """Protocol defining the extractor interface.

    All extractors must implement `extract` and declare `supported_extensions`.
    """

    supported_extensions: list[str]

    def extract(self, file_path: Path) -> ExtractedDocument:
        """Extract text from a file.

        Args:
            file_path: Path to the file to extract text from.

        Returns:
            ExtractedDocument with extracted text and metadata.

        Raises:
            ExtractionError: If extraction fails.
        """
        ...


class ExtractorRegistry:
    """Maps file extensions to extractor instances.

    Provides a unified interface for extracting text from any supported
    document format.
    """

    def __init__(self) -> None:
        self._extractors: dict[str, BaseExtractor] = {}

    def register(self, extractor: BaseExtractor) -> None:
        """Register an extractor for its supported extensions."""
        for ext in extractor.supported_extensions:
            self._extractors[ext.lower()] = extractor

    def get_extractor(self, file_path: Path) -> BaseExtractor:
        """Look up the extractor for a file by its extension.

        Args:
            file_path: Path to the file.

        Returns:
            The appropriate extractor.

        Raises:
            ExtractionError: If the file extension is not supported.
        """
        ext = file_path.suffix.lower()
        if ext not in self._extractors:
            supported = ", ".join(sorted(self._extractors.keys()))
            raise ExtractionError(
                f"Unsupported file extension '{ext}'. "
                f"Supported extensions: {supported}"
            )
        return self._extractors[ext]

    def extract(self, file_path: Path) -> ExtractedDocument:
        """Convenience method: get extractor and extract text.

        Args:
            file_path: Path to the file.

        Returns:
            ExtractedDocument with extracted text and metadata.

        Raises:
            ExtractionError: If the file extension is unsupported or extraction fails.
        """
        extractor = self.get_extractor(file_path)
        return extractor.extract(file_path)
