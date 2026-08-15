"""Unit tests for RAG components (Phase 4).

Tests use mocked HTTP calls for Ollama and ChromaDB so they don't
require external services.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.config import Settings
from src.rag.chromadb_client import ChromaDBClient
from src.rag.chunking import Chunk, chunk_sections
from src.rag.embedding_provider import (
    EmbeddingProviderError,
    OllamaNomicEmbeddingProvider,
    create_embedding_provider,
)
from src.rag.ingestion import IngestionPipeline
from src.rag.parsers import DocumentParserError, get_parser
from src.rag.text_cleaning import clean_text, count_tokens_estimate, split_into_paragraphs


class TestTextCleaning:
    """Tests for text cleaning functions."""

    def test_clean_text_basic(self) -> None:
        """Test basic text cleaning."""
        raw = "  Hello   World  \n\n\n  "
        cleaned = clean_text(raw)
        assert cleaned == "Hello World"

    def test_clean_text_html_removal(self) -> None:
        """Test HTML tag removal."""
        raw = "<p>Hello <b>World</b></p>"
        cleaned = clean_text(raw)
        assert "Hello" in cleaned
        assert "World" in cleaned
        assert "<p>" not in cleaned
        assert "<b>" not in cleaned

    def test_clean_text_page_numbers(self) -> None:
        """Test page number removal."""
        raw = "Page 1 of 10\nContent here\nPage 2"
        cleaned = clean_text(raw)
        assert "Page 1 of 10" not in cleaned or "Page 1" not in cleaned

    def test_split_into_paragraphs(self) -> None:
        """Test paragraph splitting."""
        text = "Para 1\n\nPara 2\n\n\nPara 3"
        paragraphs = split_into_paragraphs(text)
        assert len(paragraphs) == 3
        assert paragraphs[0] == "Para 1"
        assert paragraphs[1] == "Para 2"
        assert paragraphs[2] == "Para 3"

    def test_count_tokens_estimate(self) -> None:
        """Test token estimation."""
        # ~4 chars per token
        assert count_tokens_estimate("") == 0
        assert count_tokens_estimate("test") == 1
        assert count_tokens_estimate("a" * 100) == 25
        assert count_tokens_estimate("hello world") == 2


class TestChunking:
    """Tests for section-aware chunking."""

    def test_chunk_small_section(self) -> None:
        """Test chunking a section that fits in one chunk."""
        from src.rag.parsers import DocumentSection

        settings = Settings(rag_chunk_size=512, rag_chunk_overlap=64, rag_min_chunk_size=50)

        sections = [
            DocumentSection(
                heading="Test Section",
                level=1,
                content="This is a small section that fits in one chunk.",
                page_number=1,
            )
        ]

        chunks = chunk_sections(sections, settings, "test-source")
        assert len(chunks) == 1
        assert chunks[0].section_heading == "Test Section"
        assert chunks[0].chunk_index == 0

    def test_chunk_large_section(self) -> None:
        """Test chunking a section that needs multiple chunks."""
        from src.rag.parsers import DocumentSection

        settings = Settings(rag_chunk_size=50, rag_chunk_overlap=10, rag_min_chunk_size=20)

        # Create content that will need multiple chunks
        content = " ".join([f"Sentence {i}." for i in range(30)])

        sections = [
            DocumentSection(
                heading="Large Section",
                level=1,
                content=content,
                page_number=1,
            )
        ]

        chunks = chunk_sections(sections, settings, "test-source")
        assert len(chunks) > 1
        assert all(c.section_heading == "Large Section" for c in chunks)

    def test_chunk_empty_section(self) -> None:
        """Test chunking an empty section."""
        from src.rag.parsers import DocumentSection

        settings = Settings(rag_chunk_size=512, rag_chunk_overlap=64, rag_min_chunk_size=50)

        sections = [
            DocumentSection(
                heading="Empty",
                level=1,
                content="   ",
                page_number=1,
            )
        ]

        chunks = chunk_sections(sections, settings, "test-source")
        assert len(chunks) == 0


class TestEmbeddingProvider:
    """Tests for OllamaNomicEmbeddingProvider (with mocked HTTP)."""

    @pytest.fixture
    def mock_settings(self) -> Settings:
        return Settings(
            _env_file=None,
            embedding_provider="ollama",
            ollama_base_url="http://127.0.0.1:11434",
            embedding_model="nomic-embed-text",
        )

    @pytest.mark.asyncio
    async def test_embed_success(self, mock_settings: Settings) -> None:
        """Test successful embedding generation."""
        with patch("src.rag.embedding_provider.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful response
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = MagicMock(return_value={"embedding": [0.1] * 768})
            mock_client.post.return_value = mock_response

            provider = OllamaNomicEmbeddingProvider(mock_settings)
            embeddings = await provider.embed(["test text 1", "test text 2"])

            assert len(embeddings) == 2
            assert len(embeddings[0]) == 768
            assert embeddings[0][0] == 0.1
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_embed_connection_error(self, mock_settings: Settings) -> None:
        """Test handling of connection errors."""
        import httpx

        with patch("src.rag.embedding_provider.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")

            provider = OllamaNomicEmbeddingProvider(mock_settings)

            with pytest.raises(EmbeddingProviderError, match="Cannot connect to Ollama"):
                await provider.embed(["test"])

    @pytest.mark.asyncio
    async def test_embed_model_not_found(self, mock_settings: Settings) -> None:
        """Test handling of model not found (404)."""
        import httpx

        with patch("src.rag.embedding_provider.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.post.side_effect = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=mock_response
            )

            provider = OllamaNomicEmbeddingProvider(mock_settings)

            with pytest.raises(EmbeddingProviderError, match="not found in Ollama"):
                await provider.embed(["test"])

    def test_factory_creates_ollama_provider(self, mock_settings: Settings) -> None:
        """Test factory creates Ollama provider."""
        provider = create_embedding_provider(mock_settings)
        assert isinstance(provider, OllamaNomicEmbeddingProvider)
        assert provider.provider_name == "ollama"
        assert provider.model_name == "nomic-embed-text"
        assert provider.embedding_dimension == 768

    def test_factory_rejects_unknown_provider(self) -> None:
        """Test factory rejects unknown provider."""
        settings = Settings(_env_file=None, embedding_provider="unknown")

        with pytest.raises(ValueError, match="Unsupported CYBERSRS_EMBEDDING_PROVIDER"):
            create_embedding_provider(settings)


class TestParsers:
    """Tests for document parsers."""

    def test_get_parser_pdf(self) -> None:
        """Test getting PDF parser."""
        settings = Settings(_env_file=None)
        parser = get_parser(Path("test.pdf"), settings)
        assert parser.__class__.__name__ == "PDFParser"

    def test_get_parser_markdown(self) -> None:
        """Test getting Markdown parser."""
        settings = Settings(_env_file=None)
        parser = get_parser(Path("test.md"), settings)
        assert parser.__class__.__name__ == "MarkdownParser"

    def test_get_parser_csv(self) -> None:
        """Test getting CSV parser."""
        settings = Settings(_env_file=None)
        parser = get_parser(Path("test.csv"), settings)
        assert parser.__class__.__name__ == "CSVParser"

    def test_get_parser_unknown(self) -> None:
        """Test error for unknown file type."""
        settings = Settings(_env_file=None)
        with pytest.raises(DocumentParserError, match="No parser available"):
            get_parser(Path("test.xyz"), settings)

    def test_markdown_parser_headings(self, tmp_path: Path) -> None:
        """Test Markdown parser extracts headings."""
        md_content = """# Heading 1
