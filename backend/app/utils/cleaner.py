"""Text cleaning and normalization utility."""

import re
import unicodedata


def clean_text(raw_text: str) -> str:
    """
    Clean and normalize extracted document text.
    
    Performs:
    - Unicode normalization (NFKC)
    - Removal of null bytes and non-printable control characters
    - Normalization of line breaks
    - De-hyphenation across line breaks (e.g. 'exam-\nple' -> 'example')
    - Collapsing excessive spaces and blank lines
    - Removal of extraction artifacts
    """
    if not raw_text:
        return ""

    # 1. Unicode normalization (NFKC)
    text = unicodedata.normalize("NFKC", raw_text)

    # 2. Normalize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Replace form feeds and null characters
    text = text.replace("\x0c", "\n").replace("\x00", "")

    # 4. Filter out other unprintable control characters except \n and \t
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or unicodedata.category(ch)[0] != "C")

    # 5. Fix hyphenated words broken across lines: e.g. "contin-\nued" -> "continued"
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

    # 6. Normalize whitespace per line (tabs and multiple spaces -> single space)
    lines = []
    for line in text.split("\n"):
        cleaned_line = re.sub(r"[^\S\n]+", " ", line).strip()
        lines.append(cleaned_line)

    text = "\n".join(lines)

    # 7. Collapse more than 2 consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
