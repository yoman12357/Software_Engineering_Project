"""Document parsers for RAG ingestion.

Implements safe parsing for PDF, Markdown, and CSV formats.
Extracts text with structural metadata (headings, page numbers).
"""

from __future__ import annotations

import csv
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz  # type: ignore  # PyMuPDF

from ..core.config import Settings


@dataclass
class ParsedDocument:
    """Result of parsing a document."""

    text: str
    sections: list[DocumentSection]
    metadata: dict[str, Any]


@dataclass
class DocumentSection:
    """A section within a document with heading and content."""

    heading: str
    level: int  # heading level (1, 2, 3...)
    content: str
    page_number: int | None = None
    start_char: int = 0
    end_char: int = 0


class DocumentParserError(Exception):
    """Raised when document parsing fails."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Document parsing failed: {message}")


class DocumentParser(ABC):
    """Abstract base class for document parsers."""

    @property
    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Return the file extensions this parser supports."""

    @abstractmethod
    def parse(self, file_path: Path, settings: Settings) -> ParsedDocument:
        """Parse a document file.

        Args:
            file_path: Path to the document file.
            settings: Application settings.

        Returns:
            ParsedDocument with text, sections, and metadata.

        Raises:
            DocumentParserError: If parsing fails.
        """

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in self.supported_extensions


class PDFParser(DocumentParser):
    """Parse PDF documents using PyMuPDF.

    Extracts text with page numbers and heading detection.
    """

    supported_extensions = {".pdf"}

    def parse(self, file_path: Path, settings: Settings) -> ParsedDocument:
        """Parse a PDF file.

        Args:
            file_path: Path to the PDF file.
            settings: Application settings.

        Returns:
            ParsedDocument with extracted text and sections.
        """
        if not file_path.exists():
            raise DocumentParserError(f"File not found: {file_path}")

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise DocumentParserError(f"Failed to open PDF: {e}") from e

        sections = []
        full_text_parts = []
        char_offset = 0

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text("text")

                if not page_text.strip():
                    continue

                # Detect headings in the page text
                page_sections = self._extract_sections(page_text, page_num + 1, char_offset)

                for section in page_sections:
                    sections.append(section)
                    full_text_parts.append(section.content)
                    char_offset = section.end_char

            full_text = "\n\n".join(full_text_parts)

            metadata = {
                "page_count": len(doc),
                "parser": "pymupdf",
            }

            return ParsedDocument(
                text=full_text,
                sections=sections,
                metadata=metadata,
            )

        finally:
            doc.close()

    def _extract_sections(
        self,
        page_text: str,
        page_num: int,
        base_offset: int,
    ) -> list[DocumentSection]:
        """Extract sections from page text using heading detection.

        Args:
            page_text: Raw text from the page.
            page_num: Page number (1-indexed).
            base_offset: Character offset base for this page.

        Returns:
            List of DocumentSection objects.
        """
        sections = []
        lines = page_text.split("\n")

        current_heading = ""
        current_level = 0
        current_content_lines = []
        current_start = base_offset

        heading_pattern = re.compile(r"^(\s*)(#{1,6}\s+|(?:\d+\.)+\s+|[A-Z][A-Z\s]{2,}:?\s*)(.+)$")

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                current_content_lines.append(line)
                continue

            # Check if line looks like a heading
            match = heading_pattern.match(line)
            is_heading = bool(match and len(line_stripped) < 200)

            if is_heading:
                # Save previous section if it has content
                if current_content_lines:
                    content = "\n".join(current_content_lines).strip()
                    if content:
                        sections.append(
                            DocumentSection(
                                heading=current_heading,
                                level=current_level,
                                content=content,
                                page_number=page_num,
                                start_char=current_start,
                                end_char=current_start + len(content),
                            )
                        )

                # Start new section
                current_heading = line_stripped
                # Determine heading level
                if line_stripped.startswith("#"):
                    current_level = len(line_stripped) - len(line_stripped.lstrip("#"))
                elif re.match(r"^\d+(\.\d+)*\s", line_stripped):
                    current_level = line_stripped.count(".") + 1
                else:
                    current_level = 1

                current_content_lines = []
                current_start = base_offset + len(page_text)  # approximate
            else:
                current_content_lines.append(line)

        # Save final section
        if current_content_lines:
            content = "\n".join(current_content_lines).strip()
            if content:
                sections.append(
                    DocumentSection(
                        heading=current_heading,
                        level=current_level,
                        content=content,
                        page_number=page_num,
                        start_char=current_start,
                        end_char=current_start + len(content),
                    )
                )

        # If no sections found, treat entire page as one section
        if not sections and page_text.strip():
            sections.append(
                DocumentSection(
                    heading="",
                    level=0,
                    content=page_text.strip(),
                    page_number=page_num,
                    start_char=base_offset,
                    end_char=base_offset + len(page_text.strip()),
                )
            )

        return sections


