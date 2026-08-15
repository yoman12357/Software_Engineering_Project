"""Persistence tests using a file-based SQLite database.

In-memory databases are wiped when the connection closes, so a temporary file
database is used to verify that data survives an application restart
(NFR-023).
"""

from pathlib import Path

from fastapi.testclient import TestClient

from src.core.config import Settings
from src.main import create_app


def test_project_persists_across_application_restart(tmp_path: Path) -> None:
    """A project created in one application run exists after a restart."""
    db_path = tmp_path / "test_persistence.db"
    database_url = f"sqlite:///{db_path}"

    # First run: create a project.
    settings = Settings(
        _env_file=None,
        env="testing",
        log_level="WARNING",
        database_url=database_url,
        llm_provider="mock",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/projects",
            json={"name": "Persistent Project", "description": "Survives a restart."},
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

    # The application (and its engine) has shut down; a fresh app instance is
    # created against the same database file.
    settings2 = Settings(
        _env_file=None,
        env="testing",
        log_level="WARNING",
        database_url=database_url,
        llm_provider="mock",
    )
    app2 = create_app(settings2)
    with TestClient(app2) as client2:
        get_response = client2.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 200
        body = get_response.json()
        assert body["name"] == "Persistent Project"
        assert body["description"] == "Survives a restart."
