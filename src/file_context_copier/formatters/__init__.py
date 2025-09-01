"""Output formatters for file-context-copier."""

from .base import BaseFormatter
from .markdown import MarkdownFormatter
from .txt import TxtFormatter

# Available formatters registry - just the two requested formats
FORMATTERS = {
    "markdown": MarkdownFormatter,
    "txt": TxtFormatter,
}


def get_formatter(format_name: str) -> BaseFormatter:
    """Get formatter instance for specified format."""
    formatter_class = FORMATTERS.get(format_name.lower())
    if not formatter_class:
        raise ValueError(f"Unknown format: {format_name}. Available: {list(FORMATTERS.keys())}")
    return formatter_class()


__all__ = [
    "BaseFormatter",
    "MarkdownFormatter", 
    "TxtFormatter",
    "FORMATTERS",
    "get_formatter"
]