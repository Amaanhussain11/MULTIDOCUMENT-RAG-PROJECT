"""Tests for document parsers."""

from pathlib import Path

from backend.app.parsers import TXTParser, get_parser


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
    import pytest
    with pytest.raises(ValueError):
        get_parser(".unknown")
