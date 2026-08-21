"""API tests for SRS generation, persistence, retrieval, editing, and validation (Phase 1C)."""

import copy
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm.attributes import flag_modified

from src.core.exceptions import InvalidGeneratedOutputError
from src.db import models
from src.services.srs_generation_service import SRSGenerationService

DESCRIPTION = "I want to build a firewall and monitoring system for my college network."


def _create_analysed_project(client: TestClient) -> str:
    """Create + analyse a project and return its ID."""
    payload = {"name": "Campus Firewall", "description": DESCRIPTION}
    project_id = client.post("/api/v1/projects", json=payload).json()["id"]
    response = client.post(f"/api/v1/projects/{project_id}/analyse")
    assert response.status_code == 200
    return project_id


def _generate_srs(client: TestClient, project_id: str) -> dict:
    """Generate an SRS and assert success; return the generation response."""
    response = client.post(f"/api/v1/projects/{project_id}/srs/generate")
    assert response.status_code == 200
    return response.json()


def test_generate_srs_returns_version(client: TestClient) -> None:
    """Generating an SRS returns a version with number 1 and status generated."""
    project_id = _create_analysed_project(client)
    body = _generate_srs(client, project_id)

    assert body["project_id"] == project_id
    assert body["version_number"] == 1
    assert body["status"] == "generated"


def test_generate_srs_stream_emits_validated_progress(client: TestClient) -> None:
    """The streaming endpoint emits ordered phases and a terminal result."""
    project_id = _create_analysed_project(client)
    response = client.post(f"/api/v1/projects/{project_id}/srs/generate/stream")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert [event["phase"] for event in events] == [
        "preparing",
        "retrieving",
        "generating",
        "validating",
        "completed",
    ]
    assert events[-1]["progress"] == 100
    assert events[-1]["result"]["version_number"] == 1


def test_generate_srs_stream_emits_terminal_failure(
    client: TestClient,
    monkeypatch,
) -> None:
    """A model/schema failure ends the stream with a safe retryable event."""
    project_id = _create_analysed_project(client)

    def fail_generation(*_args, **_kwargs):
        raise InvalidGeneratedOutputError()

    monkeypatch.setattr(SRSGenerationService, "generate_srs", fail_generation)
    response = client.post(f"/api/v1/projects/{project_id}/srs/generate/stream")
    events = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]

    assert response.status_code == 200
    assert events[-1] == {
        "phase": "failed",
        "progress": 100,
        "message": "The model produced an invalid response.",
        "result": None,
        "error_code": "invalid_generated_output",
    }


def test_generate_srs_persists_valid_document(client: TestClient, app: FastAPI) -> None:
    """The persisted SRS JSON is schema-valid and contains the expected sections."""
    project_id = _create_analysed_project(client)
    generated = _generate_srs(client, project_id)

    database = app.state.database
    with database.session_factory() as session:
        version = session.get(models.SRSVersion, generated["version_id"])
        assert version is not None
        srs = version.srs_json

    assert srs["metadata"]["project_name"] == "Campus Firewall"
    assert srs["metadata"]["version"] == 1
    assert srs["metadata"]["inferred_categories"] == ["CAT-02", "CAT-03"]
    assert srs["functional_requirements"]
    assert srs["non_functional_requirements"]
    assert srs["security_requirements"]
    assert srs["data_requirements"]
    assert srs["network_requirements"]
    assert srs["architecture_summary"]["components"]
    assert srs["threats"]
    assert srs["mitigations"]
    assert srs["testing_strategy"]
    assert srs["risks"]
    assert srs["references"] == []  # RAG does not exist (Phase 1C rule)


def test_generated_requirement_ids_are_unique(client: TestClient) -> None:
    """All generated requirement IDs are unique across sections (FR-047)."""
    project_id = _create_analysed_project(client)
    _generate_srs(client, project_id)
    srs = client.get(f"/api/v1/projects/{project_id}/srs").json()["srs"]

    ids = []
    for section in (
        "functional_requirements",
        "non_functional_requirements",
        "security_requirements",
        "data_requirements",
        "network_requirements",
    ):
        ids.extend(item["id"] for item in srs[section])
    assert len(ids) == len(set(ids))
    assert any(item["id"].startswith("FR-") for item in srs["functional_requirements"])
    assert any(item["id"].startswith("NFR-") for item in srs["non_functional_requirements"])
    assert any(item["id"].startswith("SEC-") for item in srs["security_requirements"])


