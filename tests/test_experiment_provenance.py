"""Experiment/model provenance, migration, and API regression tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select, text

from src.core.config import Settings
from src.core.exceptions import InvalidGeneratedOutputError
from src.db import models
from src.db.database import Database
from src.llm.base import LLMOutputError, LLMProvider, LLMRequest, LLMResponse, LLMTask
from src.llm.mock_provider import MockLLMProvider
from src.rag.retrieval import RetrievalContext, RetrievedChunk
from src.schemas.project import generate_uuid
from src.schemas.srs import SRSSchema
from src.services.srs_generation_service import SRSGenerationService

DESCRIPTION = "A firewall and network monitoring system for a college campus."


def _create_analysed_project(client: TestClient) -> str:
    """Create and analyse one project."""
    response = client.post(
        "/api/v1/projects",
        json={"name": "Provenance Test", "description": DESCRIPTION},
    )
    project_id = response.json()["id"]
    assert client.post(f"/api/v1/projects/{project_id}/analyse").status_code == 200
    return project_id


class FailingProvider(LLMProvider):
    """Provider used to verify durable failed-run records."""

    provider_name = "failing-test"

    def __init__(self) -> None:
        super().__init__("failing-model")

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Fail every generation without including prompt content."""
        raise LLMOutputError(f"forced {request.task.value} failure")


class CitingMockProvider(MockLLMProvider):
    """Mock provider that cites the static test retrieval result."""

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Add one valid source reference to the deterministic SRS payload."""
        response = super().generate(request)
        if request.task != LLMTask.SRS:
            return response
        payload = json.loads(response.content)
        payload["functional_requirements"][0]["source_references"] = [
            {
                "source_id": "doc-a_chunk_1",
                "document_title": "Test Standard",
                "section_heading": "Section 1",
                "relevance_score": 0.91,
            }
        ]
        return LLMResponse(
            content=json.dumps(payload),
            model_name=response.model_name,
            is_deterministic=True,
        )


class StaticRetriever:
    """Return fixed identifier-only RAG provenance without touching Chroma."""

    def retrieve(self, *_args, **_kwargs) -> RetrievalContext:
        """Return one retrieved chunk with source metadata."""
        return RetrievalContext(
            chunks=[
                RetrievedChunk(
                    chunk_id="doc-a_chunk_1",
                    text="Systems should enforce a deny-by-default network policy.",
                    metadata={
                        "source_id": "doc-a",
                        "document_title": "Test Standard",
                        "section_heading": "Section 1",
                    },
                    relevance_score=0.91,
                    distance=0.09,
                )
            ],
            query_texts=["network firewall requirements"],
            total_chunks=1,
            kb_version="kb-test-v1",
            retrieval_time_ms=2,
        )


class RetryingSRSProvider(MockLLMProvider):
    """Return one schema-invalid SRS followed by the canonical mock SRS."""

    def __init__(self, *, always_invalid_threat_id: bool = False) -> None:
        super().__init__()
        self.always_invalid_threat_id = always_invalid_threat_id
        self.srs_requests: list[LLMRequest] = []
        self.raw_outputs: list[str] = []

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Capture SRS attempts and inject only the requested test defects."""
        response = super().generate(request)
        if request.task != LLMTask.SRS:
            return response
        self.srs_requests.append(request)
        payload = json.loads(response.content)
        if len(self.srs_requests) == 1:
            payload["functional_requirements"] = []
        if self.always_invalid_threat_id:
            payload["threats"][0]["threat_id"] = "THR-1"
        raw = json.dumps(payload)
        if len(self.srs_requests) == 1:
            raw = f"</tool_call>\n{raw}"
        self.raw_outputs.append(raw)
        return LLMResponse(
            content=raw,
            model_name=self.model_name,
            is_deterministic=True,
            prompt_eval_count=100 + len(self.srs_requests),
            eval_count=50 + len(self.srs_requests),
        )


def test_additive_migration_preserves_legacy_rows(tmp_path: Path) -> None:
    """An older SQLite table gains a nullable run link without data loss."""
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE srs_version (id VARCHAR(36) PRIMARY KEY)")
        connection.execute("INSERT INTO srs_version (id) VALUES ('legacy-srs')")

    database = Database(f"sqlite:///{database_path.as_posix()}")
    database.init_db()

    inspector = inspect(database.engine)
    assert "model_run" in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("srs_version")}
    assert {
        "model_variant",
        "model_name",
        "adapter_name",
        "rag_enabled",
        "generation_metadata",
        "model_run_id",
    } <= columns
    with database.engine.connect() as connection:
        result = connection.execute(
            text("SELECT id, model_run_id FROM srs_version WHERE id = 'legacy-srs'")
        ).one()
    assert result == ("legacy-srs", None)

    # A second startup migration is a no-op and retains the legacy row.
    database.init_db()
    with database.engine.connect() as connection:
        count = connection.execute(
            text("SELECT COUNT(*) FROM srs_version WHERE id = 'legacy-srs'")
        ).scalar_one()
    assert count == 1


