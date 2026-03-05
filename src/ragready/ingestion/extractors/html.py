"""HTML text extractor using BeautifulSoup4.

Strips HTML tags while preserving meaningful text content.
Removes noise elements (script, style, nav, footer, header)
before extraction.
"""

from pathlib import Path

from bs4 import BeautifulSoup

from ragready.core.exceptions import ExtractionError
from ragready.ingestion.extractors.base import ExtractedDocument


class HTMLExtractor:
    """Extract text from HTML documents using BeautifulSoup4.

    Removes script, style, nav, footer, and header elements
    before extracting text to reduce noise.
    """

    supported_extensions: list[str] = [".html", ".htm"]

    # Elements to remove before text extraction (noise)
    NOISE_TAGS = ["script", "style", "nav", "footer", "header"]

    def extract(self, file_path: Path) -> ExtractedDocument:
        """Extract text from an HTML file.

        Args:
            file_path: Path to the HTML file.

        Returns:
            ExtractedDocument with cleaned text and title metadata.

        Raises:
            ExtractionError: If the file cannot be read or parsed.
        """
        try:
            raw_html = file_path.read_text(encoding="utf-8")
        except Exception as e:
            raise ExtractionError(
                f"Failed to read HTML file '{file_path.name}': {e}"
            ) from e

        try:
            soup = BeautifulSoup(raw_html, "html.parser")
        except Exception as e:
            raise ExtractionError(
                f"Failed to parse HTML in '{file_path.name}': {e}"
            ) from e

        # Extract title before removing elements
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None

        # Remove noise elements
        for tag_name in self.NOISE_TAGS:
            for element in soup.find_all(tag_name):
                element.decompose()

        # Extract text with newline separators
        text = soup.get_text(separator="\n", strip=True)

        metadata: dict = {
            "source_file": str(file_path),
            "file_type": "html",
            "file_size": file_path.stat().st_size,
        }
        if title:
            metadata["title"] = title

        return ExtractedDocument(text=text, metadata=metadata)
