"""API tests for description analysis and project-context retrieval (Phase 1B)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.db import models
from src.db.models import Project


def _create_project(client: TestClient, description: str | None = None) -> str:
    """Create a project and return its ID."""
    payload = {
        "name": "Campus Firewall",
        "description": description
        or "I want to build a firewall and monitoring system for my college network.",
    }
    return client.post("/api/v1/projects", json=payload).json()["id"]


def test_analyse_project_returns_valid_analysis(client: TestClient, app: FastAPI) -> None:
    """POST /analyse returns a schema-valid analysis with inferred categories."""
    project_id = _create_project(client)

    response = client.post(f"/api/v1/projects/{project_id}/analyse")
    assert response.status_code == 200
    body = response.json()

    assert body["project_id"] == project_id
    assert body["has_missing_information"] is True
    assert body["provider"] == "mock"
    assert body["model_name"]

    analysis = body["analysis"]
    assert analysis["inferred_categories"] == ["CAT-02", "CAT-03"]
    assert analysis["stakeholders"]
    assert analysis["assets"]
    assert analysis["users"]
    assert analysis["constraints"]
    assert analysis["goals"]
    assert analysis["project_summary"]
    assert "Expected number of network nodes" in analysis["missing_information"]


def test_analyse_project_persists_context_and_updates_project(
    client: TestClient, app: FastAPI
) -> None:
    """Analysis persists a ProjectContext and updates the project status."""
    project_id = _create_project(client)

    response = client.post(f"/api/v1/projects/{project_id}/analyse")
    assert response.status_code == 200

    # Project status became 'clarifying' (missing information detected).
    project = client.get(f"/api/v1/projects/{project_id}").json()
    assert project["status"] == "clarifying"
    assert project["inferred_categories"] == ["CAT-02", "CAT-03"]

    # A context row exists in the database.
    database = app.state.database
    with database.session_factory() as session:
        contexts = (
            session.query(models.ProjectContext)
            .filter(models.ProjectContext.project_id == project_id)
            .all()
        )
    assert len(contexts) == 1
    assert contexts[0].inferred_categories == ["CAT-02", "CAT-03"]


def test_get_project_context_returns_stored_context(
    client: TestClient,
) -> None:
    """GET /context returns the persisted ProjectContext."""
    project_id = _create_project(client)
    client.post(f"/api/v1/projects/{project_id}/analyse")

    response = client.get(f"/api/v1/projects/{project_id}/context")
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project_id
    assert body["inferred_categories"] == ["CAT-02", "CAT-03"]
    assert body["enriched_context"] is None


def test_analyse_missing_project_returns_404(client: TestClient) -> None:
    """Analysing a nonexistent project returns the standard 404 envelope."""
    response = client.post("/api/v1/projects/00000000-0000-0000-0000-000000000000/analyse")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"


def test_analyse_empty_description_returns_400(client: TestClient, app: FastAPI) -> None:
    """A project whose stored description is blank is rejected (400)."""
    project_id = _create_project(client)

    # Project creation validates non-empty descriptions, so blank the stored
    # value directly to simulate a corrupted/empty stored description.
    database = app.state.database
    with database.session_factory() as session:
        project = session.get(Project, project_id)
        assert project is not None
        project.description = "   "
        session.commit()

    response = client.post(f"/api/v1/projects/{project_id}/analyse")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "empty_description"


def test_get_context_without_analysis_returns_404(client: TestClient) -> None:
    """GET /context on a project with no analysis returns 404."""
    project_id = _create_project(client)
    response = client.get(f"/api/v1/projects/{project_id}/context")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_context_not_found"


def test_get_context_missing_project_returns_404(client: TestClient) -> None:
    """GET /context on a nonexistent project returns 404."""
    response = client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000/context")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"
