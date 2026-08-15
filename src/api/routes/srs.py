"""SRS API endpoints per API_CONTRACT.md §5 (Phase 1C)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.config import Settings
from ...llm.base import LLMProvider
from ...schemas.srs import (
    SRSEditRequest,
    SRSGenerationResponse,
    SRSValidationResponse,
    SRSVersionListResponse,
    SRSVersionRead,
)
from ...services.srs_generation_service import SRSGenerationService
from ..dependencies import (
    enforce_request_body_size,
    get_app_settings,
    get_db,
    get_llm_provider,
)

router = APIRouter(prefix="/projects", tags=["srs"])


def _srs_service(
    db: Session, provider: LLMProvider, settings: Settings
) -> SRSGenerationService:
    """Construct an SRS service bound to the request session and provider."""
    return SRSGenerationService(db, provider, settings)


@router.post("/{project_id}/srs/generate", response_model=SRSGenerationResponse)
def generate_srs(
    project_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> SRSGenerationResponse:
    """Generate a new SRS version for the project."""
    return _srs_service(db, provider, settings).generate_srs(
        project_id, use_rag=settings.rag_enabled
    )


@router.get("/{project_id}/srs", response_model=SRSVersionRead)
def get_latest_srs(
    project_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> SRSVersionRead:
    """Retrieve the latest SRS version for the project."""
    return _srs_service(db, provider, settings).get_latest_version(project_id)


@router.get("/{project_id}/srs/versions", response_model=SRSVersionListResponse)
def list_srs_versions(
    project_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> SRSVersionListResponse:
    """List all SRS versions for a project."""
    return _srs_service(db, provider, settings).list_versions(project_id)


@router.get("/{project_id}/srs/versions/{version_id}", response_model=SRSVersionRead)
def get_srs_version(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> SRSVersionRead:
    """Retrieve a specific SRS version for the project."""
    return _srs_service(db, provider, settings).get_version(project_id, version_id)


@router.put("/{project_id}/srs/versions/{version_id}", response_model=SRSVersionRead)
def edit_srs_version(
    project_id: str,
    version_id: str,
    payload: SRSEditRequest,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
    settings: Settings = Depends(get_app_settings),
    _: None = Depends(enforce_request_body_size),
) -> SRSVersionRead:
    """Apply validated user edits to an SRS version."""
    return _srs_service(db, provider, settings).edit_version(project_id, version_id, payload)


@router.post(
    "/{project_id}/srs/versions/{version_id}/validate",
    response_model=SRSValidationResponse,
)
def validate_srs_version(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> SRSValidationResponse:
    """Run deterministic validation on an SRS version."""
    return _srs_service(db, provider, settings).validate_version(project_id, version_id)
