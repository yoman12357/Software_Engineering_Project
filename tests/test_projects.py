"""API tests for the Project CRUD endpoints."""

from fastapi.testclient import TestClient

from src.core.config import Settings
from src.main import create_app


def test_create_project(client: TestClient, sample_project_payload: dict) -> None:
    """A valid project is created with 201 and persisted fields."""
    response = client.post("/api/v1/projects", json=sample_project_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == sample_project_payload["name"]
    assert body["description"] == sample_project_payload["description"]
    assert body["status"] == "draft"
    assert body["id"]
    assert "created_at" in body
    assert "updated_at" in body


def test_create_project_returns_conflict_when_project_limit_is_reached() -> None:
    """The configured project cap produces an actionable error instead of HTTP 500."""
    settings = Settings(
        _env_file=None,
        env="testing",
        log_level="WARNING",
        database_url="sqlite:///:memory:",
        llm_provider="mock",
        max_projects=1,
    )
    application = create_app(settings)
    payload = {
        "name": "Campus Firewall",
        "description": "A firewall and network monitoring system for a college campus.",
    }

    with TestClient(application) as limited_client:
        assert limited_client.post("/api/v1/projects", json=payload).status_code == 201
        response = limited_client.post(
            "/api/v1/projects",
            json={**payload, "name": "Second Project"},
        )

    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "project_limit_reached",
        "message": (
            "Maximum project limit (1) reached. "
            "Delete an existing project from the Dashboard and try again."
        ),
        "details": {},
    }


def test_create_project_trims_whitespace(client: TestClient) -> None:
    """Whitespace around name and description is stripped on creation."""
    response = client.post(
        "/api/v1/projects",
        json={"name": "  Campus IDS  ", "description": "  An IDS for the campus.  "},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Campus IDS"
    assert body["description"] == "An IDS for the campus."


def test_create_project_rejects_empty_description(client: TestClient) -> None:
    """A whitespace-only description is rejected (422, structured error)."""
    response = client.post("/api/v1/projects", json={"name": "Bad", "description": "   "})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "description" in body["error"]["details"]


def test_create_project_rejects_short_description(client: TestClient) -> None:
    """A description shorter than 10 characters is rejected (API_CONTRACT)."""
    response = client.post("/api/v1/projects", json={"name": "Short", "description": "Brief."})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_project_rejects_missing_description(client: TestClient) -> None:
    """A request without a description is rejected with 422."""
    response = client.post("/api/v1/projects", json={"name": "No Description"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_project_rejects_empty_name(client: TestClient) -> None:
    """A missing or blank name is rejected with 422."""
    response = client.post(
        "/api/v1/projects", json={"name": "", "description": "Something useful here."}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_project_rejects_oversized_name(client: TestClient) -> None:
    """A name longer than 200 characters is rejected (SEC-010)."""
    response = client.post(
        "/api/v1/projects",
        json={"name": "x" * 201, "description": "A valid description."},
    )
    assert response.status_code == 422


def test_create_project_rejects_unknown_extra_field(client: TestClient) -> None:
    """Unrecognised fields are rejected rather than silently ignored."""
    response = client.post(
        "/api/v1/projects",
        json={"name": "X", "description": "A valid description.", "malicious": "ignored"},
    )
    assert response.status_code == 422


def test_list_projects_empty(client: TestClient) -> None:
    """The project list is empty on a fresh database."""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["projects"] == []


def test_list_projects_returns_created_projects(
    client: TestClient, sample_project_payload: dict
) -> None:
    """Created projects appear in the list."""
    client.post("/api/v1/projects", json=sample_project_payload)
    client.post(
        "/api/v1/projects",
        json={"name": "API Gateway", "description": "A secure API gateway."},
    )
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    names = {item["name"] for item in body["projects"]}
    assert names == {"Campus Firewall", "API Gateway"}


def test_get_project(client: TestClient, sample_project_payload: dict) -> None:
    """A created project can be retrieved by ID."""
    created = client.post("/api/v1/projects", json=sample_project_payload).json()
    response = client.get(f"/api/v1/projects/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["description"] == sample_project_payload["description"]


def test_get_nonexistent_project_returns_404(client: TestClient) -> None:
    """A missing project returns the standard 404 error envelope."""
    response = client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "project_not_found"


def test_get_project_with_malformed_id_returns_404(client: TestClient) -> None:
    """A syntactically invalid ID is treated as 'not found', not a crash."""
    response = client.get("/api/v1/projects/not-a-valid-id")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"


def test_update_project_name(client: TestClient, sample_project_payload: dict) -> None:
    """A project name can be updated with PATCH."""
    created = client.post("/api/v1/projects", json=sample_project_payload).json()
    response = client.patch(f"/api/v1/projects/{created['id']}", json={"name": "Renamed Firewall"})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed Firewall"
    assert body["description"] == sample_project_payload["description"]


def test_update_project_description(client: TestClient, sample_project_payload: dict) -> None:
    """A project description can be updated with PATCH."""
    created = client.post("/api/v1/projects", json=sample_project_payload).json()
    new_description = "Updated description with more detail about scaling."
    response = client.patch(
        f"/api/v1/projects/{created['id']}", json={"description": new_description}
    )
    assert response.status_code == 200
    assert response.json()["description"] == new_description


def test_update_project_rejects_blank_description(
    client: TestClient, sample_project_payload: dict
) -> None:
    """A blank description in PATCH is rejected."""
    created = client.post("/api/v1/projects", json=sample_project_payload).json()
    response = client.patch(f"/api/v1/projects/{created['id']}", json={"description": "   "})
    assert response.status_code == 422


def test_update_project_rejects_empty_body(
    client: TestClient, sample_project_payload: dict
) -> None:
    """A PATCH with no fields is rejected with 422."""
    created = client.post("/api/v1/projects", json=sample_project_payload).json()
    response = client.patch(f"/api/v1/projects/{created['id']}", json={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_update_nonexistent_project_returns_404(client: TestClient) -> None:
    """PATCH on a missing project returns 404."""
    response = client.patch(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000",
        json={"name": "Ghost"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"


def test_delete_project(client: TestClient, sample_project_payload: dict) -> None:
    """A project can be deleted and is then not retrievable."""
    created = client.post("/api/v1/projects", json=sample_project_payload).json()
    response = client.delete(f"/api/v1/projects/{created['id']}")
    assert response.status_code == 204

    # The project is gone.
    get_response = client.get(f"/api/v1/projects/{created['id']}")
    assert get_response.status_code == 404


def test_delete_nonexistent_project_returns_404(client: TestClient) -> None:
    """DELETE on a missing project returns 404."""
    response = client.delete("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"
