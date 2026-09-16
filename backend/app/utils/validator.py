"""Validation utility for uploaded documents."""

from pathlib import Path

from backend.app.core.config import settings


class DocumentValidationError(Exception):
    """Exception raised when document validation fails."""
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self):
        return {
            "error": {
                "code": self.code,
                "message": self.message
            }
        }


def validate_document_file(file_path: Path, max_size_mb: int | None = None) -> None:
    """Validate a document from a local file path before ingestion."""
    if not file_path.exists():
        raise DocumentValidationError(
            code="FILE_NOT_FOUND",
            message=f"File not found: {file_path}"
        )

    if not file_path.is_file():
        raise DocumentValidationError(
            code="NOT_A_FILE",
            message=f"Path is not a regular file: {file_path}"
        )

    extension = file_path.suffix.lower()
    validate_document_metadata(
        filename=file_path.name,
        extension=extension,
        file_size=file_path.stat().st_size,
        max_size_mb=max_size_mb
    )


def validate_document_bytes(
    filename: str,
    content: bytes,
    max_size_mb: int | None = None
) -> None:
    """Validate raw document bytes and metadata."""
    extension = Path(filename).suffix.lower()
    validate_document_metadata(
        filename=filename,
        extension=extension,
        file_size=len(content),
        max_size_mb=max_size_mb
    )

    # Check for empty content
    if len(content.strip()) == 0:
        raise DocumentValidationError(
            code="EMPTY_FILE",
            message=f"The document '{filename}' is empty."
        )

    # Basic magic number / header verification for known file formats
    _verify_file_signature(content, extension, filename)


def validate_document_metadata(
    filename: str,
    extension: str,
    file_size: int,
    max_size_mb: int | None = None
) -> None:
    """Validate extension and size constraints."""
    if not extension:
        raise DocumentValidationError(
            code="MISSING_EXTENSION",
            message=f"File '{filename}' has no extension."
        )

    if extension not in settings.SUPPORTED_EXTENSIONS:
        raise DocumentValidationError(
            code="UNSUPPORTED_FILE_TYPE",
            message=f"Extension '{extension}' is not supported. Supported extensions: {sorted(list(settings.SUPPORTED_EXTENSIONS))}"
        )

    if file_size == 0:
        raise DocumentValidationError(
            code="EMPTY_FILE",
            message=f"The document '{filename}' is empty (0 bytes)."
        )

    limit_mb = max_size_mb if max_size_mb is not None else settings.MAX_FILE_SIZE_MB
    max_bytes = limit_mb * 1024 * 1024
    if file_size > max_bytes:
        raise DocumentValidationError(
            code="FILE_TOO_LARGE",
            message=f"File '{filename}' size ({file_size / (1024 * 1024):.2f}MB) exceeds maximum limit of {limit_mb}MB."
        )


def _verify_file_signature(content: bytes, extension: str, filename: str) -> None:
    """Verify magic bytes to prevent corruption or misleading file extensions."""
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise DocumentValidationError(
            code="CORRUPT_OR_INVALID_PDF",
            message=f"File '{filename}' does not have a valid PDF header."
        )
    if extension == ".docx" and not content.startswith(b"PK\x03\x04"):
        raise DocumentValidationError(
            code="CORRUPT_OR_INVALID_DOCX",
            message=f"File '{filename}' does not have a valid DOCX/ZIP header."
        )

