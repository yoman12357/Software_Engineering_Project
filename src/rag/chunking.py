"""Section-aware chunking for RAG ingestion.

Implements chunking that respects document structure:
1. Primary boundary: Section headings
2. Secondary boundary: Paragraph breaks
3. Fallback: Token-count-based splitting
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..core.config import Settings
from ..rag.parsers import DocumentSection
from ..rag.text_cleaning import count_tokens_estimate, split_into_paragraphs


@dataclass
class Chunk:
    """A text chunk with metadata."""

    text: str
    token_count: int
    section_heading: str
    section_level: int
    page_number: int | None = None
    chunk_index: int = 0


def chunk_sections(
    sections: list[DocumentSection],
    settings: Settings,
    source_id: str,
) -> list[Chunk]:
    """Chunk document sections respecting structure.

    Args:
        sections: List of DocumentSection objects from parser.
        settings: Application settings with chunk size/overlap config.
        source_id: Source document ID for metadata.

    Returns:
        List of Chunk objects.
    """
    max_chunk_size = settings.rag_chunk_size
    chunk_overlap = settings.rag_chunk_overlap
    min_chunk_size = settings.rag_min_chunk_size

    chunks = []
    chunk_index = 0

    for section in sections:
        section_chunks = _chunk_section(
            section=section,
            max_chunk_size=max_chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_size=min_chunk_size,
            chunk_index=chunk_index,
        )
        chunks.extend(section_chunks)
        chunk_index += len(section_chunks)

    return chunks


def _chunk_section(
    section: DocumentSection,
    max_chunk_size: int,
    chunk_overlap: int,
    min_chunk_size: int,
    chunk_index: int,
) -> list[Chunk]:
    """Chunk a single section.

    Args:
        section: DocumentSection to chunk.
        max_chunk_size: Maximum tokens per chunk.
        chunk_overlap: Overlap tokens between chunks.
        min_chunk_size: Minimum chunk size (smaller chunks merged).
        chunk_index: Starting chunk index.

    Returns:
        List of Chunk objects for this section.
    """
    if not section.content.strip():
        return []

    # First, split into paragraphs
    paragraphs = split_into_paragraphs(section.content)

    if not paragraphs:
        return []

    # Check if entire section fits in one chunk
    full_text = section.content
    full_tokens = count_tokens_estimate(full_text)

    if full_tokens <= max_chunk_size:
        return [
            Chunk(
                text=full_text,
                token_count=full_tokens,
                section_heading=section.heading,
                section_level=section.level,
                page_number=section.page_number,
                chunk_index=chunk_index,
            )
        ]

    # Section too large, chunk by paragraphs with overlap
    chunks: list[Chunk] = []
    current_chunk_paragraphs: list[str] = []
    current_tokens = 0
    local_index = 0

    for para in paragraphs:
        para_tokens = count_tokens_estimate(para)

        # If single paragraph exceeds max size, split it
        if para_tokens > max_chunk_size:
            # Flush current chunk first
            if current_chunk_paragraphs:
                chunk_text = "\n\n".join(current_chunk_paragraphs)
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        token_count=current_tokens,
                        section_heading=section.heading,
                        section_level=section.level,
                        page_number=section.page_number,
                        chunk_index=chunk_index + local_index,
                    )
                )
                local_index += 1
                current_chunk_paragraphs = []
                current_tokens = 0

            # Split large paragraph into sentences
            sentence_chunks = _split_large_paragraph(
                para,
                max_chunk_size,
                chunk_overlap,
                min_chunk_size,
                section,
                chunk_index + local_index,
            )
            chunks.extend(sentence_chunks)
            local_index += len(sentence_chunks)
            continue

        # Check if adding this paragraph exceeds max size
        if current_tokens + para_tokens > max_chunk_size and current_chunk_paragraphs:
            # Flush current chunk
            chunk_text = "\n\n".join(current_chunk_paragraphs)
            chunks.append(
                Chunk(
                    text=chunk_text,
                    token_count=current_tokens,
                    section_heading=section.heading,
                    section_level=section.level,
                    page_number=section.page_number,
                    chunk_index=chunk_index + local_index,
                )
            )
            local_index += 1

            # Start new chunk with overlap
            overlap_paragraphs = _get_overlap_paragraphs(current_chunk_paragraphs, chunk_overlap)
            current_chunk_paragraphs = overlap_paragraphs + [para]
            current_tokens = sum(count_tokens_estimate(p) for p in current_chunk_paragraphs)
        else:
            current_chunk_paragraphs.append(para)
            current_tokens += para_tokens

    # Flush remaining
    if current_chunk_paragraphs:
        chunk_text = "\n\n".join(current_chunk_paragraphs)
        if count_tokens_estimate(chunk_text) >= min_chunk_size:
            chunks.append(
                Chunk(
                    text=chunk_text,
                    token_count=current_tokens,
                    section_heading=section.heading,
                    section_level=section.level,
                    page_number=section.page_number,
                    chunk_index=chunk_index + local_index,
                )
            )
        elif chunks:
            # Merge with previous chunk if too small
            chunks[-1].text += "\n\n" + chunk_text
            chunks[-1].token_count += current_tokens

    # Update chunk indices
    for i, chunk in enumerate(chunks):
        chunk.chunk_index = chunk_index + i

    return chunks


def _split_large_paragraph(
    paragraph: str,
    max_chunk_size: int,
    chunk_overlap: int,
    min_chunk_size: int,
    section: DocumentSection,
    start_index: int,
) -> list[Chunk]:
    """Split a paragraph that exceeds max chunk size.

    Splits by sentences with overlap.

    Args:
        paragraph: The paragraph text.
        max_chunk_size: Maximum tokens per chunk.
        chunk_overlap: Overlap tokens.
        min_chunk_size: Minimum chunk size.
        section: Source section for metadata.
        start_index: Starting chunk index.

    Returns:
        List of Chunk objects.
    """
    # Split by sentences
    sentences = re_split_sentences(paragraph)

    if not sentences:
        return []

    chunks: list[Chunk] = []
    current_sentences: list[str] = []
    current_tokens = 0
    local_index = 0

    for sentence in sentences:
        sent_tokens = count_tokens_estimate(sentence)

        if current_tokens + sent_tokens > max_chunk_size and current_sentences:
            chunk_text = " ".join(current_sentences)
            if count_tokens_estimate(chunk_text) >= min_chunk_size:
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        token_count=current_tokens,
                        section_heading=section.heading,
                        section_level=section.level,
                        page_number=section.page_number,
                        chunk_index=local_index,
                    )
                )
                local_index += 1

            # Overlap: keep last few sentences
            overlap_tokens = 0
            overlap_sentences: list[str] = []
            for s in reversed(current_sentences):
                s_tokens = count_tokens_estimate(s)
                if overlap_tokens + s_tokens <= chunk_overlap:
                    overlap_sentences.insert(0, s)
                    overlap_tokens += s_tokens
                else:
                    break
            current_sentences = overlap_sentences + [sentence]
            current_tokens = overlap_tokens + sent_tokens
        else:
            current_sentences.append(sentence)
            current_tokens += sent_tokens

    # Flush remaining
    if current_sentences:
        chunk_text = " ".join(current_sentences)
        if count_tokens_estimate(chunk_text) >= min_chunk_size:
            chunks.append(
                Chunk(
                    text=chunk_text,
                    token_count=current_tokens,
                    section_heading=section.heading,
                    section_level=section.level,
                    page_number=section.page_number,
                    chunk_index=start_index + local_index,
                )
            )

    # Update global indices
    for i, chunk in enumerate(chunks):
        chunk.chunk_index = start_index + i

    return chunks


def _get_overlap_paragraphs(paragraphs: list[str], overlap_tokens: int) -> list[str]:
    """Get paragraphs from the end that fit within overlap token budget.

    Args:
        paragraphs: List of paragraphs.
        overlap_tokens: Token budget for overlap.

    Returns:
        List of paragraphs for overlap.
    """
    if not paragraphs:
        return []

    overlap: list[str] = []
    tokens = 0

    for para in reversed(paragraphs):
        para_tokens = count_tokens_estimate(para)
        if tokens + para_tokens <= overlap_tokens:
            overlap.insert(0, para)
            tokens += para_tokens
        else:
            break

    return overlap


def re_split_sentences(text: str) -> list[str]:
    """Split text into sentences.

    Uses regex to handle common sentence boundaries.

    Args:
        text: Input text.

    Returns:
        List of sentences.
    """
    if not text:
        return []

    # Split on sentence boundaries (., !, ?) followed by space and capital letter
    # This is a simple heuristic; for production, consider nltk or spacy
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)

    # Clean up
    cleaned = [s.strip() for s in sentences if s.strip()]

    return cleaned
