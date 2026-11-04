"""Tests for document parsers."""

from pathlib import Path

import pymupdf as fitz
import pytest

from backend.app.parsers import PDFParser, TXTParser, get_parser
from backend.app.utils.validator import DocumentValidationError


def test_txt_parser(tmp_path: Path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("This is line one.\nThis is line two.")

    parser = get_parser(".txt")
    assert isinstance(parser, TXTParser)

    pages = parser.parse_file(txt_file)
    assert len(pages) == 1
    assert "line one" in pages[0].text
    assert "line two" in pages[0].text


def test_get_parser_unsupported_raises():
    with pytest.raises(ValueError):
        get_parser(".unknown")


def test_pdf_parser_normal_text(tmp_path: Path):
    pdf_file = tmp_path / "test_normal.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "First paragraph of readable text.")
    page.insert_text((50, 80), "Second paragraph of readable text.")
    doc.save(str(pdf_file))
    doc.close()

    parser = get_parser(".pdf")
    assert isinstance(parser, PDFParser)

    pages = parser.parse_file(pdf_file)
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "First paragraph of readable text." in pages[0].text
    assert "Second paragraph of readable text." in pages[0].text


def test_pdf_parser_embedded_images_ignored(tmp_path: Path):
    pdf_file = tmp_path / "test_images.pdf"
    doc = fitz.open()
    page = doc.new_page()
    pix = fitz.Pixmap(fitz.csRGB, (0, 0, 20, 20), 0)
    page.insert_image(fitz.Rect(50, 50, 150, 150), pixmap=pix)
    page.insert_text((50, 200), "Grounded text extractable beside image.")
    doc.save(str(pdf_file))
    doc.close()

    parser = PDFParser()
    pages = parser.parse_file(pdf_file)
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Grounded text extractable beside image." in pages[0].text


def test_pdf_parser_mixed_text_and_image_pages(tmp_path: Path):
    pdf_file = tmp_path / "test_mixed.pdf"
    doc = fitz.open()
    # Page 1: image + text
    page1 = doc.new_page()
    pix = fitz.Pixmap(fitz.csRGB, (0, 0, 10, 10), 0)
    page1.insert_image(fitz.Rect(20, 20, 80, 80), pixmap=pix)
    page1.insert_text((20, 100), "Page 1 Content with Image")

    # Page 2: text only
    page2 = doc.new_page()
    page2.insert_text((20, 100), "Page 2 Pure Text Content")

    doc.save(str(pdf_file))
    doc.close()

    parser = PDFParser()
    pages = parser.parse_file(pdf_file)
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert "Page 1 Content with Image" in pages[0].text
    assert pages[1].page_number == 2
    assert "Page 2 Pure Text Content" in pages[1].text


def test_pdf_parser_multipage_numbering(tmp_path: Path):
    pdf_file = tmp_path / "test_multipage.pdf"
    doc = fitz.open()
    for i in range(1, 4):
        p = doc.new_page()
        p.insert_text((50, 50), f"Section {i} text on page {i}.")
    doc.save(str(pdf_file))
    doc.close()

    parser = PDFParser()
    pages = parser.parse_file(pdf_file)
    assert len(pages) == 3
    for idx, page in enumerate(pages):
        assert page.page_number == idx + 1
        assert f"Section {idx + 1}" in page.text


def test_pdf_parser_blank_pages_skipped(tmp_path: Path):
    pdf_file = tmp_path / "test_blank_pages.pdf"
    doc = fitz.open()
    # Page 1: has text
    p1 = doc.new_page()
    p1.insert_text((50, 50), "Page 1 content")

    # Page 2: completely blank
    doc.new_page()

    # Page 3: has text
    p3 = doc.new_page()
    p3.insert_text((50, 50), "Page 3 content")

    doc.save(str(pdf_file))
    doc.close()

    parser = PDFParser()
    pages = parser.parse_file(pdf_file)
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert "Page 1 content" in pages[0].text
    assert pages[1].page_number == 3
    assert "Page 3 content" in pages[1].text


def test_pdf_parser_scanned_image_only_raises_ocr_required(tmp_path: Path):
    pdf_file = tmp_path / "test_scanned.pdf"
    doc = fitz.open()
    page = doc.new_page()
    pix = fitz.Pixmap(fitz.csRGB, (0, 0, 10, 10), 0)
    page.insert_image(fitz.Rect(50, 50, 150, 150), pixmap=pix)
    doc.save(str(pdf_file))
    doc.close()

    parser = PDFParser()
    with pytest.raises(DocumentValidationError) as exc_info:
        parser.parse_file(pdf_file)
    assert exc_info.value.code == "OCR_REQUIRED"
    assert "OCR is required" in exc_info.value.message


def test_pdf_parser_corrupted_pdf_raises():
    parser = PDFParser()
    with pytest.raises(DocumentValidationError) as exc_info:
        parser.parse_bytes(b"%PDF-corrupted-stream-bytes-here", "corrupted.pdf")
    assert exc_info.value.code == "CORRUPT_OR_INVALID_PDF"


def test_pdf_parser_password_protected_pdf_raises(tmp_path: Path):
    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((50, 50), "Confidential data")
    pdf_bytes = doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="secret123")
    doc.close()

    parser = PDFParser()
    with pytest.raises(DocumentValidationError) as exc_info:
        parser.parse_bytes(pdf_bytes, "encrypted.pdf")
    assert exc_info.value.code == "PASSWORD_PROTECTED_PDF"
    assert "password-protected" in exc_info.value.message
