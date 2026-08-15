"""RAG (Retrieval-Augmented Generation) package for CyberSRS."""

from .chromadb_client import ChromaDBClient, SearchResult, create_chromadb_client
from .chunking import Chunk, chunk_sections
from .embedding_provider import (
    EmbeddingProvider,
    EmbeddingProviderError,
    OllamaNomicEmbeddingProvider,
    create_embedding_provider,
)
from .ingestion import DocumentIngestionResult, IngestionPipeline, IngestionStats, run_ingestion
from .parsers import (
    DocumentParser,
    DocumentParserError,
    DocumentSection,
    ParsedDocument,
    get_parser,
)
from .retrieval import (
    CitationValidator,
    RetrievalContext,
    RetrievedChunk,
    Retriever,
    create_retriever,
)

__all__ = [
    # ChromaDB
    "ChromaDBClient",
    "SearchResult",
    "create_chromadb_client",
    # Chunking
    "Chunk",
    "chunk_sections",
    # Embedding
    "EmbeddingProvider",
    "EmbeddingProviderError",
    "OllamaNomicEmbeddingProvider",
    "create_embedding_provider",
    # Ingestion
    "IngestionPipeline",
    "IngestionStats",
    "DocumentIngestionResult",
    "run_ingestion",
    # Parsers
    "DocumentParser",
    "DocumentParserError",
    "ParsedDocument",
    "DocumentSection",
    "get_parser",
    # Retrieval
    "Retriever",
    "RetrievalContext",
    "RetrievedChunk",
    "CitationValidator",
    "create_retriever",
]
