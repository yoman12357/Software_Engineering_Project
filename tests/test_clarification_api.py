"""API tests for the clarification workflow (Phase 1B)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.db import models

DESCRIPTION = "I want to build a firewall and monitoring system for my college network."


def _create_analysed_project(client: TestClient) -> str:
    """Create a project, analyse it, and return its ID."""
    payload = {"name": "Campus Firewall", "description": DESCRIPTION}
    project_id = client.post("/api/v1/projects", json=payload).json()["id"]
    response = client.post(f"/api/v1/projects/{project_id}/analyse")
    assert response.status_code == 200
    return project_id


def test_generate_questions_returns_stable_ids(
    client: TestClient,
) -> None:
    """POST /clarifications/generate returns questions with stable IDs."""
    project_id = _create_analysed_project(client)

    response = client.post(f"/api/v1/projects/{project_id}/clarifications/generate")
    assert response.status_code == 200
    body = response.json()

    assert body["project_id"] == project_id
    ids = [q["id"] for q in body["questions"]]
    assert ids == ["q-001", "q-002", "q-003"]
    assert all(len(q["question_text"]) > 0 for q in body["questions"])
    assert all(len(q["reason"]) > 0 for q in body["questions"])
    assert all(q["target_gap"] for q in body["questions"])
    assert all(
        q["expected_answer_type"] in {"text", "number", "list", "boolean"}
        for q in body["questions"]
    )


def test_get_questions_returns_generated_questions(
    client: TestClient,
) -> None:
    """GET /clarifications returns the persisted questions."""
    project_id = _create_analysed_project(client)
    client.post(f"/api/v1/projects/{project_id}/clarifications/generate")

    response = client.get(f"/api/v1/projects/{project_id}/clarifications")
    assert response.status_code == 200
    body = response.json()
    assert len(body["questions"]) == 3
    assert body["questions"][0]["id"] == "q-001"
    assert body["questions"][0]["answer"] is None


def test_get_questions_without_generation_returns_404(
    client: TestClient,
) -> None:
    """GET /clarifications on an ungenerated project returns 404."""
    project_id = _create_analysed_project(client)
    response = client.get(f"/api/v1/projects/{project_id}/clarifications")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "no_clarification_questions"


def test_submit_answers_persists_and_updates_context(client: TestClient, app: FastAPI) -> None:
    """Submitting answers saves them and enriches the stored context."""
    project_id = _create_analysed_project(client)
    generated = client.post(f"/api/v1/projects/{project_id}/clarifications/generate").json()
    question_ids = [q["id"] for q in generated["questions"]]

    response = client.post(
        f"/api/v1/projects/{project_id}/clarifications",
        json={
            "answers": [
                {"question_id": question_ids[0], "answer_text": "500 nodes", "skipped": False},
                {"question_id": question_ids[1], "answer_text": "", "skipped": True},
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answers_saved"] == 2
    assert body["context_updated"] is True
    assert body["project_id"] == project_id

    # The project progressed to 'analysed' after answers were submitted.
    project = client.get(f"/api/v1/projects/{project_id}").json()
    assert project["status"] == "analysed"

    # The stored context was enriched.
    context = client.get(f"/api/v1/projects/{project_id}/context").json()
    assert context["enriched_context"] is not None
    answers = context["enriched_context"]["clarification_answers"]
    assert len(answers) == 2
    assert answers[0]["answer_text"] == "500 nodes"

    # The API returns the answers on the questions.
    questions = client.get(f"/api/v1/projects/{project_id}/clarifications").json()["questions"]
    assert questions[0]["answer"]["answer_text"] == "500 nodes"
    assert questions[1]["answer"]["skipped"] is True


def test_duplicate_answer_is_rejected(client: TestClient) -> None:
    """Submitting a second answer to the same question returns 400."""
    project_id = _create_analysed_project(client)
    generated = client.post(f"/api/v1/projects/{project_id}/clarifications/generate").json()
    question_id = generated["questions"][0]["id"]

    payload = {
        "answers": [{"question_id": question_id, "answer_text": "500 nodes", "skipped": False}]
    }
    first = client.post(f"/api/v1/projects/{project_id}/clarifications", json=payload)
    assert first.status_code == 200

    second = client.post(f"/api/v1/projects/{project_id}/clarifications", json=payload)
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "duplicate_clarification_answer"


def test_submit_answer_for_unknown_question_returns_404(
    client: TestClient,
) -> None:
    """Answering a question that does not belong to the project returns 404."""
    project_id = _create_analysed_project(client)
    client.post(f"/api/v1/projects/{project_id}/clarifications/generate")

    response = client.post(
        f"/api/v1/projects/{project_id}/clarifications",
        json={"answers": [{"question_id": "q-999", "answer_text": "N/A", "skipped": False}]},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "clarification_question_not_found"


def test_submit_non_skipped_empty_answer_is_rejected(client: TestClient) -> None:
    """A non-skipped answer with empty text is rejected (422)."""
    project_id = _create_analysed_project(client)
    generated = client.post(f"/api/v1/projects/{project_id}/clarifications/generate").json()
    question_id = generated["questions"][0]["id"]

    response = client.post(
        f"/api/v1/projects/{project_id}/clarifications",
        json={"answers": [{"question_id": question_id, "answer_text": "", "skipped": False}]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_multiple_projects_each_generate_q001_q003(client: TestClient) -> None:
    """Stable question IDs are scoped per-project (no global PK collision)."""
    first = _create_analysed_project(client)
    second = _create_analysed_project(client)

    first_questions = client.post(f"/api/v1/projects/{first}/clarifications/generate").json()[
        "questions"
    ]
    second_questions = client.post(f"/api/v1/projects/{second}/clarifications/generate").json()[
        "questions"
    ]

    assert [q["id"] for q in first_questions] == ["q-001", "q-002", "q-003"]
    assert [q["id"] for q in second_questions] == ["q-001", "q-002", "q-003"]

    # Answers can be submitted to both projects using the same stable IDs.
    payload = {
        "answers": [
            {"question_id": "q-001", "answer_text": "500 nodes", "skipped": False},
            {"question_id": "q-002", "answer_text": "", "skipped": True},
        ]
    }
    first_submit = client.post(f"/api/v1/projects/{first}/clarifications", json=payload)
    second_submit = client.post(f"/api/v1/projects/{second}/clarifications", json=payload)
    assert first_submit.status_code == 200
    assert second_submit.status_code == 200
    assert first_submit.json()["answers_saved"] == 2
    assert second_submit.json()["answers_saved"] == 2


def test_clarification_on_missing_project_returns_404(client: TestClient) -> None:
    """Clarification endpoints on a nonexistent project return 404."""
    missing = "00000000-0000-0000-0000-000000000000"
    generate = client.post(f"/api/v1/projects/{missing}/clarifications/generate")
    assert generate.status_code == 404
    assert generate.json()["error"]["code"] == "project_not_found"

    get = client.get(f"/api/v1/projects/{missing}/clarifications")
    assert get.status_code == 404
    assert get.json()["error"]["code"] == "project_not_found"

    submit = client.post(
        f"/api/v1/projects/{missing}/clarifications",
        json={"answers": [{"question_id": "q-001", "answer_text": "x", "skipped": False}]},
    )
    assert submit.status_code == 404
    assert submit.json()["error"]["code"] == "project_not_found"


def test_generate_questions_on_invalid_state_returns_400(client: TestClient, app: FastAPI) -> None:
    """Generating questions for a project in a terminal state returns 400."""
    project_id = _create_analysed_project(client)

    # Force the project into a state that does not allow clarification.
    database = app.state.database
    with database.session_factory() as session:
        project = session.get(models.Project, project_id)
        assert project is not None
        project.status = "exported"
        session.commit()

    response = client.post(f"/api/v1/projects/{project_id}/clarifications/generate")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_project_state"
