"""Data-access operations for project-scoped reference documents."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import ProjectDocument


class ProjectDocumentRepository:
    """Persistence helpers for :class:`ProjectDocument`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, document: ProjectDocument) -> ProjectDocument:
        """Persist a project document."""
        self._session.add(document)
        self._session.flush()
        return document

    def get(self, project_id: str, document_id: str) -> ProjectDocument | None:
        """Return one document only when it belongs to the project."""
        statement = select(ProjectDocument).where(
            ProjectDocument.id == document_id,
            ProjectDocument.project_id == project_id,
        )
        return self._session.scalar(statement)

    def list_for_project(self, project_id: str) -> list[ProjectDocument]:
        """Return project documents in upload order."""
        statement = (
            select(ProjectDocument)
            .where(ProjectDocument.project_id == project_id)
            .order_by(ProjectDocument.created_at.asc())
        )
        return list(self._session.scalars(statement))

    def delete(self, document: ProjectDocument) -> None:
        """Delete a project document record."""
        self._session.delete(document)
        self._session.flush()
