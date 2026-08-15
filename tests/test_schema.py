"""Database schema survey tests (ROADMAP Phase 1 gate).

The ROADMAP completion gate requires that the SQLite schema includes all
entities from DATA_MODEL.md. These tests verify every table exists and that
cascade deletion removes related rows (SEC-047).
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from src.db import models
from src.db.database import Database

EXPECTED_TABLES = {
    "project",
    "project_description",
    "clarification_question",
    "clarification_answer",
    "project_context",
    "srs_version",
    "requirement",
    "acceptance_criterion",
    "threat",
    "mitigation",
    "source_document",
    "retrieved_chunk",
    "generation_run",
    "model_run",
    "evaluation_run",
    "exported_document",
}


def test_schema_contains_all_data_model_tables(app: FastAPI) -> None:
    """Every entity from DATA_MODEL.md exists as a table."""
    database: Database = app.state.database
    inspector = inspect(database.engine)
    tables = set(inspector.get_table_names())
    assert EXPECTED_TABLES <= tables


def test_delete_project_cascades_to_related_records(
    client: TestClient, app: FastAPI, sample_project_payload: dict
) -> None:
    """Deleting a project removes related rows (SEC-047)."""
    created = client.post("/api/v1/projects", json=sample_project_payload).json()
    project_id = created["id"]

    database: Database = app.state.database
    with database.session_factory() as session:
        project = session.get(models.Project, project_id)
        assert project is not None
        # Add related records directly so the cascade path is exercised.
        srs = models.SRSVersion(
            id="10000000-0000-0000-0000-000000000001",
            project_id=project_id,
            version_number=1,
            srs_json={"metadata": {}},
            status="draft",
        )
        session.add(srs)
        session.commit()

    # Delete through the API.
    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204

    with database.session_factory() as session:
        assert session.get(models.Project, project_id) is None
        assert session.get(models.SRSVersion, "10000000-0000-0000-0000-000000000001") is None


def test_timestamps_are_timezone_aware_utc(
    client: TestClient, sample_project_payload: dict
) -> None:
    """Created/updated timestamps are stored as timezone-aware UTC (TEST_STRATEGY)."""
    created = client.post("/api/v1/projects", json=sample_project_payload).json()
    assert created["created_at"].endswith("+00:00") or created["created_at"].endswith("Z")
    assert created["updated_at"].endswith("+00:00") or created["updated_at"].endswith("Z")
