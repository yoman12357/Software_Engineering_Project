"""Tests for the health endpoint."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """The health endpoint reports a healthy API with a working database."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "cybersrs-api"
    assert body["database_ok"] is True


def test_openapi_documentation_loads(client: TestClient) -> None:
    """Swagger/OpenAPI JSON is generated automatically."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    body = response.json()
    assert body["info"]["title"] == "CyberSRS API"
    assert "/api/v1/health" in body["paths"]
    assert "/api/v1/projects" in body["paths"]
