"""Integration tests for SQLite-backed chat-session persistence."""

from fastapi.testclient import TestClient


def _payload(
    project_id: str | None = None,
    name: str = "Architecture chat",
    message_prefix: str = "first",
) -> dict:
    """Return a valid complete chat-session snapshot."""
    return {
        "project_id": project_id,
        "name": name,
        "messages": [
            {
                "id": f"{message_prefix}-message-1",
                "role": "user",
                "content": "Explain zero trust.",
                "type": "text",
                "metadata": None,
                "timestamp": "2026-08-21T06:00:00Z",
            },
            {
                "id": f"{message_prefix}-message-2",
                "role": "assistant",
                "content": "Zero trust continuously verifies access.",
                "type": "text",
                "metadata": {"ragEnabled": False},
                "timestamp": "2026-08-21T06:00:01Z",
            },
        ],
        "stage": "welcome",
        "analysis": None,
        "clarification_questions": None,
        "srs": None,
        "srs_version_id": None,
        "pending_project_description": None,
    }


def test_chat_session_crud_and_pin_order(client: TestClient) -> None:
    """A session round-trips, updates, lists, and deletes through SQLite."""
    first = client.put("/api/v1/chat/sessions/chat-1", json=_payload())
    assert first.status_code == 200
    assert first.json()["messages"][1]["metadata"] == {"ragEnabled": False}

    second = client.put(
        "/api/v1/chat/sessions/chat-2",
        json=_payload(name="Pinned chat", message_prefix="second"),
    )
    assert second.status_code == 200
    updated = client.patch(
        "/api/v1/chat/sessions/chat-2",
        json={"name": "Important chat", "pinned": True},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Important chat"
    assert updated.json()["pinned_at"] is not None

    listing = client.get("/api/v1/chat/sessions")
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["sessions"]] == ["chat-2", "chat-1"]

    restored = client.get("/api/v1/chat/sessions/chat-1")
    assert restored.status_code == 200
    assert [item["id"] for item in restored.json()["messages"]] == [
        "first-message-1",
        "first-message-2",
    ]

    assert client.delete("/api/v1/chat/sessions/chat-1").status_code == 204
    missing = client.get("/api/v1/chat/sessions/chat-1")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "chat_session_not_found"


def test_project_delete_cascades_to_chat_sessions(
    client: TestClient,
    sample_project_payload: dict,
) -> None:
    """Deleting a project removes its associated conversation history."""
    project = client.post("/api/v1/projects", json=sample_project_payload).json()
    saved = client.put(
        "/api/v1/chat/sessions/project-chat",
        json=_payload(project_id=project["id"]),
    )
    assert saved.status_code == 200

    assert client.delete(f"/api/v1/projects/{project['id']}").status_code == 204
    assert client.get("/api/v1/chat/sessions/project-chat").status_code == 404
