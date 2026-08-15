"""Health check endpoint per API_CONTRACT.md."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..dependencies import get_db

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health-check response payload."""

    status: str
    service: str
    database_ok: bool


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Return service and dependency health.

    The database is probed with a trivial query; the response reports whether
    the API and its primary dependency (SQLite) are operational.
    """
    database_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - exercised only when DB is broken
        database_ok = False

    return HealthResponse(
        status="ok" if database_ok else "degraded",
        service="cybersrs-api",
        database_ok=database_ok,
    )
