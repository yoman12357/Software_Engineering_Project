"""SQLAlchemy engine, session factory, and declarative base."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _make_engine(database_url: str):
    """Create a SQLAlchemy engine for the given database URL.

    SQLite-specific options (``check_same_thread``) are applied only when the
    URL points to a SQLite database. In-memory SQLite databases additionally
    use a static connection pool so the schema (created during startup) is
    visible to request-handler threads — a regular pool gives every thread its
    own private in-memory database. Other backends are created unchanged so
    the application can move to PostgreSQL post-MVP without structural change.
    """
    kwargs: dict = {}
    if database_url.startswith("sqlite"):
        # FastAPI + pytest can touch the same connection from different
        # threads; SQLite must permit it (each session still serialises).
        kwargs["connect_args"] = {"check_same_thread": False}
        if database_url in ("sqlite://", "sqlite:///:memory:"):
            kwargs["poolclass"] = StaticPool
    return create_engine(database_url, **kwargs)


class Database:
    """Owns the engine and session factory for the application lifetime."""

    def __init__(self, database_url: str) -> None:
        self.engine = _make_engine(database_url)
        self.session_factory = sessionmaker(
            bind=self.engine, autoflush=False, expire_on_commit=False
        )

    def init_db(self) -> None:
        """Create tables and apply additive compatibility migrations."""
        from . import models  # noqa: F401  (registers tables on Base)
        from .migrations import apply_compatibility_migrations

        Base.metadata.create_all(self.engine)
        apply_compatibility_migrations(self.engine)
