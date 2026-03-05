"""Unit tests for document text extractors."""

from pathlib import Path

import fitz  # PyMuPDF
import pytest

from ragready.core.exceptions import ExtractionError
from ragready.ingestion.extractors import create_default_registry
from ragready.ingestion.extractors.html import HTMLExtractor
from ragready.ingestion.extractors.markdown import MarkdownExtractor
from ragready.ingestion.extractors.pdf import PDFExtractor
from ragready.ingestion.extractors.plaintext import PlaintextExtractor


# ── PDF Extractor Tests ──────────────────────────────────────────────────


class TestPDFExtractor:
    """Tests for PDFExtractor."""

    def _create_pdf(self, path: Path, text: str, pages: int = 1) -> None:
        """Create a small PDF with text programmatically."""
        doc = fitz.open()
        for i in range(pages):
            page = doc.new_page()
            page_text = f"{text} (page {i + 1})" if pages > 1 else text
            page.insert_text((72, 72), page_text, fontsize=12)
        doc.save(str(path))
        doc.close()

    def test_extract_single_page(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "test.pdf"
        self._create_pdf(pdf_path, "Hello PDF world")

        extractor = PDFExtractor()
        result = extractor.extract(pdf_path)

        assert "Hello PDF world" in result.text
        assert result.metadata["file_type"] == "pdf"
        assert result.metadata["page_count"] == 1
        assert result.metadata["source_file"] == str(pdf_path)

    def test_extract_multi_page(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "multi.pdf"
        self._create_pdf(pdf_path, "Content", pages=3)

        extractor = PDFExtractor()
        result = extractor.extract(pdf_path)

        assert "Content (page 1)" in result.text
        assert "Content (page 3)" in result.text
        assert result.metadata["page_count"] == 3

    def test_corrupted_pdf_raises_error(self, tmp_path: Path) -> None:
        bad_pdf = tmp_path / "bad.pdf"
        bad_pdf.write_bytes(b"not a real pdf file contents random garbage")

        extractor = PDFExtractor()
        with pytest.raises(ExtractionError, match="Failed to open PDF"):
            extractor.extract(bad_pdf)

    def test_empty_pdf_raises_error(self, tmp_path: Path) -> None:
        """A PDF with pages but no text should raise ExtractionError."""
        pdf_path = tmp_path / "empty.pdf"
        doc = fitz.open()
        doc.new_page()  # blank page, no text
        doc.save(str(pdf_path))
        doc.close()

        extractor = PDFExtractor()
        with pytest.raises(ExtractionError, match="no extractable text"):
            extractor.extract(pdf_path)


# ── Markdown Extractor Tests ─────────────────────────────────────────────


class TestMarkdownExtractor:
    """Tests for MarkdownExtractor."""

    def test_extract_markdown(self, tmp_path: Path) -> None:
        md_path = tmp_path / "test.md"
        content = "# Hello\n\nThis is **bold** text.\n\n## Section 2\n\nMore content here."
        md_path.write_text(content, encoding="utf-8")

        extractor = MarkdownExtractor()
        result = extractor.extract(md_path)

        # Raw markdown preserved (not converted to HTML)
        assert "# Hello" in result.text
        assert "**bold**" in result.text
        assert "## Section 2" in result.text
        assert result.metadata["file_type"] == "markdown"
        assert result.metadata["file_size"] > 0

    def test_extract_markdown_alternate_extension(self, tmp_path: Path) -> None:
        md_path = tmp_path / "test.markdown"
        md_path.write_text("# Test", encoding="utf-8")

        extractor = MarkdownExtractor()
        result = extractor.extract(md_path)
        assert "# Test" in result.text


# ── HTML Extractor Tests ─────────────────────────────────────────────────


class TestHTMLExtractor:
    """Tests for HTMLExtractor."""

    SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
    <header><nav><a href="/">Home</a></nav></header>
    <script>console.log("noise");</script>
    <style>.noise { color: red; }</style>
    <main>
        <h1>Main Content</h1>
        <p>This is important text.</p>
    </main>
    <footer>Copyright 2026</footer>
</body>
</html>"""

    def test_extract_html_strips_tags(self, tmp_path: Path) -> None:
        html_path = tmp_path / "test.html"
        html_path.write_text(self.SAMPLE_HTML, encoding="utf-8")

        extractor = HTMLExtractor()
        result = extractor.extract(html_path)

        assert "Main Content" in result.text
        assert "important text" in result.text
        assert result.metadata["file_type"] == "html"
        assert result.metadata["title"] == "Test Page"

    def test_extract_html_removes_noise_tags(self, tmp_path: Path) -> None:
        html_path = tmp_path / "test.html"
        html_path.write_text(self.SAMPLE_HTML, encoding="utf-8")

        extractor = HTMLExtractor()
        result = extractor.extract(html_path)

        # script, style, nav, footer, header content should be removed
        assert "console.log" not in result.text
        assert ".noise" not in result.text
        assert "Copyright 2026" not in result.text
        assert "Home" not in result.text  # nav link

    def test_extract_html_no_title(self, tmp_path: Path) -> None:
        html_path = tmp_path / "notitle.html"
        html_path.write_text("<p>Just text</p>", encoding="utf-8")

        extractor = HTMLExtractor()
        result = extractor.extract(html_path)

        assert "Just text" in result.text
        assert "title" not in result.metadata

    def test_extract_htm_extension(self, tmp_path: Path) -> None:
        htm_path = tmp_path / "test.htm"
        htm_path.write_text("<p>HTM content</p>", encoding="utf-8")

        extractor = HTMLExtractor()
        result = extractor.extract(htm_path)
        assert "HTM content" in result.text


# ── Plaintext Extractor Tests ────────────────────────────────────────────


class TestPlaintextExtractor:
    """Tests for PlaintextExtractor."""

    def test_extract_utf8(self, tmp_path: Path) -> None:
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("Hello plain text world!", encoding="utf-8")

        extractor = PlaintextExtractor()
        result = extractor.extract(txt_path)

        assert result.text == "Hello plain text world!"
        assert result.metadata["file_type"] == "plaintext"
        assert result.metadata["file_size"] > 0

    def test_extract_latin1_fallback(self, tmp_path: Path) -> None:
        txt_path = tmp_path / "latin1.txt"
        # Write bytes that are valid latin-1 but not valid UTF-8
        txt_path.write_bytes(b"Caf\xe9 au lait")

        extractor = PlaintextExtractor()
        result = extractor.extract(txt_path)

        assert "Caf" in result.text
        assert result.metadata["file_type"] == "plaintext"

    def test_extract_text_extension(self, tmp_path: Path) -> None:
        txt_path = tmp_path / "test.text"
        txt_path.write_text("Text extension", encoding="utf-8")

        extractor = PlaintextExtractor()
        result = extractor.extract(txt_path)
        assert "Text extension" in result.text


# ── ExtractorRegistry Tests ──────────────────────────────────────────────


class TestExtractorRegistry:
    """Tests for ExtractorRegistry and create_default_registry."""

    def test_default_registry_has_all_extensions(self) -> None:
        registry = create_default_registry()
        expected = {".pdf", ".md", ".markdown", ".html", ".htm", ".txt", ".text"}
        assert set(registry._extractors.keys()) == expected

    def test_registry_selects_correct_extractor(self) -> None:
        registry = create_default_registry()

        assert isinstance(registry.get_extractor(Path("doc.pdf")), PDFExtractor)
        assert isinstance(registry.get_extractor(Path("doc.md")), MarkdownExtractor)
        assert isinstance(registry.get_extractor(Path("doc.html")), HTMLExtractor)
        assert isinstance(registry.get_extractor(Path("doc.txt")), PlaintextExtractor)

    def test_registry_unsupported_extension(self) -> None:
        registry = create_default_registry()
        with pytest.raises(ExtractionError, match="Unsupported file extension '.docx'"):
            registry.get_extractor(Path("document.docx"))

    def test_registry_extract_convenience(self, tmp_path: Path) -> None:
        registry = create_default_registry()
        txt_path = tmp_path / "via_registry.txt"
        txt_path.write_text("Registry test", encoding="utf-8")

        result = registry.extract(txt_path)
        assert "Registry test" in result.text

    def test_registry_case_insensitive(self) -> None:
        registry = create_default_registry()
        # Extensions are stored lowercased
        assert isinstance(registry.get_extractor(Path("doc.PDF")), PDFExtractor)
        assert isinstance(registry.get_extractor(Path("doc.Html")), HTMLExtractor)
