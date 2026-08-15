"""Project-description analysis pipeline (Phase 1B).

Orchestrates the deterministic mock LLM flow behind the :class:`LLMProvider`
abstraction: description analysis, subdomain inference, missing-information
detection, structured :class:`ProjectContext` persistence, and project-state
progression.
"""

from sqlalchemy.orm import Session

from ..core.config import Settings
from ..core.exceptions import (
    EmptyDescriptionError,
    InvalidGeneratedOutputError,
    InvalidProjectStateError,
    ProjectContextNotFoundError,
    ProjectNotFoundError,
)
from ..core.exceptions import LLMTimeoutError as ApiLLMTimeoutError
from ..db.models import ProjectContext
from ..llm.base import (
    LLMOutputError,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMTask,
    LLMTimeoutError,
)
from ..prompts.analysis import ANALYSIS_SYSTEM_PROMPT, ANALYSIS_USER_TEMPLATE
from ..repositories.context_repository import ProjectContextRepository
from ..repositories.project_repository import ProjectRepository
from ..schemas.analysis import (
    AnalysisResponse,
    ProjectAnalysis,
    ProjectContextCreate,
    utcnow_iso,
)
from ..schemas.project import generate_uuid
from .provenance_service import ModelRunRecorder

ANALYSABLE_STATES: frozenset[str] = frozenset({"draft", "analysed", "clarifying"})


class AnalysisService:
    """Use cases for description analysis and project-context retrieval."""

    def __init__(
        self,
        session: Session,
        provider: LLMProvider,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._provider = provider
        self._settings = settings or Settings()
        self._projects = ProjectRepository(session)
        self._contexts = ProjectContextRepository(session)
        self._model_runs = ModelRunRecorder(session, self._settings, provider)

    def analyse_project(self, project_id: str) -> AnalysisResponse:
        """Analyse a project's description and persist the resulting context.

        Args:
            project_id: The project to analyse.

        Returns:
            A validated analysis response.

        Raises:
            ProjectNotFoundError: If the project does not exist.
            EmptyDescriptionError: If the stored description is empty.
            InvalidProjectStateError: If the project status cannot be analysed.
            InvalidGeneratedOutputError: If the provider returns output that
                fails schema validation.
        """
        project = self._projects.get(project_id)
        if project is None:
            raise ProjectNotFoundError()

        description = project.description.strip()
        if not description:
            raise EmptyDescriptionError()

        if project.status not in ANALYSABLE_STATES:
            raise InvalidProjectStateError()

        model_run = self._model_runs.start(
            project.id,
            "project_analysis",
            prompt_template_version="analysis-v1",
        )
        try:
            request = LLMRequest(
                task=LLMTask.ANALYSIS,
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
                user_content=ANALYSIS_USER_TEMPLATE.format(description=description),
            )
            analysis = self._provider.generate_with_validation(request, ProjectAnalysis)

            context = ProjectContext(
                id=generate_uuid(),
                project_id=project.id,
                model_run_id=model_run.id,
                **ProjectContextCreate(
                    stakeholders=analysis.stakeholders,
                    assets=analysis.assets,
                    users=analysis.users,
                    constraints=analysis.constraints,
                    goals=analysis.goals,
                    inferred_categories=analysis.inferred_categories,
                    missing_information=analysis.missing_information,
                ).model_dump(),
            )
            self._contexts.add(context)

            project.inferred_categories = analysis.inferred_categories
            project.status = "clarifying" if analysis.missing_information else "analysed"
            self._projects.save(project)
            self._model_runs.succeed(
                model_run,
                artifact_type="project_context",
                artifact_ids=[context.id],
                deterministic_validation_applied=True,
                deterministic_repair_applied=False,
            )
        except Exception as exc:
            self._model_runs.fail(model_run, exc)
            raise

        self._session.refresh(context)
        self._session.refresh(project)

        return AnalysisResponse(
            project_id=project.id,
            analysis=analysis,
            has_missing_information=bool(analysis.missing_information),
            provider=self._provider.provider_name,
            model_name=self._provider.model_name,
            generated_at=utcnow_iso(),
        )

    def get_project_context(self, project_id: str) -> ProjectContext:
        """Return the latest stored context for a project.

        Raises:
            ProjectNotFoundError: If the project does not exist.
            ProjectContextNotFoundError: If the project has not been analysed.
        """
        if self._projects.get(project_id) is None:
            raise ProjectNotFoundError()
        context = self._contexts.get_latest_for_project(project_id)
        if context is None:
            raise ProjectContextNotFoundError()
        return context

    def _parse_analysis(self, response: LLMResponse) -> ProjectAnalysis:
        """Validate provider output against :class:`ProjectAnalysis`.

        Raises:
            InvalidGeneratedOutputError: On schema-validation failure.
        """
        try:
            return self._provider.parse_structured(response, ProjectAnalysis)
        except LLMTimeoutError as exc:
            raise ApiLLMTimeoutError(str(exc)) from exc
        except LLMOutputError as exc:
            raise InvalidGeneratedOutputError(str(exc)) from exc
