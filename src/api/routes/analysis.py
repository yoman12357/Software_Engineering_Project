"""Analysis API endpoints per API_CONTRACT.md §3 (Phase 1B)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.config import Settings
from ...llm.base import LLMProvider
from ...schemas.analysis import (
    AnalysisResponse,
    ProjectContextRead,
)
from ...services.analysis_service import AnalysisService
from ..dependencies import get_app_settings, get_db, get_srs_llm_provider

router = APIRouter(prefix="/projects", tags=["analysis"])


def _analysis_service(
    db: Session, provider: LLMProvider, settings: Settings
) -> AnalysisService:
    """Construct an analysis service bound to the request session and provider."""
    return AnalysisService(db, provider, settings)


@router.post("/{project_id}/analyse", response_model=AnalysisResponse)
def analyse_project(
    project_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> AnalysisResponse:
    """Analyse the project's description and persist the ProjectContext."""
    return _analysis_service(db, provider, settings).analyse_project(project_id)


@router.get("/{project_id}/context", response_model=ProjectContextRead)
def get_project_context(
    project_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> ProjectContextRead:
    """Return the latest stored ProjectContext for the project."""
    context = _analysis_service(db, provider, settings).get_project_context(project_id)
    return ProjectContextRead.model_validate(context)
