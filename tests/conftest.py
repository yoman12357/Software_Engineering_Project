"""Shared pytest fixtures.

Tests use an isolated in-memory SQLite database so the development database
at ``./data/cybersrs.db`` is never touched (NFR-023 / TEST_STRATEGY §1).
"""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.config import Settings
from src.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Yield a TestClient bound to an app isolated to in-memory SQLite."""
    settings = Settings(
        _env_file=None,
        env="testing",
        log_level="WARNING",
        database_url="sqlite:///:memory:",
        llm_provider="mock",
    )
    application = create_app(settings)
    with TestClient(application) as c:
        yield c


@pytest.fixture
def app(client: TestClient) -> FastAPI:
    """Return the FastAPI application instance behind the test client."""
    return client.app  # type: ignore[return-value]


@pytest.fixture
def sample_project_payload() -> dict:
    """A valid project creation payload."""
    return {
        "name": "Campus Firewall",
        "description": "A firewall and network monitoring system for a college campus.",
    }
