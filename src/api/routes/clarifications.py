"""Clarification API endpoints per API_CONTRACT.md §4 (Phase 1B)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.config import Settings
from ...llm.base import LLMProvider
from ...schemas.clarification import (
    ClarificationAnswerSubmission,
    ClarificationAnswerSubmissionResponse,
    ClarificationQuestionListResponse,
)
from ...services.clarification_service import ClarificationService
from ..dependencies import (
    enforce_request_body_size,
    get_app_settings,
    get_db,
    get_srs_llm_provider,
)

router = APIRouter(prefix="/projects", tags=["clarifications"])


def _clarification_service(
    db: Session, provider: LLMProvider, settings: Settings
) -> ClarificationService:
    """Construct a clarification service bound to the request session."""
    return ClarificationService(db, provider, settings)


@router.post(
    "/{project_id}/clarifications/generate",
    response_model=ClarificationQuestionListResponse,
)
def generate_clarification_questions(
    project_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> ClarificationQuestionListResponse:
    """Generate (or regenerate) clarification questions for a project."""
    return _clarification_service(db, provider, settings).generate_questions(project_id)


@router.get(
    "/{project_id}/clarifications",
    response_model=ClarificationQuestionListResponse,
)
def get_clarification_questions(
    project_id: str,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
) -> ClarificationQuestionListResponse:
    """Return generated clarification questions with any saved answers."""
    return _clarification_service(db, provider, settings).get_questions_for_project(project_id)


@router.post(
    "/{project_id}/clarifications",
    response_model=ClarificationAnswerSubmissionResponse,
)
def submit_clarification_answers(
    project_id: str,
    payload: ClarificationAnswerSubmission,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
    _: None = Depends(enforce_request_body_size),
) -> ClarificationAnswerSubmissionResponse:
    """Submit answers to clarification questions and update project context."""
    return _clarification_service(db, provider, settings).submit_answers(project_id, payload)
