"""Document text extractors for various file formats.

Provides a registry-based architecture for extracting text from
PDF, Markdown, HTML, and plaintext documents.
"""

from ragready.ingestion.extractors.base import ExtractedDocument, ExtractorRegistry
from ragready.ingestion.extractors.html import HTMLExtractor
from ragready.ingestion.extractors.markdown import MarkdownExtractor
from ragready.ingestion.extractors.pdf import PDFExtractor
from ragready.ingestion.extractors.plaintext import PlaintextExtractor


def create_default_registry() -> ExtractorRegistry:
    """Create an ExtractorRegistry with all built-in extractors registered."""
    registry = ExtractorRegistry()
    registry.register(PDFExtractor())
    registry.register(MarkdownExtractor())
    registry.register(HTMLExtractor())
    registry.register(PlaintextExtractor())
    return registry


__all__ = [
    "ExtractedDocument",
    "ExtractorRegistry",
    "PDFExtractor",
    "MarkdownExtractor",
    "HTMLExtractor",
    "PlaintextExtractor",
    "create_default_registry",
]
