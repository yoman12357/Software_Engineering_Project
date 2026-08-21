"""Tests for the PDF export and source-chunk endpoints (Phase 1C additions)."""

from fastapi.testclient import TestClient

DESCRIPTION = "I want to build a firewall and monitoring system for my college network."


def _create_analysed_project(client: TestClient) -> str:
    """Create + analyse a project and return its ID."""
    payload = {"name": "Campus Firewall", "description": DESCRIPTION}
    project_id = client.post("/api/v1/projects", json=payload).json()["id"]
    response = client.post(f"/api/v1/projects/{project_id}/analyse")
    assert response.status_code == 200
    return project_id


def _generate_srs(client: TestClient, project_id: str) -> dict:
    """Generate an SRS and return the generation response."""
    response = client.post(f"/api/v1/projects/{project_id}/srs/generate")
    assert response.status_code == 200
    return response.json()


def test_export_srs_pdf_returns_pdf(client: TestClient) -> None:
    """The PDF export endpoint returns an application/pdf attachment."""
    project_id = _create_analysed_project(client)
    generated = _generate_srs(client, project_id)
    version_id = generated["version_id"]

    response = client.get(
        f"/api/v1/projects/{project_id}/srs/versions/{version_id}/export/pdf"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers.get("content-disposition", "")
    assert response.content[:5] == b"%PDF-"  # PDF magic bytes


def test_export_srs_pdf_unknown_version_returns_404(client: TestClient) -> None:
    """Exporting a non-existent version returns a structured 404."""
    project_id = _create_analysed_project(client)

    response = client.get(
        f"/api/v1/projects/{project_id}/srs/versions/does-not-exist/export/pdf"
    )

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "srs_version_not_found"


def test_get_srs_sources_returns_empty_list(client: TestClient) -> None:
    """The sources endpoint returns the sources envelope (empty with mock provider)."""
    project_id = _create_analysed_project(client)
    generated = _generate_srs(client, project_id)
    version_id = generated["version_id"]

    response = client.get(
        f"/api/v1/projects/{project_id}/srs/versions/{version_id}/sources"
    )

    assert response.status_code == 200
    body = response.json()
    assert "sources" in body
    assert isinstance(body["sources"], list)


def test_get_srs_sources_unknown_version_returns_404(client: TestClient) -> None:
    """The sources endpoint returns 404 for an unknown version."""
    project_id = _create_analysed_project(client)

    response = client.get(
        f"/api/v1/projects/{project_id}/srs/versions/does-not-exist/sources"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "srs_version_not_found"


def test_get_srs_source_chunk_unknown_returns_404(client: TestClient) -> None:
    """Fetching an uncited chunk returns a structured 404."""
    project_id = _create_analysed_project(client)
    generated = _generate_srs(client, project_id)
    version_id = generated["version_id"]

    response = client.get(
        f"/api/v1/projects/{project_id}/srs/versions/{version_id}/sources/nonexistent_chunk"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "srs_version_not_found"


def test_pdf_export_service_render() -> None:
    """The PDF service renders a minimal SRS dict to valid PDF bytes."""
    from src.services.pdf_export_service import PDFExportService

    service = PDFExportService.__new__(PDFExportService)

    srs_data = {
        "metadata": {
            "project_name": "Test Project",
            "version": 1,
            "generated_at": "2026-01-01T00:00:00Z",
            "model_name": "mock",
        },
        "project_overview": {"description": "Test overview", "purpose": "Test purpose"},
        "scope": {"in_scope": ["A"], "out_of_scope": ["B"]},
        "assumptions": ["Assumption one"],
        "stakeholders": ["Stakeholder"],
        "user_roles": ["Admin"],
        "functional_requirements": [
            {
                "id": "FR-001",
                "title": "Login",
                "statement": "The system shall authenticate users.",
                "rationale": "Security.",
                "acceptance_criteria": "Login succeeds with valid credentials.",
                "priority": "must",
                "confidence": "high",
                "dependencies": [],
                "source_references": [],
            }
        ],
        "architecture_summary": {
            "description": "Simple architecture",
            "components": [
                {
                    "name": "Web",
                    "description": "Web tier",
                    "responsibilities": ["Serve UI"],
                }
            ],
        },
        "threats": [],
        "risks": [],
    }

    pdf_bytes = service.render_pdf_bytes(srs_data)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:5] == b"%PDF-"
    assert len(pdf_bytes) > 1000
