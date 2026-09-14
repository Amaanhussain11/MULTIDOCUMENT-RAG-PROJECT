"""Tests for text cleaning and normalization."""

from backend.app.utils.cleaner import clean_text


def test_clean_text_normalizes_unicode():
    # Full-width characters and ligature "ﬁ"
    raw = "Ｔｈｉｓ is a ﬁne test."
    cleaned = clean_text(raw)
    assert cleaned == "This is a fine test."


def test_clean_text_collapses_whitespace_and_newlines():
    raw = "Line 1.   \t  \n\n\n\n\nLine 2    with    spaces."
    cleaned = clean_text(raw)
    assert cleaned == "Line 1.\n\nLine 2 with spaces."


def test_clean_text_removes_control_characters_and_nulls():
    raw = "Hello\x00 World\x0c!\x07"
    cleaned = clean_text(raw)
    assert cleaned == "Hello World\n!"


def test_clean_text_repairs_hyphenated_line_breaks():
    raw = "The system sup-\nports multi-document ingestion."
    cleaned = clean_text(raw)
    assert "supports" in cleaned
