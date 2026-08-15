"""CyberSRS FastAPI application entry point.

Phase 1B scope: mock AI pipeline. The deterministic MockLLMProvider is wired
behind the LLMProvider abstraction; no real Ollama/Qwen calls, RAG, embeddings,
or ChromaDB are used. Phase 2 will swap the provider without changing routes.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from .api import errors
from .api.routes import analysis, clarifications, health, projects, provenance, srs
from .core.config import Settings, get_settings
from .core.logging import configure_logging
from .db.database import Database
from .llm.factory import create_llm_provider


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Args:
        settings: Application settings; defaults to the cached settings object.

    Returns:
        A configured FastAPI app with routers, error handling, and a database
        initialized on startup.
    """
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Initialise the database once at startup and clean up on exit."""
        # SQLite cannot create parent directories; ensure the file's folder
        # exists before the engine connects.
        if app_settings.database_url.startswith("sqlite"):
            db_path = app_settings.database_url.replace("sqlite:///", "", 1)
            if db_path not in ("", ":memory:"):
                parent = Path(db_path).expanduser().resolve().parent
                parent.mkdir(parents=True, exist_ok=True)

        database = Database(app_settings.database_url)
        database.init_db()
        app.state.database = database
        yield
        # SQLAlchemy engines are disposed on shutdown for clean process exit.
        database.engine.dispose()

    app = FastAPI(
        title="CyberSRS API",
        description=(
            "CyberSRS backend API. Phase 1B scope: project management, health, "
            "description analysis, and clarification endpoints using the "
            "deterministic mock LLM provider."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    # Expose the configured settings so request-scoped code (for example the
    # body-size-limit dependency) reads the same values used at startup.
    app.state.settings = app_settings

    # Phase 1B: build the configured LLM provider once (mock). Phase 2 swaps
    # this for the Ollama-backed provider behind the same abstraction.
    app.state.llm_provider = create_llm_provider(app_settings)

    # Centralised, safe error handling (SEC-046: no stack traces or internal
    # paths are exposed to clients).
    errors.register_error_handlers(app)

    # Route wiring under a single versioned API prefix. Routers are mounted
    # at /api/v1 so OpenAPI paths are grouped under the version prefix.
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(analysis.router, prefix="/api/v1")
    app.include_router(clarifications.router, prefix="/api/v1")
    app.include_router(srs.router, prefix="/api/v1")
    app.include_router(provenance.router, prefix="/api/v1")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="127.0.0.1", port=get_settings().backend_port, reload=True)
