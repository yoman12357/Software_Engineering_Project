"""Application configuration loaded from environment variables or a .env file."""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .model_constants import DEFAULT_BASE_MODEL_NAME, DEFAULT_FINETUNED_MODEL_NAME


class Settings(BaseSettings):
    """CyberSRS application settings.

    Every value is read from an environment variable prefixed with ``CYBERSRS_``
    (for example ``CYBERSRS_ENV``) or from a ``.env`` file. No secrets are
    hard-coded here; see `.env.example` for the supported variables.
    """

    model_config = SettingsConfigDict(
        env_prefix="CYBERSRS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/cybersrs.db"
    backend_port: int = 8000
    frontend_port: int = 5173
    max_request_body_bytes: int = 1_048_576  # SEC-011: 1 MB default
    max_projects: int = 100  # SEC-041: limit total stored projects
    upload_dir: str = "./data/uploads"
    max_upload_bytes: int = 10_485_760
    max_project_documents: int = 5
    max_project_document_context_chars: int = 12_000

    # --- Model variant selection (Phase 8: base vs fine-tuned) ---
    # "base"  = Qwen3-4B-Instruct-2507 (original)
    # "finetuned" = CyberSRS fine-tuned adapter (cybersrs-qwen3-4b-ft)
    # Default is "base" to preserve existing behaviour.
    model_variant: str = Field(
        default="base",
        validation_alias=AliasChoices("model_variant", "CYBERSRS_MODEL_VARIANT"),
    )

    # --- LLM provider selection (Phase 1B: mock; Phase 2: ollama) ---
    # Phase 1B must remain deterministic and mocked. The locally installed
    # Qwen / nomic-embed-text models are reserved for Phase 2 and are never
    # called while ``llm_provider`` is "mock".
    llm_provider: str = "mock"

    # --- Model registry ---
    # Base model (original Qwen3-4B-Instruct-2507).
    base_model_name: str = DEFAULT_BASE_MODEL_NAME
    # Fine-tuned model (CyberSRS QLoRA adapter).
    finetuned_model_name: str = DEFAULT_FINETUNED_MODEL_NAME

    # --- LLM / embedding models (used from Phase 2/4 onward) ---
    # Main LLM for inference (AGENTS.md: Qwen/Qwen3-4B-Instruct-2507).
    # Kept for backward compatibility; resolved from model_variant at runtime.
    model_name: str = DEFAULT_BASE_MODEL_NAME
    # Embedding model — local-only; never Qwen, DeepSeek, or any external API.
    embedding_model: str = "nomic-embed-text"
    # Optional override for the Ollama model store (OLLAMA_MODELS equivalent).
    ollama_models_dir: str = ""
    # Ollama API base URL (local-first; must bind to localhost).
    ollama_base_url: str = "http://127.0.0.1:11434"
    # Maximum retry attempts for LLM calls (SEC-039).
    llm_max_retries: int = Field(
        default=1,
        validation_alias=AliasChoices(
            "llm_max_retries",
            "CYBERSRS_LLM_MAX_RETRIES",
            "LLM_MAX_RETRIES",
        ),
    )
    # Legacy timeout alias for LLM calls (SEC-039).
    llm_timeout_seconds: int = Field(
        default=120,
        validation_alias=AliasChoices(
            "llm_timeout_seconds",
            "CYBERSRS_LLM_TIMEOUT_SECONDS",
            "LLM_TIMEOUT_SECONDS",
        ),
    )
    # Ollama-specific read/generation timeout in seconds (local Qwen defaults).
    ollama_timeout_seconds: int = Field(
        default=300,
        validation_alias=AliasChoices(
            "ollama_timeout_seconds",
            "CYBERSRS_OLLAMA_TIMEOUT_SECONDS",
            "OLLAMA_TIMEOUT_SECONDS",
        ),
    )
    # Keep the 4B model within its responsive 8K operating range locally.
    ollama_num_ctx: int = Field(
        default=8192,
        validation_alias=AliasChoices(
            "ollama_num_ctx",
            "CYBERSRS_OLLAMA_NUM_CTX",
            "OLLAMA_NUM_CTX",
        ),
    )

    # --- RAG Configuration (Phase 4) ---
    # Embedding provider (currently only ollama is supported).
    embedding_provider: str = "ollama"
    # ChromaDB persistence directory.
    chroma_path: str = Field(
        default="./data/chroma",
        validation_alias=AliasChoices(
            "chroma_path",
            "CYBERSRS_CHROMA_PATH",
            "CYBERSRS_CHROMA_PERSIST_DIR",
            "CHROMA_PERSIST_DIR",
        ),
    )
    # ChromaDB collection name.
    chroma_collection: str = Field(
        default="cybersrs_knowledge",
        validation_alias=AliasChoices(
            "chroma_collection",
            "CYBERSRS_CHROMA_COLLECTION",
            "CHROMA_COLLECTION",
        ),
    )
    # Enable retrieval-augmented generation for SRS generation.
    rag_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("rag_enabled", "CYBERSRS_RAG_ENABLED", "RAG_ENABLED"),
    )
    project_chroma_collection: str = "cybersrs_project_documents"
    # Stable identifier for the currently indexed knowledge-base snapshot.
    # ``unknown`` is explicit for deployments that predate provenance tracking.
    knowledge_base_version: str = Field(
        default="unknown",
        validation_alias=AliasChoices(
            "knowledge_base_version",
            "CYBERSRS_KNOWLEDGE_BASE_VERSION",
            "KNOWLEDGE_BASE_VERSION",
        ),
    )
    # A compact complete SRS exceeds 4K tokens, while substantially larger
    # budgets make the local 4B model too slow on typical development hardware.
    ollama_num_predict: int = Field(
        default=5200,
        validation_alias=AliasChoices(
            "ollama_num_predict",
            "CYBERSRS_OLLAMA_NUM_PREDICT",
            "OLLAMA_NUM_PREDICT",
        ),
    )
    ollama_repeat_penalty: float = Field(
        default=1.1,
        validation_alias=AliasChoices(
            "ollama_repeat_penalty",
            "CYBERSRS_OLLAMA_REPEAT_PENALTY",
            "OLLAMA_REPEAT_PENALTY",
        ),
    )
    ollama_repeat_last_n: int = Field(
        default=256,
        validation_alias=AliasChoices(
            "ollama_repeat_last_n",
            "CYBERSRS_OLLAMA_REPEAT_LAST_N",
            "OLLAMA_REPEAT_LAST_N",
        ),
    )
    ollama_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        validation_alias=AliasChoices(
            "ollama_temperature",
            "CYBERSRS_OLLAMA_TEMPERATURE",
        ),
    )

    ollama_top_p: float = Field(
        default=0.9,
        gt=0.0,
        le=1.0,
        validation_alias=AliasChoices(
            "ollama_top_p",
            "CYBERSRS_OLLAMA_TOP_P",
            "OLLAMA_TOP_P",
        ),
    )
    # Number of chunks to retrieve per query.
    rag_top_k: int = 10
    # Minimum relevance score threshold (0.0–1.0).
    rag_min_score: float = 0.3
    # Maximum retrieved context characters inserted into a single LLM prompt.
    rag_max_context_chars: int = 6_000
    # Maximum characters kept from one retrieved chunk in an LLM prompt.
    rag_max_chunk_chars: int = 1_000
    # Maximum chunk size in tokens (experimental default).
    rag_chunk_size: int = 512
    # Chunk overlap in tokens (experimental default).
    rag_chunk_overlap: int = 64
    # Minimum chunk size in tokens.
    rag_min_chunk_size: int = 50


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
