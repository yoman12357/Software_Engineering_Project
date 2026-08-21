"""API coverage for secure project-scoped reference documents."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.core.config import Settings
from src.llm.base import LLMRequest, LLMResponse
from src.llm.mock_provider import MockLLMProvider
from src.main import create_app


class RecordingMockProvider(MockLLMProvider):
    """Mock provider that records the most recent validated request."""

    last_request: LLMRequest | None = None

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Record the request and delegate to the deterministic mock."""
        self.last_request = request
        return super().generate(request)


@pytest.fixture
def document_client(tmp_path: Path) -> Iterator[TestClient]:
    """Yield an isolated client whose uploads use a temporary directory."""
    settings = Settings(
        _env_file=None,
        env="testing",
        log_level="WARNING",
        database_url="sqlite:///:memory:",
        llm_provider="mock",
        rag_enabled=False,
        upload_dir=str(tmp_path / "uploads"),
        max_upload_bytes=128,
        max_project_documents=2,
    )
    with TestClient(create_app(settings)) as client:
        yield client


def _project_id(client: TestClient) -> str:
    response = client.post(
        "/api/v1/projects",
        json={"name": "Reference test", "description": "A secure network reference project."},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_upload_list_and_delete_text_document(
    document_client: TestClient, tmp_path: Path
) -> None:
    """A supported document is stored safely, listed, and fully deleted."""
    project_id = _project_id(document_client)
    response = document_client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={
            "file": (
                "requirements.txt",
                b"Require MFA and encrypted audit logs.",
                "text/plain",
            )
        },
    )
    assert response.status_code == 201
    document = response.json()
    assert document["original_filename"] == "requirements.txt"
    assert "stored_path" not in document
    assert "extracted_text" not in document
    stored_files = list((tmp_path / "uploads" / project_id).iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].name != "requirements.txt"

    listed = document_client.get(f"/api/v1/projects/{project_id}/documents")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    deleted = document_client.delete(
        f"/api/v1/projects/{project_id}/documents/{document['id']}"
    )
    assert deleted.status_code == 204
    assert not stored_files[0].exists()


def test_upload_rejects_unsupported_and_oversized_documents(
    document_client: TestClient,
) -> None:
    """Extension and byte limits are deterministically enforced."""
    project_id = _project_id(document_client)
    unsupported = document_client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("program.exe", b"MZ executable", "application/x-msdownload")},
    )
    assert unsupported.status_code == 415
    oversized = document_client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("large.txt", b"x" * 129, "text/plain")},
    )
    assert oversized.status_code == 413


def test_project_deletion_removes_uploaded_file(
    document_client: TestClient, tmp_path: Path
) -> None:
    """Deleting a project also removes its generated upload files."""
    project_id = _project_id(document_client)
    uploaded = document_client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("scope.md", b"# Scope\nRequire device identity checks.", "text/markdown")},
    )
    assert uploaded.status_code == 201
    project_dir = tmp_path / "uploads" / project_id
    assert list(project_dir.iterdir())
    assert document_client.delete(f"/api/v1/projects/{project_id}").status_code == 204
    assert not list(project_dir.iterdir())


def test_uploaded_text_is_included_in_project_analysis(document_client: TestClient) -> None:
    """Uploaded project content reaches the analysis prompt before questions are generated."""
    project_id = _project_id(document_client)
    uploaded = document_client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={
            "file": (
                "constraints.txt",
                b"Reference constraint: retain audit events for 365 days.",
                "text/plain",
            )
        },
    )
    assert uploaded.status_code == 201
    provider = RecordingMockProvider()
    document_client.app.state.srs_llm_provider = provider
    analysed = document_client.post(f"/api/v1/projects/{project_id}/analyse")
    assert analysed.status_code == 200
    assert provider.last_request is not None
    assert "retain audit events for 365 days" in provider.last_request.user_content
