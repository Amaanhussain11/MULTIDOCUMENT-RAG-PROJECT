"""Tests for token-aware chunking."""

from backend.app.parsers.base_parser import ParsedPage
from backend.app.utils.chunker import count_tokens, create_chunks


def test_count_tokens_returns_positive():
    tokens = count_tokens("Hello world, this is a test sentence for token counting.")
    assert tokens > 0


def test_create_chunks_preserves_page_numbers():
    pages = [
        ParsedPage(page_number=1, text="Page 1 sentence one. Page 1 sentence two."),
        ParsedPage(page_number=2, text="Page 2 sentence one. Page 2 sentence two."),
    ]
    chunks = create_chunks(
        pages=pages,
        document_id="doc_123",
        user_id="user_abc",
        chunk_size=50,
        chunk_overlap=10
    )
    assert len(chunks) >= 1
    assert chunks[0].document_id == "doc_123"
    assert chunks[0].user_id == "user_abc"
    assert chunks[0].page_number is not None


def test_create_chunks_handles_empty_input():
    chunks = create_chunks(
        pages=[],
        document_id="doc_123",
        user_id="user_abc"
    )
    assert chunks == []


def test_create_chunks_large_1000_line_document():
    # 1000 lines of text
    lines = [f"This is line number {i} of an extensive document. It has several descriptive words." for i in range(1000)]
    pages = [ParsedPage(page_number=1, text="\n".join(lines))]
    chunks = create_chunks(
        pages=pages,
        document_id="doc_large",
        user_id="user_test",
        chunk_size=1000,
        chunk_overlap=150
    )
    assert len(chunks) > 0
    # Every chunk must be unique and properly ordered
    for idx, c in enumerate(chunks):
        assert c.chunk_index == idx
        assert c.document_id == "doc_large"
        assert c.page_start == 1
        assert c.page_end == 1


def test_create_chunks_spans_multiple_pages():
    # Two short pages that merge into a single chunk under chunk_size=200
    pages = [
        ParsedPage(page_number=4, text="Short statement on page four."),
        ParsedPage(page_number=5, text="Continuation on page five."),
    ]
    chunks = create_chunks(
        pages=pages,
        document_id="doc_multipage",
        user_id="user_test",
        chunk_size=200,
        chunk_overlap=20,
    )
    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.page_start == 4
    assert chunk.page_end == 5
    assert chunk.page_number == 4
    assert "page four" in chunk.text
    assert "page five" in chunk.text