def test_analysis_and_clarification_artifacts_link_to_successful_runs(
    client: TestClient, app: FastAPI
) -> None:
    """New context and question artifacts reference completed model runs."""
    project_id = _create_analysed_project(client)
    response = client.post(f"/api/v1/projects/{project_id}/clarifications/generate")
    assert response.status_code == 200

    with app.state.database.session_factory() as session:
        context = session.scalar(
            select(models.ProjectContext).where(models.ProjectContext.project_id == project_id)
        )
        questions = list(
            session.scalars(
                select(models.ClarificationQuestion).where(
                    models.ClarificationQuestion.project_id == project_id
                )
            )
        )
        assert context is not None and context.model_run_id is not None
        assert context.model_run is not None
        assert context.model_run.operation_type == "project_analysis"
        assert context.model_run.status == "succeeded"
        assert context.model_run.completed_at is not None
        assert context.model_run.latency_seconds is not None
        assert questions
        assert all(question.model_run_id is not None for question in questions)
        assert len({question.model_run_id for question in questions}) == 1
        assert questions[0].model_run is not None
        assert questions[0].model_run.operation_type == "clarification_generation"


def test_failed_srs_generation_persists_sanitized_run(
    client: TestClient, app: FastAPI
) -> None:
    """A provider failure leaves a failed run and no invented artifact link."""
    project_id = _create_analysed_project(client)
    with app.state.database.session_factory() as session:
        service = SRSGenerationService(session, FailingProvider(), app.state.settings)
        with pytest.raises(LLMOutputError):
            service.generate_srs(project_id, use_rag=False)

    with app.state.database.session_factory() as session:
        run = session.scalar(
            select(models.ModelRun)
            .where(
                models.ModelRun.project_id == project_id,
                models.ModelRun.operation_type == "srs_generation",
            )
            .order_by(models.ModelRun.started_at.desc())
        )
        assert run is not None
        assert run.status == "failed"
        assert run.completed_at is not None
        assert run.latency_seconds is not None
        assert run.error_message == "Operation failed (LLMOutputError)"
        assert DESCRIPTION not in run.error_message
        assert session.scalar(
            select(models.SRSVersion).where(models.SRSVersion.project_id == project_id)
        ) is None


def test_srs_schema_failure_retries_once_with_sanitized_errors(
    client: TestClient, app: FastAPI
) -> None:
    """A missing required section triggers one bounded full-SRS correction."""
    project_id = _create_analysed_project(client)
    provider = RetryingSRSProvider()
    settings = Settings(
        _env_file=None,
        env="testing",
        database_url="sqlite:///:memory:",
        llm_provider="mock",
        llm_max_retries=1,
    )

    with app.state.database.session_factory() as session:
        service = SRSGenerationService(session, provider, settings)
        generated = service.generate_srs(project_id, use_rag=False)

    assert len(provider.srs_requests) == 2
    assert provider.srs_requests[0].response_schema is SRSSchema
    assert provider.srs_requests[1].response_schema is SRSSchema
    assert "functional_requirements" in provider.srs_requests[1].user_content
    assert "</tool_call>" not in provider.srs_requests[1].user_content
    with app.state.database.session_factory() as session:
        version = session.get(models.SRSVersion, generated.version_id)
        assert version is not None and version.model_run is not None
        attempts = version.model_run.metadata_json["generation_attempts"]
        assert [item["status"] for item in attempts] == ["schema_invalid", "valid"]
        assert attempts[0]["wrapper_removed"] is True
        assert attempts[0]["input_tokens"] == 101
        assert attempts[1]["output_tokens"] == 52


def test_malformed_threat_id_still_fails_after_bounded_retry(
    client: TestClient, app: FastAPI
) -> None:
    """Strict validation never canonicalizes or invents malformed threat IDs."""
    project_id = _create_analysed_project(client)
    provider = RetryingSRSProvider(always_invalid_threat_id=True)
    settings = Settings(
        _env_file=None,
        env="testing",
        database_url="sqlite:///:memory:",
        llm_provider="mock",
        llm_max_retries=1,
    )

    with app.state.database.session_factory() as session:
        service = SRSGenerationService(session, provider, settings)
        with pytest.raises(InvalidGeneratedOutputError, match="threats.0.threat_id"):
            service.generate_srs(project_id, use_rag=False)

    assert len(provider.srs_requests) == 2
    with app.state.database.session_factory() as session:
        run = session.scalar(
            select(models.ModelRun)
            .where(
                models.ModelRun.project_id == project_id,
                models.ModelRun.operation_type == "srs_generation",
            )
            .order_by(models.ModelRun.started_at.desc())
        )
        assert run is not None and run.status == "failed"
        assert [item["status"] for item in run.metadata_json["generation_attempts"]] == [
            "schema_invalid",
            "schema_invalid",
        ]
        assert session.scalar(
            select(models.SRSVersion).where(models.SRSVersion.project_id == project_id)
        ) is None


