"""Read-only model and artifact provenance endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.config import Settings
from ...llm.base import LLMProvider
from ...schemas.provenance import ArtifactProvenanceResponse, ModelInfoResponse
from ...services.provenance_service import ProvenanceQueryService
from ..dependencies import get_app_settings, get_db, get_srs_llm_provider

router = APIRouter(tags=["provenance"])


@router.get("/system/model-info", response_model=ModelInfoResponse)
def get_model_info(
    settings: Settings = Depends(get_app_settings),
    provider: LLMProvider = Depends(get_srs_llm_provider),
) -> ModelInfoResponse:
    """Return allow-listed active model and RAG information."""
    return ProvenanceQueryService.model_info(settings, provider)


@router.get(
    "/projects/{project_id}/srs/versions/{version_id}/provenance",
    response_model=ArtifactProvenanceResponse,
)
def get_srs_provenance(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
) -> ArtifactProvenanceResponse:
    """Return the model run associated with an SRS version."""
    return ProvenanceQueryService(db).get_srs_provenance(project_id, version_id)
