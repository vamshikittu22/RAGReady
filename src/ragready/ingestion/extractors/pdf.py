"""PDF text extractor using PyMuPDF (fitz)."""

from pathlib import Path

import fitz  # PyMuPDF

from ragready.core.exceptions import ExtractionError
from ragready.ingestion.extractors.base import ExtractedDocument


class PDFExtractor:
    """Extract text from PDF documents using PyMuPDF.

    Extracts text page-by-page and joins with double newlines
    to preserve page boundaries.
    """

    supported_extensions: list[str] = [".pdf"]

    def extract(self, file_path: Path) -> ExtractedDocument:
        """Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            ExtractedDocument with extracted text and page_count metadata.

        Raises:
            ExtractionError: If the PDF is empty, has no text, or is corrupted.
        """
        try:
            doc = fitz.open(str(file_path))
        except Exception as e:
            raise ExtractionError(
                f"Failed to open PDF '{file_path.name}': {e}"
            ) from e

        try:
            page_count = len(doc)
            if page_count == 0:
                raise ExtractionError(
                    f"PDF '{file_path.name}' has 0 pages."
                )

            pages_text: list[str] = []
            for page in doc:
                text = page.get_text("text")
                if text.strip():
                    pages_text.append(text.strip())

            if not pages_text:
                raise ExtractionError(
                    f"PDF '{file_path.name}' has {page_count} page(s) but no extractable text."
                )

            full_text = "\n\n".join(pages_text)

            return ExtractedDocument(
                text=full_text,
                metadata={
                    "source_file": str(file_path),
                    "file_type": "pdf",
                    "page_count": page_count,
                },
            )
        finally:
            doc.close()
