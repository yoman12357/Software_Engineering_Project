"""Backward-compatible entry point for the canonical database migration."""

from __future__ import annotations

from migrate_model_provenance import main

if __name__ == "__main__":
    raise SystemExit(main())
