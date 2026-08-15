"""Persistence queries for experiment and model provenance."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import ModelRun


class ModelRunRepository:
    """Data-access helpers for :class:`ModelRun`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, model_run: ModelRun) -> ModelRun:
        """Persist and flush a model run."""
        self._session.add(model_run)
        self._session.flush()
        return model_run

    def get(self, model_run_id: str) -> ModelRun | None:
        """Return a model run by ID, or ``None``."""
        return self._session.get(ModelRun, model_run_id)

    def list_for_project(self, project_id: str) -> list[ModelRun]:
        """Return project runs newest first."""
        statement = (
            select(ModelRun)
            .where(ModelRun.project_id == project_id)
            .order_by(ModelRun.started_at.desc())
        )
        return list(self._session.scalars(statement))
