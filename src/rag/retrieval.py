"""RAG retrieval module for CyberSRS.

Implements retrieval-augmented generation for grounded SRS generation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..core.config import Settings
from ..rag.chromadb_client import ChromaDBClient, create_chromadb_client
from ..rag.embedding_provider import EmbeddingProvider, create_embedding_provider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrievedChunk:
    """A retrieved chunk with metadata for citation."""

    chunk_id: str
    text: str
    metadata: dict[str, Any]
    relevance_score: float
    distance: float


@dataclass(frozen=True)
class RetrievalContext:
    """Assembled retrieval context for grounded generation."""

    chunks: list[RetrievedChunk]
    query_texts: list[str]
    total_chunks: int
    kb_version: str
    retrieval_time_ms: int


class RetrievalError(Exception):
    """Raised when retrieval fails."""

    pass


class Retriever:
    """Handles retrieval of relevant chunks for grounded SRS generation."""

    def __init__(
        self,
        settings: Settings,
        chroma_client: ChromaDBClient | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        """Initialize the retriever.

        Args:
            settings: Application settings.
            chroma_client: Optional pre-configured ChromaDB client.
            embedding_provider: Optional pre-configured embedding provider.
        """
        self._settings = settings
        self._chroma = chroma_client or create_chromadb_client(settings)
        self._embedding_provider = embedding_provider or create_embedding_provider(settings)

    def retrieve(
        self,
        project_context: dict[str, Any],
        kb_version: str,
        top_k: int | None = None,
        min_score: float | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> RetrievalContext:
        """Retrieve relevant chunks for the given project context.

        Args:
            project_context: Dictionary containing project context (categories, goals, etc.)
            kb_version: Knowledge base version identifier.
            top_k: Number of results per query (defaults to settings.rag_top_k).
            min_score: Minimum relevance score threshold (defaults to settings.rag_min_score).
            filter_metadata: Optional mandatory Chroma metadata filter.

        Returns:
            RetrievalContext with retrieved chunks and metadata.
        """
        import time

        start_time = time.perf_counter()

        top_k = top_k or self._settings.rag_top_k
        min_score = min_score or self._settings.rag_min_score

        # Build query texts from project context
        query_texts = self._build_queries(project_context)

        logger.info(
            "Retrieving chunks for project",
            extra={
                "categories": project_context.get("inferred_categories", []),
                "query_count": len(query_texts),
                "top_k": top_k,
                "min_score": min_score,
            },
        )

        # Embed queries with the configured local embedding provider before
        # querying Chroma, so RAG does not fall back to Chroma's default model.
        query_embeddings = self._embedding_provider.embed_sync(query_texts)

        # Retrieve chunks
        search_results = self._chroma.query(
            query_texts=query_texts,
            query_embeddings=query_embeddings,
            top_k=top_k,
            min_score=min_score,
            filter_metadata=filter_metadata,
        )

        # Convert to retrieved chunks
        retrieved_chunks = [
            RetrievedChunk(
                chunk_id=r.chunk_id,
                text=r.text,
                metadata=r.metadata,
                relevance_score=r.relevance_score,
                distance=r.distance,
            )
            for r in search_results
        ]

        retrieval_time_ms = int((time.perf_counter() - start_time) * 1000)

        logger.info(
            "Retrieval completed",
            extra={
                "total_chunks": len(retrieved_chunks),
                "retrieval_time_ms": retrieval_time_ms,
                "kb_version": kb_version,
            },
        )

        return RetrievalContext(
            chunks=retrieved_chunks,
            query_texts=query_texts,
            total_chunks=len(retrieved_chunks),
            kb_version=kb_version,
            retrieval_time_ms=retrieval_time_ms,
        )

    def retrieve_for_question(
        self,
        question: str,
        kb_version: str,
        top_k: int | None = None,
        min_score: float | None = None,
    ) -> RetrievalContext:
        """Retrieve chunks for one conversational question without SRS-section queries."""
        import time

        start_time = time.perf_counter()
        result_limit = self._settings.rag_top_k if top_k is None else top_k
        score_threshold = self._settings.rag_min_score if min_score is None else min_score
        query_embeddings = self._embedding_provider.embed_sync([question])
        results = self._chroma.query(
            query_texts=[question],
            query_embeddings=query_embeddings,
            top_k=result_limit,
            min_score=score_threshold,
        )
        chunks = [
            RetrievedChunk(
                chunk_id=result.chunk_id,
                text=result.text,
                metadata=result.metadata,
                relevance_score=result.relevance_score,
                distance=result.distance,
            )
            for result in results
        ]
        return RetrievalContext(
            chunks=chunks,
            query_texts=[question],
            total_chunks=len(chunks),
            kb_version=kb_version,
            retrieval_time_ms=int((time.perf_counter() - start_time) * 1000),
        )

    def _build_queries(self, project_context: dict[str, Any]) -> list[str]:
        """Build retrieval queries from project context.

        Args:
            project_context: Dictionary with project context.

        Returns:
            List of query strings for retrieval.
        """
        queries = []

        # Primary query: concatenation of inferred categories + goals + key constraints
        categories = project_context.get("inferred_categories", [])
        goals = project_context.get("goals", [])
        constraints = project_context.get("constraints", [])

        primary_parts = []
        if categories:
            primary_parts.append(f"Cybersecurity categories: {', '.join(categories)}")
        if goals:
            primary_parts.append(f"Goals: {'; '.join(goals[:3])}")  # Limit to 3 goals
        if constraints:
            primary_parts.append(f"Constraints: {'; '.join(constraints[:3])}")

        primary_query = " ".join(primary_parts)
        if primary_query:
            queries.append(primary_query)

        # Secondary queries per SRS section being generated
        section_queries = [
            "functional requirements cybersecurity system",
            "non-functional requirements availability performance security",
            "security requirements authentication authorization encryption",
            "data requirements retention integrity privacy",
            "network requirements segmentation firewall",
            "architecture components cybersecurity system",
            "threat model STRIDE mitigations",
        ]

        # Add section-specific queries based on inferred categories
        categories_set = set(categories)
        if "CAT-02" in categories_set or "CAT-03" in categories_set:  # Firewall/Monitoring
            queries.append("firewall network monitoring requirements")
        if "CAT-04" in categories_set:  # IAM
            queries.append("identity access management authentication authorization")
        if "CAT-05" in categories_set:  # Secure web/API
            queries.append("API security OWASP Top 10 requirements")
        if "CAT-06" in categories_set:  # VPN
            queries.append("VPN remote access zero trust requirements")
        if "CAT-07" in categories_set:  # Logging
            queries.append("security logging SIEM alerting requirements")
        if "CAT-08" in categories_set:  # Zero trust
            queries.append("zero trust network segmentation requirements")

        # Add general section queries
        queries.extend(section_queries)

        # Deduplicate while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                unique_queries.append(q)

        # Limit to reasonable number of queries
        return unique_queries[:10]

    def assemble_context(self, context: RetrievalContext) -> str:
        """Assemble retrieved chunks into a context block for the LLM prompt.

        Args:
            context: RetrievalContext with retrieved chunks.

        Returns:
            Formatted context string for LLM prompt.
        """
        if not context.chunks:
            return (
                "--- NO RETRIEVED CYBERSECURITY KNOWLEDGE ---\n\n"
                "No relevant knowledge found in the knowledge base."
            )

        lines = [
            "--- RETRIEVED CYBERSECURITY KNOWLEDGE ---",
            "",
        ]

        for i, chunk in enumerate(context.chunks):
            meta = chunk.metadata
            source_info = []
            if meta.get("document_title"):
                source_info.append(meta["document_title"])
            if meta.get("section_heading"):
                source_info.append(f"Section: {meta['section_heading']}")
            if meta.get("organisation"):
                source_info.append(meta["organisation"])
            if meta.get("page_number"):
                source_info.append(f"Page: {meta['page_number']}")

            source_str = " | ".join(source_info) if source_info else "Unknown source"

            lines.append(f"[Source {i + 1}: {source_str}] (relevance: {chunk.relevance_score:.3f})")
            lines.append(chunk.text)
            lines.append("")

        lines.append("--- END RETRIEVED KNOWLEDGE ---")
        return "\n".join(lines)


def create_retriever(
    settings: Settings,
    chroma_client: ChromaDBClient | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> Retriever:
    """Factory function to create a Retriever instance.

    Args:
        settings: Application settings.
        chroma_client: Optional pre-configured ChromaDB client.
        embedding_provider: Optional pre-configured embedding provider.

    Returns:
        A configured Retriever instance.
    """
    return Retriever(settings, chroma_client, embedding_provider)


# --- Citation Validation ---


class CitationValidator:
    """Validates that generated citations reference actual retrieved chunks."""

    def __init__(self, retrieval_context: RetrievalContext) -> None:
        """Initialize with the retrieval context used for generation.

        Args:
            retrieval_context: The RetrievalContext used during generation.
        """
        self._retrieved_chunk_ids = {chunk.chunk_id for chunk in retrieval_context.chunks}
        self._chunk_metadata = {
            chunk.chunk_id: chunk.metadata for chunk in retrieval_context.chunks
        }

    def validate_citations(self, citations: list[dict[str, Any]]) -> tuple[list[dict], list[str]]:
        """Validate a list of citations against retrieved chunks.

        Args:
            citations: List of citation dictionaries from generated output.

        Returns:
            Tuple of (validated_citations, warnings).
        """
        validated = []
        warnings = []

        for citation in citations:
            source_id = citation.get("source_id")
            if not source_id:
                warnings.append(f"Citation missing source_id: {citation}")
                continue

            if source_id not in self._retrieved_chunk_ids:
                warnings.append(
                    f"Unsupported citation: source_id '{source_id}' not found in retrieved chunks. "
                    f"Available: {sorted(self._retrieved_chunk_ids)}"
                )
                # Mark as unsupported but keep for visibility
                validated.append({**citation, "supported": False})
            else:
                # Valid citation - add metadata from retrieved chunk
                meta = self._chunk_metadata.get(source_id, {})
                validated.append(
                    {
                        **citation,
                        "supported": True,
                        "document_title": citation.get("document_title")
                        or meta.get("document_title"),
                        "section_heading": citation.get("section_heading")
                        or meta.get("section_heading"),
                        "relevance_score": citation.get("relevance_score")
                        or meta.get("relevance_score"),
                    }
                )

        return validated, warnings
