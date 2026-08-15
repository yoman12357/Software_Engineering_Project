"""Apply the canonical additive CyberSRS database migrations."""

from __future__ import annotations

from src.core.config import Settings
from src.db.database import Database


def main() -> int:
    """Initialize missing tables and apply idempotent compatibility columns."""
    database = Database(Settings().database_url)
    database.init_db()
    database.engine.dispose()
    print("CyberSRS database migration completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
