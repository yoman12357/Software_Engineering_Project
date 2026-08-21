"""Validated API representations for project reference documents."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectDocumentRead(BaseModel):
    """Safe project-document metadata returned to the browser."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    original_filename: str
    media_type: str
    file_extension: str
    file_size_bytes: int
    sha256: str
    status: str
    chunk_count: int
    created_at: datetime


class ProjectDocumentListResponse(BaseModel):
    """List of project documents with an explicit total."""

    documents: list[ProjectDocumentRead]
    total: int