def test_failed_rag_srs_keeps_retrieval_ids_without_fabricating_citations(
    client: TestClient, app: FastAPI
) -> None:
    """Failed generation retains RAG IDs while citation IDs remain empty."""
    project_id = _create_analysed_project(client)
    settings = Settings(
        _env_file=None,
        env="testing",
        database_url="sqlite:///:memory:",
        llm_provider="mock",
        rag_enabled=True,
        knowledge_base_version="kb-test-v1",
    )

    with app.state.database.session_factory() as session:
        service = SRSGenerationService(session, FailingProvider(), settings)
        service._retriever = StaticRetriever()  # type: ignore[assignment]
        with pytest.raises(LLMOutputError):
            service.generate_srs(project_id, use_rag=True)

    with app.state.database.session_factory() as session:
        run = session.scalar(
            select(models.ModelRun)
            .where(
                models.ModelRun.project_id == project_id,
                models.ModelRun.operation_type == "srs_generation",
            )
            .order_by(models.ModelRun.started_at.desc())
        )
        assert run is not None and run.status == "failed"
        assert run.rag_enabled is True
        assert run.retrieved_chunk_ids == ["doc-a_chunk_1"]
        assert run.retrieved_document_ids == ["doc-a"]
        assert run.citation_ids == []


def test_rag_identifiers_and_artifact_association_are_persisted(
    client: TestClient, app: FastAPI
) -> None:
    """SRS provenance records KB, chunk, document, and citation identifiers."""
    project_id = _create_analysed_project(client)
    settings = Settings(
        _env_file=None,
        env="testing",
        database_url="sqlite:///:memory:",
        llm_provider="mock",
        rag_enabled=True,
        knowledge_base_version="kb-test-v1",
    )

    with app.state.database.session_factory() as session:
        service = SRSGenerationService(session, CitingMockProvider(), settings)
        service._retriever = StaticRetriever()  # type: ignore[assignment]
        generated = service.generate_srs(project_id, use_rag=True)

    with app.state.database.session_factory() as session:
        version = session.get(models.SRSVersion, generated.version_id)
        assert version is not None and version.model_run is not None
        run = version.model_run
        assert run.status == "succeeded"
        assert run.rag_enabled is True
        assert run.embedding_model == "nomic-embed-text"
        assert run.knowledge_base_version == "kb-test-v1"
        assert run.retrieved_chunk_ids == ["doc-a_chunk_1"]
        assert run.retrieved_document_ids == ["doc-a"]
        assert run.citation_ids == ["doc-a_chunk_1"]
        assert version.model_run_id == run.id

    response = client.get(
        f"/api/v1/projects/{project_id}/srs/versions/{generated.version_id}/provenance"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provenance_status"] == "recorded"
    assert body["model_run"]["retrieved_chunk_ids"] == ["doc-a_chunk_1"]
    assert body["model_run"]["citation_ids"] == ["doc-a_chunk_1"]
    assert body["model_run"]["deterministic_validation_applied"] is True
    assert body["model_run"]["deterministic_repair_applied"] is True


def test_legacy_srs_provenance_is_explicitly_unknown(
    client: TestClient, app: FastAPI
) -> None:
    """Old SRS rows remain readable without invented provenance values."""
    project = client.post(
        "/api/v1/projects",
        json={"name": "Legacy", "description": DESCRIPTION},
    ).json()
    version_id = generate_uuid()
    with app.state.database.session_factory() as session:
        session.add(
            models.SRSVersion(
                id=version_id,
                project_id=project["id"],
                version_number=1,
                srs_json={},
                status="generated",
                model_run_id=None,
            )
        )
        session.commit()

    response = client.get(
        f"/api/v1/projects/{project['id']}/srs/versions/{version_id}/provenance"
    )
    assert response.status_code == 200
    assert response.json() == {
        "artifact_type": "srs",
        "artifact_id": version_id,
        "provenance_status": "legacy_unknown",
        "model_run": None,
    }


def test_model_info_is_allow_listed_and_contains_no_secrets(client: TestClient) -> None:
    """The demonstration endpoint cannot reveal paths, prompts, or credentials."""
    response = client.get("/api/v1/system/model-info")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "active_model_variant",
        "active_model_name",
        "provider",
        "rag_enabled",
        "embedding_model",
        "knowledge_base_version",
    }
    serialized = json.dumps(body).lower()
    for forbidden in (
        "database_url",
        "chroma_path",
        "ollama_base_url",
        "api_key",
        "password",
        "system_prompt",
        "user_content",
    ):
        assert forbidden not in serialized
