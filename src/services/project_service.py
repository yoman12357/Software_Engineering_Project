"""Business logic for the Project resource.

The service depends on :class:`ProjectRepository` and :class:`Session`; it
owns domain rules (ID generation, not-found handling) while the repository
only persists data. A single transaction is committed per operation by the
caller-visible method.
"""

from sqlalchemy.orm import Session

from ..core.config import Settings, get_settings
from ..core.exceptions import ProjectLimitError, ProjectNotFoundError
from ..db.models import Project
from ..repositories.project_repository import ProjectRepository
from ..schemas.project import ProjectCreate, ProjectUpdate, generate_uuid


class ProjectService:
    """Operations that implement the project-management use cases."""

    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._repository = ProjectRepository(session)
        self._settings = settings or get_settings()

    def create_project(self, data: ProjectCreate) -> Project:
        """Create and persist a new project.

        Raises:
            ProjectLimitError: If max_projects limit (SEC-041) is reached.
        """
        if self._settings.max_projects > 0:
            current_count = len(self._repository.list_all())
            if current_count >= self._settings.max_projects:
                raise ProjectLimitError(
                    f"Maximum project limit ({self._settings.max_projects}) reached. "
                    "Delete an existing project from the Dashboard and try again."
                )

        project = Project(
            id=generate_uuid(),
            name=data.name,
            description=data.description,
            status="draft",
        )
        self._repository.add(project)
        self._session.commit()
        self._session.refresh(project)
        return project

    def get_project(self, project_id: str) -> Project:
        """Return a project by ID or raise :class:`ProjectNotFoundError`."""
        project = self._repository.get(project_id)
        if project is None:
            raise ProjectNotFoundError()
        return project

    def list_projects(self) -> list[Project]:
        """Return all projects, newest first."""
        return self._repository.list_all()

    def update_project(self, project_id: str, data: ProjectUpdate) -> Project:
        """Partially update a project's name and/or description.

        Raises:
            ProjectNotFoundError: If no project has the given ID.
        """
        project = self.get_project(project_id)
        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description
        self._repository.save(project)
        self._session.commit()
        self._session.refresh(project)
        return project

    def delete_project(self, project_id: str) -> None:
        """Delete a project by ID.

        Raises:
            ProjectNotFoundError: If no project has the given ID.
        """
        project = self.get_project(project_id)
        self._repository.delete(project)
        self._session.commit()