class MarkdownParser(DocumentParser):
    """Parse Markdown documents.

    Extracts text with heading structure preserved.
    """

    supported_extensions = {".md", ".markdown"}

    def parse(self, file_path: Path, settings: Settings) -> ParsedDocument:
        """Parse a Markdown file.

        Args:
            file_path: Path to the Markdown file.
            settings: Application settings.

        Returns:
            ParsedDocument with extracted text and sections.
        """
        if not file_path.exists():
            raise DocumentParserError(f"File not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with error handling
            with open(file_path, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            raise DocumentParserError(f"Failed to read Markdown file: {e}") from e

        sections = self._extract_sections(content)
        full_text = "\n\n".join(s.content for s in sections if s.content)

        metadata = {
            "parser": "markdown",
        }

        return ParsedDocument(
            text=full_text,
            sections=sections,
            metadata=metadata,
        )

    def _extract_sections(self, content: str) -> list[DocumentSection]:
        """Extract sections from Markdown using heading syntax."""
        sections: list[DocumentSection] = []
        lines = content.split("\n")

        current_heading = ""
        current_level = 0
        current_content_lines: list[str] = []
        current_start = 0
        char_offset = 0

        for line in lines:
            # Check for Markdown heading
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                # Save previous section
                if current_content_lines:
                    section_content = "\n".join(current_content_lines).strip()
                    if section_content:
                        sections.append(
                            DocumentSection(
                                heading=current_heading,
                                level=current_level,
                                content=section_content,
                                start_char=current_start,
                                end_char=current_start + len(section_content),
                            )
                        )

                # Start new section
                current_heading = heading_match.group(2).strip()
                current_level = len(heading_match.group(1))
                current_content_lines = []
                current_start = char_offset
            else:
                current_content_lines.append(line)

            char_offset += len(line) + 1  # +1 for newline

        # Save final section
        if current_content_lines:
            section_content = "\n".join(current_content_lines).strip()
            if section_content:
                sections.append(
                    DocumentSection(
                        heading=current_heading,
                        level=current_level,
                        content=section_content,
                        start_char=current_start,
                        end_char=current_start + len(section_content),
                    )
                )

        # If no headings found, treat entire document as one section
        if not sections and content.strip():
            sections.append(
                DocumentSection(
                    heading="",
                    level=0,
                    content=content.strip(),
                    start_char=0,
                    end_char=len(content.strip()),
                )
            )

        return sections


class CSVParser(DocumentParser):
    """Parse CSV documents.

    Converts CSV rows to text with column headers as context.
    """

    supported_extensions = {".csv"}

    def parse(self, file_path: Path, settings: Settings) -> ParsedDocument:
        """Parse a CSV file.

        Args:
            file_path: Path to the CSV file.
            settings: Application settings.

        Returns:
            ParsedDocument with CSV content converted to text.
        """
        if not file_path.exists():
            raise DocumentParserError(f"File not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                # Detect delimiter
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter

                reader = csv.DictReader(f, delimiter=delimiter)
                rows = list(reader)

                if not reader.fieldnames:
                    raise DocumentParserError("CSV has no headers")

                fieldnames = reader.fieldnames
        except Exception as e:
            raise DocumentParserError(f"Failed to parse CSV: {e}") from e

        # Convert to text representation
        sections = []
        text_parts = []

        # Header section
        header_text = " | ".join(fieldnames)
        sections.append(
            DocumentSection(
                heading="CSV Headers",
                level=1,
                content=header_text,
            )
        )
        text_parts.append(header_text)

        # Data rows
        for i, row in enumerate(rows):
            row_text = " | ".join(str(row.get(field, "")) for field in fieldnames)
            sections.append(
                DocumentSection(
                    heading=f"Row {i + 1}",
                    level=2,
                    content=row_text,
                )
            )
            text_parts.append(row_text)

        full_text = "\n".join(text_parts)

        metadata = {
            "parser": "csv",
            "row_count": len(rows),
            "column_count": len(fieldnames),
            "columns": fieldnames,
        }

        return ParsedDocument(
            text=full_text,
            sections=sections,
            metadata=metadata,
        )


def get_parser(file_path: Path, settings: Settings) -> DocumentParser:
    """Get the appropriate parser for a file.

    Args:
        file_path: Path to the file.
        settings: Application settings.

    Returns:
        DocumentParser instance.

    Raises:
        DocumentParserError: If no parser is available for the file type.
    """
    parsers = [
        PDFParser(),
        MarkdownParser(),
        CSVParser(),
    ]

    for parser in parsers:
        if parser.can_parse(file_path):
            return parser

    raise DocumentParserError(f"No parser available for file type: {file_path.suffix}")
