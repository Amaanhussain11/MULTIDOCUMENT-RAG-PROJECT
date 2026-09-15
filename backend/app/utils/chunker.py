"""Token-aware text chunking with metadata preservation."""

import re

from backend.app.core.config import settings
from backend.app.parsers.base_parser import ParsedPage
from backend.app.schemas.document import DocumentChunk

try:
    import tiktoken
    _TOKENIZER = tiktoken.get_encoding("cl100k_base")
except Exception:
    _TOKENIZER = None


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken, falling back to heuristic."""
    if _TOKENIZER is not None:
        return len(_TOKENIZER.encode(text, disallowed_special=()))
    # Heuristic fallback: ~0.75 words per token -> 1.3 tokens per word
    words = len(text.split())
    return max(1, int(words * 1.33))


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences while retaining punctuation and paragraphs."""
    # Split on paragraph breaks first
    paragraphs = text.split("\n\n")
    sentences: list[str] = []
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Split paragraph into sentence candidates
        parts = re.split(r"(?<=[.?!])\s+", p)
        for part in parts:
            part = part.strip()
            if part:
                sentences.append(part)

    return sentences


def create_chunks(
    pages: list[ParsedPage],
    document_id: str,
    user_id: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[DocumentChunk]:
    """
    Split parsed pages into chunks adhering to token size and overlap limits.
    
    Preserves page number metadata for source attribution.
    """
    target_chunk_size = chunk_size or settings.CHUNK_SIZE
    target_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    # Collect sentence units with their originating page numbers
    units: list[dict] = []
    for page in pages:
        cleaned_page_text = page.text.strip()
        if not cleaned_page_text:
            continue
        sentences = split_into_sentences(cleaned_page_text)
        for s in sentences:
            units.append({
                "text": s,
                "tokens": count_tokens(s),
                "page_number": page.page_number
            })

    if not units:
        return []

    chunks: list[DocumentChunk] = []
    chunk_index = 0
    start_idx = 0
    n = len(units)

    while start_idx < n:
        end_idx = start_idx
        current_tokens = 0

        # Expand window until reaching target_chunk_size (always include at least 1 unit)
        while end_idx < n and (current_tokens + units[end_idx]["tokens"] <= target_chunk_size or end_idx == start_idx):
            current_tokens += units[end_idx]["tokens"]
            end_idx += 1

        # Create chunk from units[start_idx:end_idx]
        chunk_units = units[start_idx:end_idx]
        chunk_text = " ".join(u["text"] for u in chunk_units)
        page_number = chunk_units[0]["page_number"]
        chunk_id = f"{document_id}_c{chunk_index}"

        chunks.append(DocumentChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            user_id=user_id,
            chunk_index=chunk_index,
            text=chunk_text,
            page_number=page_number
        ))
        chunk_index += 1

        if end_idx >= n:
            break

        # Calculate next start_idx for overlap
        overlap_tokens = 0
        next_start = end_idx
        for idx in range(end_idx - 1, start_idx, -1):
            if overlap_tokens + units[idx]["tokens"] > target_overlap:
                break
            overlap_tokens += units[idx]["tokens"]
            next_start = idx

        # Strict guarantee: next start must advance by at least 1 unit
        start_idx = max(start_idx + 1, next_start)

    return chunks
