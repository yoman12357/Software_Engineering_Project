"""Data-access operations for the Project entity."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Project


class ProjectRepository:
    """Persistence helpers for :class:`Project`.

    The repository is deliberately thin: it performs simple CRUD against the
    database and raises no domain exceptions. Domain rules live in the service
    layer. This keeps the repository reusable and testable.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, project: Project) -> Project:
        """Persist a new project and return it with its generated timestamps."""
        self._session.add(project)
        self._session.flush()
        return project

    def get(self, project_id: str) -> Project | None:
        """Return the project with the given ID, or None."""
        return self._session.get(Project, project_id)

    def list_all(self) -> list[Project]:
        """Return all projects ordered by creation time (newest first)."""
        stmt = select(Project).order_by(Project.created_at.desc())
        return list(self._session.scalars(stmt))

    def delete(self, project: Project) -> None:
        """Delete the given project from the database."""
        self._session.delete(project)
        self._session.flush()

    def save(self, project: Project) -> Project:
        """Persist changes made to an existing project."""
        self._session.flush()
        return project
