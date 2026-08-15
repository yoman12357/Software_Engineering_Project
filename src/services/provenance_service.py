"""Experiment/model-run recording and safe provenance queries."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..core.config import Settings
from ..core.exceptions import ProjectNotFoundError, SRSVersionNotFoundError
from ..db.models import ModelRun
from ..llm.base import LLMProvider
from ..repositories.model_run_repository import ModelRunRepository
from ..repositories.project_repository import ProjectRepository
from ..repositories.srs_repository import SRSVersionRepository
from ..schemas.project import generate_uuid
from ..schemas.provenance import (
    ArtifactProvenanceResponse,
    ModelInfoResponse,
    ModelRunRead,
)

_UNKNOWN_KB_VERSION = "unknown"
_CORPUS_INVENTORY = (
    Path(__file__).resolve().parents[2] / "ai" / "evaluation" / "corpus_inventory.json"
)


def resolve_knowledge_base_version(settings: Settings) -> str:
    """Resolve a safe KB identifier without opening or changing Chroma data."""
    configured = settings.knowledge_base_version.strip()
    if configured and configured.lower() != _UNKNOWN_KB_VERSION:
        return configured
    try:
        payload = json.loads(_CORPUS_INVENTORY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _UNKNOWN_KB_VERSION
    version = payload.get("kb_version")
    return str(version) if version else _UNKNOWN_KB_VERSION


class ModelRunRecorder:
    """Record model-backed operations without storing prompts or user content."""

    def __init__(self, session: Session, settings: Settings, provider: LLMProvider) -> None:
        self._session = session
        self._settings = settings
        self._provider = provider
        self._runs = ModelRunRepository(session)

    def start(
        self,
        project_id: str,
        operation_type: str,
        *,
        rag_requested: bool = False,
        prompt_template_version: str,
    ) -> ModelRun:
        """Create and commit a running row before model inference begins."""
        model_run = ModelRun(
            id=generate_uuid(),
            project_id=project_id,
            operation_type=operation_type,
            model_variant=self._settings.model_variant.strip().lower() or "unknown",
            model_name=self._provider.model_name or "unknown",
            rag_enabled=False,
            embedding_model=self._settings.embedding_model if rag_requested else None,
            knowledge_base_version=(
                resolve_knowledge_base_version(self._settings) if rag_requested else None
            ),
            started_at=datetime.now(UTC),
            status="running",
            metadata_json={
                "provider": self._provider.provider_name,
                "prompt_template_version": prompt_template_version,
                "rag_requested": rag_requested,
            },
        )
        self._runs.add(model_run)
        self._session.commit()
        self._session.refresh(model_run)
        return model_run

    def succeed(
        self,
        model_run: ModelRun,
        *,
        artifact_type: str,
        artifact_ids: list[str],
        rag_enabled: bool = False,
        knowledge_base_version: str | None = None,
        retrieved_chunk_ids: list[str] | None = None,
        retrieved_document_ids: list[str] | None = None,
        citation_ids: list[str] | None = None,
        deterministic_validation_applied: bool,
        deterministic_repair_applied: bool,
        metadata: dict[str, Any] | None = None,
    ) -> ModelRun:
        """Complete a successful run and commit artifact associations atomically."""
        completed_at = datetime.now(UTC)
        model_run.completed_at = completed_at
        model_run.latency_seconds = max(
            0.0, (completed_at - model_run.started_at).total_seconds()
        )
        model_run.status = "succeeded"
        model_run.rag_enabled = rag_enabled
        model_run.embedding_model = self._settings.embedding_model if rag_enabled else None
        model_run.knowledge_base_version = knowledge_base_version if rag_enabled else None
        model_run.retrieved_chunk_ids = sorted(set(retrieved_chunk_ids or []))
        model_run.retrieved_document_ids = sorted(set(retrieved_document_ids or []))
        model_run.citation_ids = sorted(set(citation_ids or []))
        model_run.error_message = None
        model_run.metadata_json = {
            **(model_run.metadata_json or {}),
            "artifact_type": artifact_type,
            "artifact_ids": artifact_ids,
            "deterministic_validation_applied": deterministic_validation_applied,
            "deterministic_repair_applied": deterministic_repair_applied,
            **(metadata or {}),
        }
        self._session.commit()
        self._session.refresh(model_run)
        return model_run

    def record_retrieval(
        self,
        model_run: ModelRun,
        *,
        knowledge_base_version: str,
        retrieved_chunk_ids: list[str],
        retrieved_document_ids: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> ModelRun:
        """Persist RAG identifiers before generation so failures remain traceable."""
        model_run.rag_enabled = True
        model_run.embedding_model = self._settings.embedding_model
        model_run.knowledge_base_version = knowledge_base_version
        model_run.retrieved_chunk_ids = sorted(set(retrieved_chunk_ids))
        model_run.retrieved_document_ids = sorted(set(retrieved_document_ids))
        model_run.citation_ids = []
        model_run.metadata_json = {
            **(model_run.metadata_json or {}),
            **(metadata or {}),
        }
        self._session.commit()
        self._session.refresh(model_run)
        return model_run

    def record_attempts(
        self,
        model_run: ModelRun,
        attempts: list[dict[str, Any]],
    ) -> ModelRun:
        """Persist sanitized generation-attempt telemetry without raw prompts or output."""
        model_run.metadata_json = {
            **(model_run.metadata_json or {}),
            "generation_attempts": attempts,
        }
        self._session.commit()
        self._session.refresh(model_run)
        return model_run

    def fail(self, model_run: ModelRun, error: Exception) -> ModelRun:
        """Persist a sanitized failure after rolling back partial artifact writes."""
        model_run_id = model_run.id
        self._session.rollback()
        persisted = self._runs.get(model_run_id)
        if persisted is None:  # pragma: no cover - start() commits the row
            raise RuntimeError("Model run disappeared before failure recording")
        completed_at = datetime.now(UTC)
        persisted.completed_at = completed_at
        persisted.latency_seconds = max(
            0.0, (completed_at - persisted.started_at).total_seconds()
        )
        persisted.status = "failed"
        persisted.error_message = f"Operation failed ({type(error).__name__})"
        self._session.commit()
        self._session.refresh(persisted)
        return persisted


class ProvenanceQueryService:
    """Read-only queries used by provenance demonstration endpoints."""

    def __init__(self, session: Session) -> None:
        self._projects = ProjectRepository(session)
        self._versions = SRSVersionRepository(session)

    def get_srs_provenance(
        self, project_id: str, version_id: str
    ) -> ArtifactProvenanceResponse:
        """Return recorded provenance or an explicit legacy marker for an SRS."""
        if self._projects.get(project_id) is None:
            raise ProjectNotFoundError()
        version = self._versions.get_version(project_id, version_id)
        if version is None:
            raise SRSVersionNotFoundError()
        if version.model_run is None:
            return ArtifactProvenanceResponse(
                artifact_type="srs",
                artifact_id=version.id,
                provenance_status="legacy_unknown",
                model_run=None,
            )
        return ArtifactProvenanceResponse(
            artifact_type="srs",
            artifact_id=version.id,
            provenance_status="recorded",
            model_run=self._to_read(version.model_run),
        )

    @staticmethod
    def model_info(settings: Settings, provider: LLMProvider) -> ModelInfoResponse:
        """Build the allow-listed system model-information response."""
        return ModelInfoResponse(
            active_model_variant=settings.model_variant.strip().lower() or "unknown",
            active_model_name=provider.model_name or "unknown",
            provider=provider.provider_name,
            rag_enabled=settings.rag_enabled,
            embedding_model=settings.embedding_model,
            knowledge_base_version=resolve_knowledge_base_version(settings),
        )

    @staticmethod
    def _to_read(model_run: ModelRun) -> ModelRunRead:
        """Convert a run to the API allow-list without returning arbitrary metadata."""
        metadata = model_run.metadata_json or {}
        return ModelRunRead(
            id=model_run.id,
            operation_type=model_run.operation_type,
            model_variant=model_run.model_variant,
            model_name=model_run.model_name,
            rag_enabled=model_run.rag_enabled,
            embedding_model=model_run.embedding_model,
            knowledge_base_version=model_run.knowledge_base_version,
            retrieved_chunk_ids=model_run.retrieved_chunk_ids or [],
            retrieved_document_ids=model_run.retrieved_document_ids or [],
            citation_ids=model_run.citation_ids or [],
            started_at=model_run.started_at,
            completed_at=model_run.completed_at,
            latency_seconds=model_run.latency_seconds,
            status=model_run.status,
            error_message=model_run.error_message,
            deterministic_validation_applied=metadata.get(
                "deterministic_validation_applied"
            ),
            deterministic_repair_applied=metadata.get("deterministic_repair_applied"),
        )
