"""Document parsers package."""



from backend.app.parsers.base_parser import BaseParser, ParsedPage
from backend.app.parsers.docx_parser import DOCXParser
from backend.app.parsers.pdf_parser import PDFParser
from backend.app.parsers.txt_parser import TXTParser

PARSER_REGISTRY: dict[str, type[BaseParser]] = {
    ".pdf": PDFParser,
    ".docx": DOCXParser,
    ".txt": TXTParser,
}


def get_parser(extension: str) -> BaseParser:
    """Retrieve the corresponding parser for a given file extension."""
    clean_ext = extension.lower().strip()
    if not clean_ext.startswith("."):
        clean_ext = f".{clean_ext}"

    parser_cls = PARSER_REGISTRY.get(clean_ext)
    if not parser_cls:
        raise ValueError(f"Unsupported file extension: '{extension}'. Supported: {list(PARSER_REGISTRY.keys())}")
    return parser_cls()


__all__ = [
    "BaseParser",
    "ParsedPage",
    "PDFParser",
    "DOCXParser",
    "TXTParser",
    "get_parser",
    "PARSER_REGISTRY",
]