def test_generated_requirement_has_no_source_references(client: TestClient) -> None:
    """Requirements must not invent external citations (Phase 1C rule)."""
    project_id = _create_analysed_project(client)
    _generate_srs(client, project_id)
    srs = client.get(f"/api/v1/projects/{project_id}/srs").json()["srs"]
    for section in (
        "functional_requirements",
        "non_functional_requirements",
        "security_requirements",
    ):
        for requirement in srs[section]:
            assert requirement["source_references"] == []


def test_generate_srs_requires_analysis(client: TestClient) -> None:
    """Generating without an analysed project returns 404 (context not found)."""
    payload = {"name": "No Analysis", "description": DESCRIPTION}
    project_id = client.post("/api/v1/projects", json=payload).json()["id"]
    response = client.post(f"/api/v1/projects/{project_id}/srs/generate")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_context_not_found"


def test_generate_srs_missing_project_returns_404(client: TestClient) -> None:
    """Generating for a nonexistent project returns 404."""
    response = client.post("/api/v1/projects/00000000-0000-0000-0000-000000000000/srs/generate")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"


def test_generate_srs_invalid_state_returns_400(client: TestClient, app: FastAPI) -> None:
    """Generating for a project in a terminal state returns 400."""
    project_id = _create_analysed_project(client)
    database = app.state.database
    with database.session_factory() as session:
        project = session.get(models.Project, project_id)
        assert project is not None
        project.status = "exported"
        session.commit()

    response = client.post(f"/api/v1/projects/{project_id}/srs/generate")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_project_state"


def test_get_latest_srs_returns_generated_document(client: TestClient) -> None:
    """GET /projects/{id}/srs returns the latest generated SRS."""
    project_id = _create_analysed_project(client)
    _generate_srs(client, project_id)

    response = client.get(f"/api/v1/projects/{project_id}/srs")
    assert response.status_code == 200
    body = response.json()
    assert body["version_number"] == 1
    assert body["srs"]["metadata"]["project_name"] == "Campus Firewall"


def test_get_latest_srs_without_generation_returns_404(client: TestClient) -> None:
    """GET /srs on a project with no SRS returns 404."""
    project_id = _create_analysed_project(client)
    response = client.get(f"/api/v1/projects/{project_id}/srs")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "no_srs_version"


def test_version_history_is_preserved(client: TestClient) -> None:
    """Generating twice preserves history with incremented versions (FR-064)."""
    project_id = _create_analysed_project(client)
    first = _generate_srs(client, project_id)
    second = _generate_srs(client, project_id)

    assert first["version_number"] == 1
    assert second["version_number"] == 2
    assert first["version_id"] != second["version_id"]

    versions = client.get(f"/api/v1/projects/{project_id}/srs/versions").json()
    numbers = [v["version_number"] for v in versions["versions"]]
    assert numbers == [2, 1]


def test_regenerate_section_creates_new_version_and_preserves_other_sections(
    client: TestClient,
) -> None:
    """Section regeneration creates history instead of overwriting its source."""
    project_id = _create_analysed_project(client)
    first = _generate_srs(client, project_id)
    source = client.get(f"/api/v1/projects/{project_id}/srs/versions/{first['version_id']}").json()

    response = client.post(
        f"/api/v1/projects/{project_id}/srs/versions/{first['version_id']}/regenerate",
        json={"section": "security_requirements"},
    )
    assert response.status_code == 200
    regenerated = response.json()
    assert regenerated["id"] != first["version_id"]
    assert regenerated["version_number"] == 2
    assert regenerated["srs"]["functional_requirements"] == source["srs"]["functional_requirements"]
    assert regenerated["srs"]["metadata"]["version"] == 2


