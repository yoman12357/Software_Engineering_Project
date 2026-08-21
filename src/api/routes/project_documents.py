"""Project reference-document endpoints documented in API_CONTRACT.md."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from ...core.config import Settings
from ...core.exceptions import ProjectDocumentLimitError
from ...schemas.project_document import ProjectDocumentListResponse, ProjectDocumentRead
from ...services.project_document_service import ProjectDocumentService
from ..dependencies import get_app_settings, get_db

router = APIRouter(prefix="/projects", tags=["project-documents"])


@router.post(
    "/{project_id}/documents",
    response_model=ProjectDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_project_document(
    project_id: str,
    file: Annotated[UploadFile, File()],
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProjectDocumentRead:
    """Upload one bounded project reference document."""
    content = await file.read(settings.max_upload_bytes + 1)
    await file.close()
    if len(content) > settings.max_upload_bytes:
        raise ProjectDocumentLimitError("The uploaded file exceeds the size limit.")
    document = ProjectDocumentService(db, settings).upload(
        project_id,
        file.filename or "",
        content,
        file.content_type,
    )
    return ProjectDocumentRead.model_validate(document)


@router.get("/{project_id}/documents", response_model=ProjectDocumentListResponse)
def list_project_documents(
    project_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ProjectDocumentListResponse:
    """List safe metadata for a project's uploaded documents."""
    documents = ProjectDocumentService(db, settings).list_for_project(project_id)
    return ProjectDocumentListResponse(
        documents=[ProjectDocumentRead.model_validate(item) for item in documents],
        total=len(documents),
    )


@router.delete(
    "/{project_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_project_document(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> None:
    """Delete a project document and its locally derived artefacts."""
    ProjectDocumentService(db, settings).delete(project_id, document_id)
