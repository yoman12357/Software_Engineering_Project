"""RAG ingestion pipeline for CyberSRS.

Orchestrates the full offline ingestion process:
1. Load manifest
2. Parse documents
3. Clean and normalize text
4. Section-aware chunking
5. Generate embeddings
6. Store in ChromaDB
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core.config import Settings
from ..rag.chromadb_client import ChromaDBClient, create_chromadb_client
from ..rag.chunking import chunk_sections
from ..rag.embedding_provider import create_embedding_provider
from ..rag.parsers import get_parser
from ..rag.text_cleaning import clean_text, normalize_whitespace

logger = logging.getLogger(__name__)


@dataclass
class IngestionStats:
    """Statistics from an ingestion run."""

    documents_processed: int = 0
    documents_failed: int = 0
    total_chunks: int = 0
    total_embeddings: int = 0
    total_time_seconds: float = 0.0
    kb_version: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass
class DocumentIngestionResult:
    """Result of ingesting a single document."""

    source_id: str
    success: bool
    chunks_created: int = 0
    embeddings_created: int = 0
    error: str | None = None
    file_hash: str = ""


class IngestionPipeline:
    """Orchestrates the RAG ingestion process."""

    def __init__(
        self,
        settings: Settings,
        chroma_client: ChromaDBClient | None = None,
        embedding_provider: Any | None = None,
    ) -> None:
        """Initialize the ingestion pipeline.

        Args:
            settings: Application settings.
            chroma_client: Optional pre-configured ChromaDB client.
            embedding_provider: Optional pre-configured embedding provider.
        """
        self._settings = settings
        self._chroma = chroma_client or create_chromadb_client(settings)
        self._embedding_provider = embedding_provider or create_embedding_provider(settings)

    def ingest_corpus(
        self,
        manifest_path: Path,
        corpus_root: Path,
        force_reingest: bool = False,
    ) -> IngestionStats:
        """Ingest all documents from the corpus manifest.

        Args:
            manifest_path: Path to manifest.json.
            corpus_root: Root directory of the corpus (knowledge/).
            force_reingest: If True, re-ingest already ingested documents.

        Returns:
            IngestionStats with run statistics.
        """
        start_time = time.time()

        # Load manifest
        with open(manifest_path) as f:
            manifest = json.load(f)

        # Compute KB version from manifest
        kb_version = self._compute_kb_version(manifest)

        stats = IngestionStats(kb_version=kb_version)

        logger.info(
            "Starting ingestion of %s documents (KB version: %s)",
            len(manifest.get("documents", [])),
            kb_version,
        )

        for doc_info in manifest.get("documents", []):
            if not doc_info.get("packaged", False):
                logger.info(f"Skipping non-packaged document: {doc_info['source_id']}")
                continue

            try:
                result = self._ingest_document(
                    doc_info=doc_info,
                    corpus_root=corpus_root,
                    kb_version=kb_version,
                    force_reingest=force_reingest,
                )
                if result.success:
                    stats.documents_processed += 1
                    stats.total_chunks += result.chunks_created
                    stats.total_embeddings += result.embeddings_created
                else:
                    stats.documents_failed += 1
                    stats.errors.append(f"{result.source_id}: {result.error}")

            except Exception as e:
                stats.documents_failed += 1
                error_msg = f"{doc_info.get('source_id', 'unknown')}: {e}"
                stats.errors.append(error_msg)
                logger.exception(f"Failed to ingest {doc_info.get('source_id')}: {e}")

        stats.total_time_seconds = time.time() - start_time

        logger.info(
            f"Ingestion complete: {stats.documents_processed} processed, "
            f"{stats.documents_failed} failed, {stats.total_chunks} chunks, "
            f"{stats.total_embeddings} embeddings in {stats.total_time_seconds:.1f}s"
        )

        return stats

    def _ingest_document(
        self,
        doc_info: dict,
        corpus_root: Path,
        kb_version: str,
        force_reingest: bool,
    ) -> DocumentIngestionResult:
        """Ingest a single document.

        Args:
            doc_info: Document info from manifest.
            corpus_root: Corpus root directory.
            kb_version: Knowledge base version.
            force_reingest: Whether to force re-ingestion.

        Returns:
            DocumentIngestionResult.
        """
        source_id = doc_info["source_id"]
        local_path = corpus_root / doc_info["local_path"]

        logger.info(f"Ingesting {source_id} ({local_path})")

        # Verify file hash
        file_hash = self._compute_file_hash(local_path)
        expected_hash = doc_info.get("sha256", "").lower()

        if file_hash != expected_hash:
            error = f"Hash mismatch: expected {expected_hash}, got {file_hash}"
            logger.error(f"Hash verification failed for {source_id}: {error}")
            return DocumentIngestionResult(
                source_id=source_id,
                success=False,
                error=error,
                file_hash=file_hash,
            )

        # Parse document
        parser = get_parser(local_path, self._settings)
        parsed = parser.parse(local_path, self._settings)

        # Clean text
        for section in parsed.sections:
            section.content = normalize_whitespace(clean_text(section.content))

        # Chunk sections
        chunks = chunk_sections(parsed.sections, self._settings, source_id)

        if not chunks:
            logger.warning(f"No chunks generated for {source_id}")
            return DocumentIngestionResult(
                source_id=source_id,
                success=True,
                chunks_created=0,
                embeddings_created=0,
                file_hash=file_hash,
            )

        # Generate embeddings
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = self._embedding_provider.embed_sync(chunk_texts)

        if len(embeddings) != len(chunks):
            raise ValueError(f"Embedding count mismatch: {len(embeddings)} vs {len(chunks)}")

        # Prepare document metadata for ChromaDB
        doc_metadata = {
            "title": doc_info.get("title", ""),
            "organization": doc_info.get("organization", ""),
            "version": doc_info.get("version", ""),
            "publication_date": doc_info.get("publication_date", ""),
            "retrieval_date": doc_info.get("retrieval_date", ""),
            "source_url": doc_info.get("source_url", ""),
            "file_hash_sha256": file_hash,
            "categories": doc_info.get("categories", []),
            "license_note": doc_info.get("license_note", ""),
        }

        # Store in ChromaDB
        upserted = self._chroma.upsert_chunks(source_id, chunks, doc_metadata, embeddings)

        if upserted != len(chunks):
            logger.warning(f"Expected to upsert {len(chunks)} chunks, but {upserted} were stored")

        return DocumentIngestionResult(
            source_id=source_id,
            success=True,
            chunks_created=len(chunks),
            embeddings_created=len(embeddings),
            file_hash=file_hash,
        )

    def _compute_kb_version(self, manifest: dict) -> str:
        """Compute knowledge base version from manifest content."""
        doc_json = json.dumps(manifest.get("documents", []), sort_keys=True).encode()
        return hashlib.sha256(doc_json).hexdigest()[:16]

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()


def run_ingestion(
    manifest_path: str | Path,
    corpus_root: str | Path,
    settings: Settings | None = None,
    force: bool = False,
) -> IngestionStats:
    """Run the ingestion pipeline as a standalone function.

    Args:
        manifest_path: Path to manifest.json.
        corpus_root: Root directory of corpus.
        settings: Optional settings (uses defaults if not provided).
        force: Force re-ingestion of existing documents.

    Returns:
        IngestionStats.
    """
    settings = settings or Settings()
    chroma = create_chromadb_client(settings)
    embedding_provider = create_embedding_provider(settings)

    pipeline = IngestionPipeline(settings, chroma, embedding_provider)

    return pipeline.ingest_corpus(
        manifest_path=Path(manifest_path),
        corpus_root=Path(corpus_root),
        force_reingest=force,
    )
