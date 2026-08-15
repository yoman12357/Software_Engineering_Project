"""Text cleaning and normalization for RAG ingestion."""

from __future__ import annotations

import re
import unicodedata


def clean_text(text: str) -> str:
    """Clean raw extracted text.

    Args:
        text: Raw text from document parsing.

    Returns:
        Cleaned text.
    """
    if not text:
        return ""

    # Normalize Unicode (NFC)
    text = unicodedata.normalize("NFC", text)

    # Remove non-UTF-8 characters (replace with space)
    text = text.encode("utf-8", errors="replace").decode("utf-8")

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove common header/footer patterns (page numbers, etc.)
    # Common patterns: "Page X", "X of Y", "X / Y"
    text = re.sub(r"\b(?:page|p\.?)\s*\d+\s*(?:of|/)\s*\d+\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*\d+\s*$", " ", text, flags=re.MULTILINE)  # Standalone page numbers

    # Remove excessive whitespace
    # Replace multiple spaces with single space
    text = re.sub(r"[ \t]+", " ", text)
    # Replace multiple newlines with double newline (paragraph separator)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Trim leading/trailing whitespace
    text = text.strip()

    return text


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace while preserving paragraph structure.

    Args:
        text: Input text.

    Returns:
        Text with normalized whitespace.
    """
    if not text:
        return ""

    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Collapse multiple spaces
    text = re.sub(r"[ ]{2,}", " ", text)

    # Ensure paragraphs are separated by exactly two newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def extract_section_heading(text: str, max_length: int = 200) -> str | None:
    """Extract a section heading from the beginning of text.

    Args:
        text: Text to extract heading from.
        max_length: Maximum length of heading to consider.

    Returns:
        Extracted heading or None.
    """
    if not text:
        return None

    # Look at first few lines
    lines = text[:max_length].split("\n")
    for line in lines[:5]:
        line = line.strip()
        if not line:
            continue
        # Check for heading patterns
        if re.match(r"^(#{1,6}\s+|(?:\d+\.)+\s+|[A-Z][A-Z\s]{2,}:?\s*)", line):
            return line.strip()

    return None


def split_into_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs.

    Args:
        text: Input text.

    Returns:
        List of paragraphs.
    """
    if not text:
        return []

    # Split on double newline
    paragraphs = [p.strip() for p in text.split("\n\n")]
    return [p for p in paragraphs if p]


def count_tokens_estimate(text: str) -> int:
    """Estimate token count for text.

    Uses rough approximation: ~4 characters per token for English.

    Args:
        text: Input text.

    Returns:
        Estimated token count.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)
