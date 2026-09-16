"""Base parser interface and data structures."""

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel


class ParsedPage(BaseModel):
    """Represents text extracted from a document page or section."""
    page_number: int | None = None
    text: str


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def parse_file(self, file_path: Path) -> list[ParsedPage]:
        """Parse a document file from a local filesystem path."""
        pass

    @abstractmethod
    def parse_bytes(self, content: bytes, filename: str) -> list[ParsedPage]:
        """Parse a document directly from raw bytes."""
        pass
