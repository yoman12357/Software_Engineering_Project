"""Safe API schemas for model and artifact provenance."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ModelInfoResponse(BaseModel):
    """Read-only active model and RAG configuration."""

    active_model_variant: str
    active_model_name: str
    provider: str
    rag_enabled: bool
    embedding_model: str | None
    knowledge_base_version: str


class ModelRunRead(BaseModel):
    """Sanitized provenance fields for a completed or failed model run."""

    id: str
    operation_type: str
    model_variant: str
    model_name: str
    rag_enabled: bool
    embedding_model: str | None
    knowledge_base_version: str | None
    retrieved_chunk_ids: list[str]
    retrieved_document_ids: list[str]
    citation_ids: list[str]
    started_at: datetime
    completed_at: datetime | None
    latency_seconds: float | None
    status: str
    error_message: str | None
    deterministic_validation_applied: bool | None
    deterministic_repair_applied: bool | None


class ArtifactProvenanceResponse(BaseModel):
    """Model provenance associated with one generated artifact."""

    artifact_type: str
    artifact_id: str
    provenance_status: Literal["recorded", "legacy_unknown"]
    model_run: ModelRunRead | None
