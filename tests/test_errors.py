"""Tests for the centralised error-envelope behaviour (SEC-046)."""

from fastapi.testclient import TestClient


def test_validation_errors_use_standard_envelope(client: TestClient) -> None:
    """A malformed request body returns the documented 422 envelope."""
    response = client.post("/api/v1/projects", json={"name": ""})
    assert response.status_code == 422
    body = response.json()
    assert set(body["error"].keys()) == {"code", "message", "details"}
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["error"]["details"], dict)


def test_404_errors_use_standard_envelope(client: TestClient) -> None:
    """Not-found responses use the standard envelope with a stable code."""
    response = client.get("/api/v1/projects/bogus-id")
    assert response.status_code == 404
    body = response.json()
    assert set(body["error"].keys()) == {"code", "message", "details"}
    assert body["error"]["code"] == "project_not_found"
    assert body["error"]["details"] == {}


def test_error_messages_do_not_leak_internal_details(client: TestClient) -> None:
    """Error bodies must not contain stack traces, paths, or SQL fragments."""
    response = client.get("/api/v1/projects/bogus-id")
    serialized = response.text.lower()
    assert "traceback" not in serialized
    assert "select" not in serialized
    assert "sqlite" not in serialized
    assert "cybersrs.db" not in serialized
    assert ".env" not in serialized