def test_get_specific_version(client: TestClient) -> None:
    """A specific version can be retrieved by ID."""
    project_id = _create_analysed_project(client)
    first = _generate_srs(client, project_id)
    second = _generate_srs(client, project_id)

    response = client.get(f"/api/v1/projects/{project_id}/srs/versions/{first['version_id']}")
    assert response.status_code == 200
    assert response.json()["version_number"] == 1

    first_content = response.json()["srs"]
    second_content = client.get(
        f"/api/v1/projects/{project_id}/srs/versions/{second['version_id']}"
    ).json()["srs"]
    assert first_content != second_content


def test_get_specific_version_missing_returns_404(client: TestClient) -> None:
    """Retrieving a missing version returns 404 scoped to the project."""
    project_id = _create_analysed_project(client)
    response = client.get(
        f"/api/v1/projects/{project_id}/srs/versions/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "srs_version_not_found"


def test_edit_srs_statement(client: TestClient) -> None:
    """A validated edit updates a requirement statement."""
    project_id = _create_analysed_project(client)
    generated = _generate_srs(client, project_id)

    response = client.put(
        f"/api/v1/projects/{project_id}/srs/versions/{generated['version_id']}",
        json={
            "updates": [
                {
                    "section": "functional_requirements",
                    "requirement_id": "FR-001",
                    "field": "statement",
                    "new_value": "The system shall filter all inbound traffic by default.",
                }
            ]
        },
    )
    assert response.status_code == 200
    updated = response.json()["srs"]
    assert (
        updated["functional_requirements"][0]["statement"]
        == "The system shall filter all inbound traffic by default."
    )

    fetched = client.get(
        f"/api/v1/projects/{project_id}/srs/versions/{generated['version_id']}"
    ).json()
    assert (
        fetched["srs"]["functional_requirements"][0]["statement"]
        == "The system shall filter all inbound traffic by default."
    )


def test_edit_srs_unknown_section_returns_400(client: TestClient) -> None:
    """Editing an unknown section returns 400."""
    project_id = _create_analysed_project(client)
    generated = _generate_srs(client, project_id)

    response = client.put(
        f"/api/v1/projects/{project_id}/srs/versions/{generated['version_id']}",
        json={
            "updates": [
                {
                    "section": "bogus_section",
                    "requirement_id": "FR-001",
                    "field": "statement",
                    "new_value": "Anything",
                }
            ]
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_srs_edit"


def test_edit_srs_unknown_requirement_returns_400(client: TestClient) -> None:
    """Editing a requirement that does not exist in the section returns 400."""
    project_id = _create_analysed_project(client)
    generated = _generate_srs(client, project_id)

    response = client.put(
        f"/api/v1/projects/{project_id}/srs/versions/{generated['version_id']}",
        json={
            "updates": [
                {
                    "section": "functional_requirements",
                    "requirement_id": "FR-999",
                    "field": "statement",
                    "new_value": "Anything",
                }
            ]
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_srs_edit"


def test_edit_srs_unknown_field_returns_400(client: TestClient) -> None:
    """Editing a non-requirement field returns 400."""
    project_id = _create_analysed_project(client)
    generated = _generate_srs(client, project_id)

    response = client.put(
        f"/api/v1/projects/{project_id}/srs/versions/{generated['version_id']}",
        json={
            "updates": [
                {
                    "section": "functional_requirements",
                    "requirement_id": "FR-001",
                    "field": "nonexistent_field",
                    "new_value": "Anything",
                }
            ]
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_srs_edit"


def test_edit_srs_duplicate_id_rejected(client: TestClient) -> None:
    """An edit that creates a duplicate requirement ID is rejected."""
    project_id = _create_analysed_project(client)
    generated = _generate_srs(client, project_id)

    response = client.put(
        f"/api/v1/projects/{project_id}/srs/versions/{generated['version_id']}",
        json={
            "updates": [
                {
                    "section": "non_functional_requirements",
                    "requirement_id": "NFR-001",
                    "field": "id",
                    "new_value": "FR-001",
                }
            ]
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_srs_edit"


def test_edit_srs_missing_version_returns_404(client: TestClient) -> None:
    """Editing a missing version returns 404."""
    project_id = _create_analysed_project(client)
    response = client.put(
        f"/api/v1/projects/{project_id}/srs/versions/00000000-0000-0000-0000-000000000000",
        json={
            "updates": [
                {
                    "section": "functional_requirements",
                    "requirement_id": "FR-001",
                    "field": "statement",
                    "new_value": "Anything",
                }
            ]
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "srs_version_not_found"


def test_validate_srs_returns_report_and_score(client: TestClient) -> None:
    """Deterministic validation returns a report and updates quality score."""
    project_id = _create_analysed_project(client)
    generated = _generate_srs(client, project_id)

    response = client.post(
        f"/api/v1/projects/{project_id}/srs/versions/{generated['version_id']}/validate"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["srs_version_id"] == generated["version_id"]
    assert isinstance(body["overall_score"], int)
    assert 0 <= body["overall_score"] <= 100
    assert body["overall_score"] >= 60


def test_validate_srs_detects_duplicate_ids(client: TestClient, app: FastAPI) -> None:
    """Validation flags duplicate requirement IDs (deterministic check)."""
    project_id = _create_analysed_project(client)
    generated = _generate_srs(client, project_id)

    database = app.state.database
    with database.session_factory() as session:
        version = session.get(models.SRSVersion, generated["version_id"])
        assert version is not None
        # Deep-copy and reassign the JSON attribute, then flag it modified so
        # SQLAlchemy persists the nested mutation.
        modified = copy.deepcopy(version.srs_json)
        modified["non_functional_requirements"][0]["id"] = "FR-001"
        version.srs_json = modified
        flag_modified(version, "srs_json")
        session.commit()

    response = client.post(
        f"/api/v1/projects/{project_id}/srs/versions/{generated['version_id']}/validate"
    )
    assert response.status_code == 200
    body = response.json()
    messages = [issue["message"] for issue in body["issues"]]
    assert any("Duplicate requirement ID" in message for message in messages)
    # A duplicate-ID error deducts points from the perfect score.
    assert body["overall_score"] < 100


def test_validate_srs_detects_missing_acceptance_criteria(client: TestClient, app: FastAPI) -> None:
    """Validation flags requirements missing acceptance criteria."""
    project_id = _create_analysed_project(client)
    generated = _generate_srs(client, project_id)

    database = app.state.database
    with database.session_factory() as session:
        version = session.get(models.SRSVersion, generated["version_id"])
        assert version is not None
        # Deep-copy and reassign the JSON attribute, then flag it modified so
        # SQLAlchemy persists the nested mutation.
        modified = copy.deepcopy(version.srs_json)
        modified["functional_requirements"][0]["acceptance_criteria"] = ""
        version.srs_json = modified
        flag_modified(version, "srs_json")
        session.commit()

    response = client.post(
        f"/api/v1/projects/{project_id}/srs/versions/{generated['version_id']}/validate"
    )
    assert response.status_code == 200
    messages = [issue["message"] for issue in response.json()["issues"]]
    assert any("acceptance criteria" in message for message in messages)


def test_validate_srs_missing_version_returns_404(client: TestClient) -> None:
    """Validating a missing version returns 404."""
    project_id = _create_analysed_project(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/srs/versions/00000000-0000-0000-0000-000000000000/validate"
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "srs_version_not_found"


def test_mock_generation_is_deterministic(client: TestClient) -> None:
    """Two SRS generations produce identical structural content (stable IDs,
    statements, architecture)."""
    project_id = _create_analysed_project(client)
    first = _generate_srs(client, project_id)
    second = _generate_srs(client, project_id)

    first_doc = client.get(
        f"/api/v1/projects/{project_id}/srs/versions/{first['version_id']}"
    ).json()["srs"]
    second_doc = client.get(
        f"/api/v1/projects/{project_id}/srs/versions/{second['version_id']}"
    ).json()["srs"]

    assert first_doc["metadata"]["version"] == 1
    assert second_doc["metadata"]["version"] == 2
    assert first_doc["functional_requirements"] == second_doc["functional_requirements"]
    assert first_doc["architecture_summary"] == second_doc["architecture_summary"]
