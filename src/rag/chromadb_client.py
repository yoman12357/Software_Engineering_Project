"""ChromaDB client wrapper for CyberSRS RAG.

Implements local persistent ChromaDB storage with metadata support.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..core.config import Settings
from ..rag.chunking import Chunk

logger = logging.getLogger(__name__)

# Chroma 0.5 can invoke an incompatible PostHog client even when anonymized
# telemetry is disabled. The capture attempt is harmless but otherwise emits
# misleading ERROR records for every local query.
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)


@dataclass
class SearchResult:
    """Result from a vector search."""

    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float
    relevance_score: float


class ChromaDBError(Exception):
    """Raised when ChromaDB operations fail."""

    pass


class ChromaDBClient:
    """Wrapper for ChromaDB operations."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the ChromaDB client.

        Args:
            settings: Application settings.
        """
        self._settings = settings
        self._persist_path = Path(settings.chroma_path).resolve()
        self._collection_name = settings.chroma_collection

        # Ensure persist directory exists
        self._persist_path.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self._client = chromadb.PersistentClient(
            path=str(self._persist_path),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            "Initialized ChromaDB at %s, collection: %s",
            self._persist_path,
            self._collection_name,
        )

    def __enter__(self) -> ChromaDBClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # ChromaDB client doesn't need explicit close for persistent client
        pass

    def _chunk_to_metadata(
        self,
        chunk: Chunk,
        source_id: str,
        doc_metadata: dict,
    ) -> dict[str, Any]:
        """Convert a chunk to ChromaDB metadata dict."""
        return {
            "source_id": source_id,
            "document_title": doc_metadata.get("title", ""),
            "organisation": doc_metadata.get("organization", ""),
            "version": doc_metadata.get("version", ""),
            "publication_date": str(doc_metadata.get("publication_date", "")),
            "retrieval_date": str(doc_metadata.get("retrieval_date", "")),
            "source_url": doc_metadata.get("source_url", ""),
            "section_heading": chunk.section_heading,
            "section_level": chunk.section_level,
            "page_number": chunk.page_number or 0,
            "chunk_index": chunk.chunk_index,
            "file_hash_sha256": doc_metadata.get("file_hash_sha256", ""),
            "categories": ",".join(doc_metadata.get("categories", [])),
            "licence_note": doc_metadata.get("license_note", ""),
            "project_id": doc_metadata.get("project_id", ""),
            "document_scope": doc_metadata.get("document_scope", "global"),
        }

    def _generate_chunk_id(self, source_id: str, chunk_index: int) -> str:
        """Generate a deterministic chunk ID."""
        return f"{source_id}_chunk_{chunk_index}"

    def upsert_chunks(
        self,
        source_id: str,
        chunks: list[Chunk],
        doc_metadata: dict,
        embeddings: list[list[float]] | None = None,
    ) -> int:
        """Upsert chunks into the collection.

        Args:
            source_id: Source document ID.
            chunks: List of Chunk objects.
            doc_metadata: Document metadata from manifest.
            embeddings: Optional precomputed embeddings for each chunk.

        Returns:
            Number of chunks upserted.
        """
        if not chunks:
            return 0
        if embeddings is not None and len(embeddings) != len(chunks):
            raise ChromaDBError(
                f"Embedding count mismatch: {len(embeddings)} embeddings for {len(chunks)} chunks"
            )

        ids = []
        documents = []
        metadatas = []
        embedding_values = []

        for index, chunk in enumerate(chunks):
            chunk_id = self._generate_chunk_id(source_id, chunk.chunk_index)
            ids.append(chunk_id)
            documents.append(chunk.text)
            metadatas.append(self._chunk_to_metadata(chunk, source_id, doc_metadata))
            if embeddings is not None:
                embedding_values.append(embeddings[index])

        try:
            # Check for existing chunks to avoid duplicates
            existing = self._collection.get(ids=ids)
            existing_ids = set(existing.get("ids", []))

            # Filter out existing chunks
            new_ids = []
            new_documents = []
            new_metadatas = []
            new_embeddings = []
            for i, chunk_id in enumerate(ids):
                if chunk_id not in existing_ids:
                    new_ids.append(chunk_id)
                    new_documents.append(documents[i])
                    new_metadatas.append(metadatas[i])
                    if embeddings is not None:
                        new_embeddings.append(embedding_values[i])

            if new_ids:
                kwargs: dict[str, Any] = {
                    "ids": new_ids,
                    "documents": new_documents,
                    "metadatas": new_metadatas,
                }
                if embeddings is not None:
                    kwargs["embeddings"] = new_embeddings
                self._collection.upsert(**kwargs)  # type: ignore[arg-type]
                logger.info(f"Upserted {len(new_ids)} new chunks for source {source_id}")

            return len(chunks)

        except Exception as e:
            raise ChromaDBError(f"Failed to upsert chunks: {e}") from e

    def query(
        self,
        query_texts: list[str],
        query_embeddings: list[list[float]] | None = None,
        top_k: int = 10,
        min_score: float = 0.3,
        filter_metadata: dict | None = None,
    ) -> list[SearchResult]:
        """Query the collection for similar chunks.

        Args:
            query_texts: List of query texts.
            top_k: Number of results per query.
            min_score: Minimum relevance score (1 - distance).
            filter_metadata: Optional metadata filter.

        Returns:
            List of SearchResult objects, deduplicated by chunk_id.
        """
        if not query_texts:
            return []
        if query_embeddings is not None and len(query_embeddings) != len(query_texts):
            raise ChromaDBError(
                "Query embedding count mismatch: "
                f"{len(query_embeddings)} embeddings for {len(query_texts)} query texts"
            )

        try:
            # Query for each query text
            all_results = []

            for index, query_text in enumerate(query_texts):
                query_kwargs: dict[str, Any] = {
                    "n_results": top_k,
                    "where": filter_metadata,
                    "include": ["documents", "metadatas", "distances"],
                }
                if query_embeddings is None:
                    query_kwargs["query_texts"] = [query_text]
                else:
                    query_kwargs["query_embeddings"] = [query_embeddings[index]]
                results = self._collection.query(
                    **query_kwargs,
                )

                # Process results
                if results.get("ids") and results["ids"]:
                    assert results["ids"] is not None
                    assert results["documents"] is not None
                    assert results["metadatas"] is not None
                    assert results["distances"] is not None
                    ids_list = results["ids"][0]
                    docs_list = results["documents"][0]
                    metas_list = results["metadatas"][0]
                    dists_list = results["distances"][0]

                    for i in range(len(ids_list)):
                        chunk_id = ids_list[i]
                        text = docs_list[i]
                        metadata = metas_list[i]
                        distance = dists_list[i]

                        # Convert distance to relevance score (cosine similarity)
                        relevance_score = 1.0 - distance

                        if relevance_score >= min_score:
                            all_results.append(
                                SearchResult(
                                    chunk_id=chunk_id,
                                    text=text,
                                    metadata=dict(metadata),
                                    distance=distance,
                                    relevance_score=relevance_score,
                                )
                            )

            # Deduplicate by chunk_id, keeping highest relevance
            deduped: dict[str, SearchResult] = {}
            for result in all_results:
                existing = deduped.get(result.chunk_id)
                if existing is None or result.relevance_score > existing.relevance_score:
                    deduped[result.chunk_id] = result

            # Sort by relevance score descending
            sorted_results = sorted(deduped.values(), key=lambda r: r.relevance_score, reverse=True)

            return sorted_results

        except Exception as e:
            raise ChromaDBError(f"Failed to query collection: {e}") from e

    def get_collection_stats(self) -> dict:
        """Get collection statistics."""
        try:
            count = self._collection.count()
            return {
                "collection_name": self._collection_name,
                "total_chunks": count,
                "persist_path": str(self._persist_path),
            }
        except Exception as e:
            raise ChromaDBError(f"Failed to get collection stats: {e}") from e

    def delete_source(self, source_id: str) -> int:
        """Delete all chunks for a source document.

        Args:
            source_id: Source document ID.

        Returns:
            Number of chunks deleted.
        """
        try:
            # Find all chunks for this source
            results = self._collection.get(
                where={"source_id": source_id},
                include=["metadatas"],
            )

            if not results.get("ids"):
                return 0

            chunk_ids = results["ids"]
            self._collection.delete(ids=chunk_ids)
            logger.info(f"Deleted {len(chunk_ids)} chunks for source {source_id}")
            return len(chunk_ids)

        except Exception as e:
            raise ChromaDBError(f"Failed to delete source chunks: {e}") from e

    def get_chunks_for_source(self, source_id: str) -> list[dict]:
        """Get all chunks for a source document.

        Args:
            source_id: Source document ID.

        Returns:
            List of chunk metadata dictionaries.
        """
        try:
            results = self._collection.get(
                where={"source_id": source_id},
                include=["documents", "metadatas"],
            )

            chunks = []
            if results.get("ids") and results["ids"]:
                assert results["ids"] is not None
                assert results["documents"] is not None
                assert results["metadatas"] is not None
                ids_list = results["ids"]
                docs_list = results["documents"]
                metas_list = results["metadatas"]
                for i, chunk_id in enumerate(ids_list):
                    chunks.append(
                        {
                            "chunk_id": chunk_id,
                            "text": docs_list[i],
                            "metadata": metas_list[i],
                        }
                    )
            return chunks

        except Exception as e:
            raise ChromaDBError(f"Failed to get source chunks: {e}") from e

    def get_chunks_by_ids(self, chunk_ids: list[str]) -> list[dict]:
        """Get chunks by their ChromaDB document IDs.

        Args:
            chunk_ids: List of chunk IDs (``{source_id}_chunk_{index}``).

        Returns:
            List of chunk dictionaries with ``chunk_id``, ``text`` and
            ``metadata`` keys, in the same order as requested. Missing IDs are
            skipped.
        """
        if not chunk_ids:
            return []

        try:
            results = self._collection.get(
                ids=chunk_ids,
                include=["documents", "metadatas"],
            )

            chunks: list[dict] = []
            ids_list = results.get("ids") or []
            docs_list = results.get("documents") or []
            metas_list = results.get("metadatas") or []

            for i, chunk_id in enumerate(ids_list):
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "text": docs_list[i] if i < len(docs_list) else "",
                        "metadata": metas_list[i] if i < len(metas_list) else {},
                    }
                )
            return chunks

        except Exception as e:
            raise ChromaDBError(f"Failed to get chunks by ids: {e}") from e


def create_chromadb_client(settings: Settings) -> ChromaDBClient:
    """Factory function to create ChromaDB client.

    Args:
        settings: Application settings.

    Returns:
        ChromaDBClient instance.
    """
    return ChromaDBClient(settings)
