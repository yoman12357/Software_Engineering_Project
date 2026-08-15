"""Project CRUD endpoints per API_CONTRACT.md (Phase 1A subset).

The route layer performs no business logic; it parses requests, delegates to
the service, and serialises responses.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...schemas.project import (
    ProjectCreate,
    ProjectListItem,
    ProjectListResponse,
    ProjectRead,
    ProjectUpdate,
)
from ...services.project_service import ProjectService
from ..dependencies import enforce_request_body_size, get_db

router = APIRouter(prefix="/projects", tags=["projects"])


def _project_service(db: Session) -> ProjectService:
    """Construct a service instance bound to the request session."""
    return ProjectService(db)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_request_body_size),
) -> ProjectRead:
    """Create a new project from a name and informal description."""
    project = _project_service(db).create_project(payload)
    return ProjectRead.model_validate(project)


@router.get("", response_model=ProjectListResponse)
def list_projects(db: Session = Depends(get_db)) -> ProjectListResponse:
    """List all projects, newest first."""
    projects = _project_service(db).list_projects()
    items = [ProjectListItem.model_validate(p) for p in projects]
    return ProjectListResponse(projects=items, total=len(items))


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)) -> ProjectRead:
    """Return a single project by ID."""
    project = _project_service(db).get_project(project_id)
    return ProjectRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_request_body_size),
) -> ProjectRead:
    """Partially update a project's name and/or description."""
    project = _project_service(db).update_project(project_id, payload)
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)) -> None:
    """Delete a project and all associated data."""
    _project_service(db).delete_project(project_id)
