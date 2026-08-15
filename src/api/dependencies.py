"""FastAPI dependency providers.

The database instance is created once from application configuration and
stored on ``app.state`` by the lifespan. The ``get_db`` dependency yields a
``Session`` bound to the request.
"""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session

from ..core.config import Settings
from ..core.exceptions import BodyTooLargeError
from ..llm.base import LLMProvider
from .middleware import body_exceeds_limit


def get_db(request: Request) -> Iterator[Session]:
    """Yield a fresh database session for the duration of a request."""
    database = request.app.state.database
    session = database.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_app_settings(request: Request) -> Settings:
    """Return the settings instance bound to the application at startup."""
    return request.app.state.settings


def get_llm_provider(request: Request) -> LLMProvider:
    """Return the LLM provider instance bound to the application.

    The provider is created once at startup from application settings via
    :func:`create_llm_provider` and shared across requests. Phase 1B always
    returns the deterministic :class:`MockLLMProvider`; Phase 2 will swap in
    the Ollama-backed provider without changing route code.
    """
    return request.app.state.llm_provider


async def enforce_request_body_size(request: Request) -> None:
    """Reject request bodies larger than the configured limit (SEC-011).

    Reads the body once and raises :class:`BodyTooLargeError` when it exceeds
    ``CYBERSRS_MAX_REQUEST_BODY_BYTES``. The body is cached on the request by
    Starlette, so the endpoint can still consume it afterwards.
    """
    max_bytes = get_app_settings(request).max_request_body_bytes
    body = await request.body()
    if body_exceeds_limit(body, max_bytes):
        raise BodyTooLargeError()
