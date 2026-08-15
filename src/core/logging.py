"""Structured JSON logging configuration.

Log output is a single JSON object per line. User-supplied content (project
descriptions, clarification answers, generated SRS text) is never logged —
see SEC-031 / SEC-032 in the security requirements.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """Format log records as a single line of JSON."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("event", "component", "duration_ms", "method", "path", "status_code"):
            if hasattr(record, key):
                entry[key] = getattr(record, key)
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def configure_logging(level: str) -> None:
    """Configure the root logger with a JSON formatter writing to stdout.

    Args:
        level: The requested log level name (e.g. ``"INFO"``). Unknown or empty
            values fall back to ``INFO``.
    """
    normalized = (level or "INFO").upper()
    log_level = getattr(logging, normalized, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)
    root.propagate = False

    # Keep uvicorn's own access logs out of the root handler to avoid
    # duplicated or inconsistent output during normal use.
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False
