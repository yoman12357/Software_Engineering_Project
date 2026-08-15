"""Security-control tests for the Phase 1 middleware (SEC-011, SEC-046)."""

from fastapi.testclient import TestClient

from src.core.config import Settings
from src.main import create_app


def test_body_size_limit_rejects_oversized_request() -> None:
    """A request body larger than the limit returns 413 (SEC-011)."""
    settings = Settings(
        _env_file=None,
        env="testing",
        log_level="WARNING",
        database_url="sqlite:///:memory:",
        max_request_body_bytes=100,
        llm_provider="mock",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        payload = {"name": "x" * 200, "description": "y" * 200}
        # The body is > 100 bytes, so the dependency rejects it with 413
        # before the schema validator runs.
        response = client.post("/api/v1/projects", json=payload)
        assert response.status_code == 413
        body = response.json()
        assert body["error"]["code"] == "request_body_too_large"


def test_body_size_limit_allows_under_limit_request() -> None:
    """Requests within the limit are processed normally (SEC-011)."""
    settings = Settings(
        _env_file=None,
        env="testing",
        log_level="WARNING",
        database_url="sqlite:///:memory:",
        max_request_body_bytes=10_000,
        llm_provider="mock",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/projects",
            json={"name": "Small", "description": "A small valid project."},
        )
        assert response.status_code == 201


def test_body_size_limit_uses_app_settings_not_global_default() -> None:
    """The limit read from the app's own settings, not a global default."""
    settings = Settings(
        _env_file=None,
        env="testing",
        log_level="WARNING",
        database_url="sqlite:///:memory:",
        max_request_body_bytes=50,
        llm_provider="mock",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/projects",
            json={"name": "Tiny", "description": "A tiny but valid description."},
        )
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "request_body_too_large"
