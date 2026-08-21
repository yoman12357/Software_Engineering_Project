"""Tests for the configuration loader (TEST_STRATEGY: unit config loading)."""

from src.core.config import Settings


def test_default_settings_apply() -> None:
    """All documented CYBERSRS_* defaults are applied when unset."""
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.env == "development"
    assert settings.log_level == "INFO"
    assert settings.database_url == "sqlite:///./data/cybersrs.db"
    assert settings.backend_port == 8000
    assert settings.frontend_port == 5173
    assert settings.max_request_body_bytes == 1_048_576
    assert settings.max_projects == 100
    # Embeddings must default to the local nomic-embed-text model.
    assert settings.embedding_model == "nomic-embed-text"
    assert settings.model_name == "qwen3:4b-instruct-2507-q4_K_M"
    assert settings.ollama_num_predict == 5200
    assert settings.ollama_repeat_penalty == 1.1
    assert settings.ollama_repeat_last_n == 256
    assert settings.ollama_temperature == 0.0
    assert settings.ollama_top_p == 0.9


def test_environment_overrides_defaults(monkeypatch) -> None:
    """Environment variables override defaults (CYBERSRS_ prefix)."""
    monkeypatch.setenv("CYBERSRS_LOG_LEVEL", "ERROR")
    monkeypatch.setenv("CYBERSRS_DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("CYBERSRS_MAX_REQUEST_BODY_BYTES", "2048")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.log_level == "ERROR"
    assert settings.database_url == "sqlite:///:memory:"
    assert settings.max_request_body_bytes == 2048


def test_rag_enabled_alias_accepts_simple_env_name(monkeypatch) -> None:
    """The plain RAG_ENABLED alias enables retrieval augmentation."""
    monkeypatch.setenv("RAG_ENABLED", "true")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.rag_enabled is True
