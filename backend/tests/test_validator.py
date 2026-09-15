"""Tests for document validation."""

from pathlib import Path

import pytest

from backend.app.utils.validator import (
    DocumentValidationError,
    validate_document_bytes,
    validate_document_file,
)


def test_validator_rejects_missing_file(tmp_path: Path):
    non_existent = tmp_path / "ghost.txt"
    with pytest.raises(DocumentValidationError) as exc:
        validate_document_file(non_existent)
    assert exc.value.code == "FILE_NOT_FOUND"


def test_validator_rejects_unsupported_extension(tmp_path: Path):
    unsupported = tmp_path / "script.py"
    unsupported.write_text("print('hello')")
    with pytest.raises(DocumentValidationError) as exc:
        validate_document_file(unsupported)
    assert exc.value.code == "UNSUPPORTED_FILE_TYPE"


def test_validator_rejects_empty_file(tmp_path: Path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    with pytest.raises(DocumentValidationError) as exc:
        validate_document_file(empty_file)
    assert exc.value.code == "EMPTY_FILE"


def test_validator_rejects_oversized_file(tmp_path: Path):
    large_file = tmp_path / "big.txt"
    large_file.write_bytes(b"A" * (2 * 1024 * 1024))
    # Test with max size of 1 MB
    with pytest.raises(DocumentValidationError) as exc:
        validate_document_file(large_file, max_size_mb=1)
    assert exc.value.code == "FILE_TOO_LARGE"


def test_validator_accepts_valid_txt_file(tmp_path: Path):
    valid_txt = tmp_path / "document.txt"
    valid_txt.write_text("Valid text content here.")
    # Should not raise
    validate_document_file(valid_txt)


def test_validator_bytes_checks_pdf_signature():
    corrupt_pdf = b"not a real pdf content"
    with pytest.raises(DocumentValidationError) as exc:
        validate_document_bytes("test.pdf", corrupt_pdf)
    assert exc.value.code == "CORRUPT_OR_INVALID_PDF"
