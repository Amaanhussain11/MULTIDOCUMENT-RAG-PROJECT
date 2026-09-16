"""PDF document parser using pypdf."""

import io
from pathlib import Path

import pypdf

from backend.app.parsers.base_parser import BaseParser, ParsedPage


class PDFParser(BaseParser):
    """Parses PDF documents into pages with page number metadata."""

    def parse_file(self, file_path: Path) -> list[ParsedPage]:
        with open(file_path, "rb") as f:
            return self.parse_bytes(f.read(), file_path.name)

    def parse_bytes(self, content: bytes, filename: str) -> list[ParsedPage]:
        pages: list[ParsedPage] = []
        stream = io.BytesIO(content)
        reader = pypdf.PdfReader(stream)

        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            pages.append(ParsedPage(page_number=idx + 1, text=page_text))

        return pages