Content 1

## Heading 2
Content 2

### Heading 3
Content 3
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        settings = Settings(_env_file=None)
        parser = get_parser(md_file, settings)
        parsed = parser.parse(md_file, settings)

        assert len(parsed.sections) >= 3
        headings = [s.heading for s in parsed.sections]
        assert "Heading 1" in headings
        assert "Heading 2" in headings
        assert "Heading 3" in headings

    def test_csv_parser(self, tmp_path: Path) -> None:
        """Test CSV parser."""
        csv_content = """col1,col2,col3
val1,val2,val3
val4,val5,val6
"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)

        settings = Settings(_env_file=None)
        parser = get_parser(csv_file, settings)
        parsed = parser.parse(csv_file, settings)

        assert "val1" in parsed.text
        assert "val4" in parsed.text
        assert parsed.metadata["row_count"] == 2
        assert parsed.metadata["column_count"] == 3


class TestChromaDBClient:
    """Tests for ChromaDB client (with mocked ChromaDB)."""

    @pytest.fixture
    def mock_chromadb(self) -> MagicMock:
        """Mock ChromaDB client and collection."""
        with patch("src.rag.chromadb_client.chromadb.PersistentClient") as mock_client_class:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.get_or_create_collection.return_value = mock_collection
            yield mock_collection

    def test_upsert_chunks(self, mock_chromadb: MagicMock) -> None:
        """Test upserting chunks."""
        settings = Settings(
            _env_file=None,
            chroma_path="./data/chroma",
            chroma_collection="test_collection",
        )

        client = ChromaDBClient(settings)
        client._collection = mock_chromadb

        chunks = [
            Chunk(
                text="chunk 1",
                token_count=10,
                section_heading="H1",
                section_level=1,
                chunk_index=0,
            ),
            Chunk(
                text="chunk 2",
                token_count=10,
                section_heading="H1",
                section_level=1,
                chunk_index=1,
            ),
        ]

        doc_meta = {
            "title": "Test Doc",
            "organization": "Test Org",
            "version": "1.0",
            "publication_date": "2024-01-01",
            "retrieval_date": "2024-01-01",
            "source_url": "http://example.com",
            "file_hash_sha256": "abc123",
            "categories": ["CAT-01"],
            "license_note": "test",
        }

        count = client.upsert_chunks("source-1", chunks, doc_meta)
        assert count == 2
        mock_chromadb.upsert.assert_called_once()

    def test_query_deduplication(self, mock_chromadb: MagicMock) -> None:
        """Test query result deduplication."""
        settings = Settings(
            _env_file=None,
            chroma_path="./data/chroma",
            chroma_collection="test_collection",
        )

        client = ChromaDBClient(settings)
        client._collection = mock_chromadb

        # Mock query results with duplicate chunk_ids
        mock_chromadb.query.return_value = {
            "ids": [["chunk_1", "chunk_2", "chunk_1"]],
            "documents": [["text 1", "text 2", "text 1 duplicate"]],
            "metadatas": [[{}, {}, {}]],
            "distances": [[0.1, 0.2, 0.15]],
        }

        results = client.query(["test query"], top_k=10, min_score=0.0)
        assert len(results) == 2  # Should deduplicate chunk_1
        assert results[0].chunk_id == "chunk_1"
        assert results[0].relevance_score == 0.9  # 1 - 0.1


class TestIngestionPipeline:
    """Tests for the ingestion pipeline (with mocked dependencies)."""

    @pytest.fixture
    def mock_pipeline(self) -> tuple[IngestionPipeline, MagicMock, MagicMock]:
        """Create pipeline with mocked ChromaDB and embedding provider."""
        settings = Settings(
            _env_file=None,
            chroma_path="./data/chroma",
            chroma_collection="test_collection",
            rag_chunk_size=512,
            rag_chunk_overlap=64,
            rag_min_chunk_size=50,
        )

        mock_chroma = MagicMock(spec=ChromaDBClient)
        mock_embedding = MagicMock()

        pipeline = IngestionPipeline(settings, mock_chroma, mock_embedding)
        return pipeline, mock_chroma, mock_embedding

    def test_compute_kb_version(self, mock_pipeline: tuple) -> None:
        """Test KB version computation."""
        pipeline, _, _ = mock_pipeline

        manifest = {
            "documents": [
                {"source_id": "doc1", "title": "Doc 1"},
                {"source_id": "doc2", "title": "Doc 2"},
            ]
        }

        version1 = pipeline._compute_kb_version(manifest)
        version2 = pipeline._compute_kb_version(manifest)
        assert version1 == version2
        assert len(version1) == 16

        # Different manifest should produce different version
        manifest2 = {"documents": [{"source_id": "doc3"}]}
        version3 = pipeline._compute_kb_version(manifest2)
        assert version3 != version1

    def test_compute_file_hash(self, mock_pipeline: tuple, tmp_path: Path) -> None:
        """Test file hash computation."""
        pipeline, _, _ = mock_pipeline

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        hash1 = pipeline._compute_file_hash(test_file)
        hash2 = pipeline._compute_file_hash(test_file)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex


class TestIngestionCLI:
    """Tests for the ingestion CLI (dry run mode)."""

    def test_dry_run(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """Test CLI dry run mode."""
        # Set caplog to capture INFO level logs
        caplog.set_level(logging.INFO)

        # Create test manifest
        manifest = {
            "documents": [
                {
                    "source_id": "test-doc",
                    "title": "Test Document",
                    "organization": "Test Org",
                    "version": "1.0",
                    "publication_date": "2024-01-01",
                    "retrieval_date": "2024-01-01",
                    "source_url": "http://example.com",
                    "local_path": "raw/test/test.txt",
                    "sha256": "abc123",
                    "size_bytes": 100,
                    "purpose": "Test",
                    "packaged": True,
                    "license_note": "test",
                }
            ]
        }

        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest))

        corpus_root = tmp_path / "knowledge"
        corpus_root.mkdir()
        doc_dir = corpus_root / "raw" / "test"
        doc_dir.mkdir(parents=True)
        (doc_dir / "test.txt").write_text("test content")

        # Run CLI in dry-run mode
        import sys

        from src.rag.ingest_cli import main

        sys.argv = [
            "ingest_cli",
            "--manifest", str(manifest_path),
            "--corpus-root", str(corpus_root),
            "--dry-run",
            "--log-level", "INFO",
        ]

        exit_code = main()
        assert exit_code == 0

        # Check log output
        log_messages = [record.message for record in caplog.records]
        combined_logs = " ".join(log_messages)
        assert "DRY RUN" in combined_logs
        assert "OK:" in combined_logs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])