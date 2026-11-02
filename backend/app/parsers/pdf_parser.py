"""PDF document parser using PyMuPDF (fitz)."""

from pathlib import Path

import pymupdf as fitz

from backend.app.parsers.base_parser import BaseParser, ParsedPage
from backend.app.utils.validator import DocumentValidationError


class PDFParser(BaseParser):
    """
    Parses PDF documents into pages with 1-based page number metadata using PyMuPDF.

    Extracts text page-by-page while completely bypassing embedded images.
    Handles empty/blank pages, detects scanned/image-only PDFs (OCR required),
    and enforces explicit validation errors for corrupted or password-protected files.
    """

    def parse_file(self, file_path: Path) -> list[ParsedPage]:
        if not file_path.exists():
            raise DocumentValidationError(
                code="FILE_NOT_FOUND",
                message=f"File not found: {file_path}",
            )
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise DocumentValidationError(
                code="CORRUPT_OR_INVALID_PDF",
                message=f"File '{file_path.name}' is corrupted or not a valid PDF: {e}",
            ) from e

        return self._extract_pages_from_doc(doc, filename=file_path.name)

    def parse_bytes(self, content: bytes, filename: str) -> list[ParsedPage]:
        if not content:
            raise DocumentValidationError(
                code="EMPTY_FILE",
                message=f"The document '{filename}' is empty (0 bytes).",
            )
        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception as e:
            raise DocumentValidationError(
                code="CORRUPT_OR_INVALID_PDF",
                message=f"File '{filename}' is corrupted or not a valid PDF: {e}",
            ) from e

        return self._extract_pages_from_doc(doc, filename=filename)

    def _extract_pages_from_doc(self, doc: fitz.Document, filename: str) -> list[ParsedPage]:
        try:
            if doc.is_encrypted or doc.needs_pass:
                raise DocumentValidationError(
                    code="PASSWORD_PROTECTED_PDF",
                    message=f"File '{filename}' is password-protected. Encrypted PDFs are not supported.",
                )

            total_page_count = len(doc)
            extracted_pages: list[ParsedPage] = []

            for page_index in range(total_page_count):
                try:
                    page = doc.load_page(page_index)
                    # Extract only text streams, ignoring all image XObjects / streams
                    text = page.get_text("text")
                    if text and text.strip():
                        extracted_pages.append(
                            ParsedPage(
                                page_number=page_index + 1,
                                text=text.strip(),
                            )
                        )
                except Exception as page_err:
                    if isinstance(page_err, DocumentValidationError):
                        raise
                    raise DocumentValidationError(
                        code="CORRUPT_OR_INVALID_PDF",
                        message=f"Error reading page {page_index + 1} of '{filename}': {page_err}",
                    ) from page_err

            # Check for scanned or image-only PDF
            if total_page_count > 0 and len(extracted_pages) == 0:
                raise DocumentValidationError(
                    code="OCR_REQUIRED",
                    message=(
                        f"PDF '{filename}' contains scanned pages or images without readable text. "
                        "OCR is required to extract text from this document."
                    ),
                )

            return extracted_pages
        finally:
            doc.close()
