"""Plain text document parser."""

from pathlib import Path
from typing import List
from backend.app.parsers.base_parser import BaseParser, ParsedPage


class TXTParser(BaseParser):
    """Parses plain text documents with UTF-8 decoding."""

    def parse_file(self, file_path: Path) -> List[ParsedPage]:
        with open(file_path, "rb") as f:
            return self.parse_bytes(f.read(), file_path.name)

    def parse_bytes(self, content: bytes, filename: str) -> List[ParsedPage]:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback for alternative common encodings
            text = content.decode("latin-1", errors="replace")

        return [ParsedPage(page_number=1, text=text)]
