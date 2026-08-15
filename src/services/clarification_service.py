"""Clarification-question workflow (Phase 1B).

Generates deterministic clarification questions from analysis gaps via the
:class:`LLMProvider` abstraction, persists them with stable IDs, accepts and
persists user answers (rejecting duplicates), and enriches the stored
:class:`ProjectContext` (USER_WORKFLOW Steps 6-8).
"""

from sqlalchemy.orm import Session

from ..core.config import Settings
from ..core.exceptions import (
    ClarificationQuestionNotFoundError,
    DuplicateClarificationAnswerError,
    InvalidGeneratedOutputError,
    InvalidProjectStateError,
    NoClarificationQuestionsError,
    ProjectContextNotFoundError,
    ProjectNotFoundError,
)
from ..core.exceptions import LLMTimeoutError as ApiLLMTimeoutError
from ..db.models import ClarificationAnswer, ClarificationQuestion
from ..llm.base import (
    LLMOutputError,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMTask,
    LLMTimeoutError,
)
from ..prompts.clarification import CLARIFICATION_SYSTEM_PROMPT, CLARIFICATION_USER_TEMPLATE
from ..repositories.context_repository import (
    ClarificationRepository,
    ProjectContextRepository,
)
from ..repositories.project_repository import ProjectRepository
from ..schemas.clarification import (
    ClarificationAnswerSubmission,
    ClarificationAnswerSubmissionResponse,
    ClarificationQuestionListResponse,
    ClarificationQuestionRead,
    ClarificationQuestionSet,
    generate_question_id,
)
from ..schemas.project import generate_uuid
from .provenance_service import ModelRunRecorder

QUESTIONABLE_STATES: frozenset[str] = frozenset({"analysed", "clarifying"})


class ClarificationService:
    """Use cases for the clarification-question workflow."""

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
        self._clarifications = ClarificationRepository(session)
        self._model_runs = ModelRunRecorder(session, self._settings, provider)

    def generate_questions(self, project_id: str) -> ClarificationQuestionListResponse:
        """Generate and persist clarification questions for a project.

        Questions are generated deterministically from the analysis gaps and
        persisted with stable IDs (``q-001``, ``q-002``, ...) so clients can
        submit answers referencing the returned IDs (USER_WORKFLOW Step 6).

        Raises:
            ProjectNotFoundError: If the project does not exist.
            ProjectContextNotFoundError: If the project has not been analysed.
            InvalidProjectStateError: If the project state is not analyzable.
            InvalidGeneratedOutputError: If the provider output is invalid.
        """
        project = self._projects.get(project_id)
        if project is None:
            raise ProjectNotFoundError()

        if project.status not in QUESTIONABLE_STATES:
            raise InvalidProjectStateError()

        context = self._contexts.get_latest_for_project(project_id)
        if context is None:
            raise ProjectContextNotFoundError()

        missing = context.missing_information or []
        if not missing:
            # Nothing to clarify; return an empty question list.
            return ClarificationQuestionListResponse(
                project_id=project_id,
                questions=[
                    ClarificationQuestionRead.model_validate(q)
                    for q in self._list_questions(project_id)
                ],
            )

        # Build context summary for the prompt
        project_summary = (
            f"A cybersecurity project: {project.description[:200]}..."
            if len(project.description) > 200
            else project.description
        )
        missing_str = "\n".join(f"- {gap}" for gap in missing)

        model_run = self._model_runs.start(
            project_id,
            "clarification_generation",
            prompt_template_version="clarification-v1",
        )
        try:
            request = LLMRequest(
                task=LLMTask.CLARIFICATION,
                system_prompt=CLARIFICATION_SYSTEM_PROMPT,
                user_content=CLARIFICATION_USER_TEMPLATE.format(
                    description=project.description,
                    project_summary=project_summary,
                    missing_information=missing_str,
                ),
            )
            question_set = self._provider.generate_with_validation(
                request, ClarificationQuestionSet
            )

            # Re-generation replaces the previous question set and answers.
            self._clarifications.delete_questions_for_project(project_id)
            self._session.flush()

            artifact_ids = []
            for index, draft in enumerate(question_set.questions):
                question = ClarificationQuestion(
                    id=generate_uuid(),
                    stable_id=generate_question_id(index + 1),
                    project_id=project_id,
                    question_text=draft.question_text,
                    reason=draft.reason,
                    is_critical=draft.is_critical,
                    display_order=index,
                    expected_answer_type=draft.expected_answer_type.value,
                    target_gap=draft.target_gap,
                    model_run_id=model_run.id,
                )
                self._clarifications.add_question(question)
                artifact_ids.append(question.id)

            self._model_runs.succeed(
                model_run,
                artifact_type="clarification_questions",
                artifact_ids=artifact_ids,
                deterministic_validation_applied=True,
                deterministic_repair_applied=False,
                metadata={"artifact_count": len(artifact_ids)},
            )
        except Exception as exc:
            self._model_runs.fail(model_run, exc)
            raise

        return self.get_questions_for_project(project_id)

    def get_questions_for_project(self, project_id: str) -> ClarificationQuestionListResponse:
        """Return all persisted clarification questions for a project.

        Raises:
            ProjectNotFoundError: If the project does not exist.
            NoClarificationQuestionsError: If no questions have been generated.
        """
        if self._projects.get(project_id) is None:
            raise ProjectNotFoundError()

        questions = self._clarifications.list_questions_for_project(project_id)
        if not questions:
            raise NoClarificationQuestionsError()

        return ClarificationQuestionListResponse(
            project_id=project_id,
            questions=[ClarificationQuestionRead.model_validate(q) for q in questions],
        )

    def submit_answers(
        self, project_id: str, submission: ClarificationAnswerSubmission
    ) -> ClarificationAnswerSubmissionResponse:
        """Persist answers for clarification questions without duplicates.

        Each answer is validated against the project's persisted questions
        (API_CONTRACT §4). Submitting a second answer to an already-answered
        question raises :class:`DuplicateClarificationAnswerError`. After
        answers are saved, the stored :class:`ProjectContext` is enriched with
        the answers and the project progresses from ``clarifying`` to
        ``analysed`` (USER_WORKFLOW Step 8).

        Raises:
            ProjectNotFoundError: If the project does not exist.
            ClarificationQuestionNotFoundError: If a submitted question ID is
                unknown for this project.
            DuplicateClarificationAnswerError: If a question already has an answer.
        """
        project = self._projects.get(project_id)
        if project is None:
            raise ProjectNotFoundError()

        for item in submission.answers:
            question = self._clarifications.get_question(item.question_id, project_id)
            if question is None:
                raise ClarificationQuestionNotFoundError()
            if question.answer is not None:
                raise DuplicateClarificationAnswerError()

        saved_count = 0
        for item in submission.answers:
            question = self._clarifications.get_question(item.question_id, project_id)
            # The validation loop above guarantees existence; mypy needs an
            # explicit guard to narrow the Optional type.
            if question is None:
                raise ClarificationQuestionNotFoundError()
            self._clarifications.add_answer(
                ClarificationAnswer(
                    id=generate_uuid(),
                    question_id=question.id,
                    answer_text=item.answer_text,
                    skipped=item.skipped,
                )
            )
            saved_count += 1

        # Expire ORM objects so the (previously loaded) question.answers
        # relationship reflects the newly persisted answers before enriching
        # the stored context.
        self._session.flush()
        self._session.expire_all()
        context_updated = self._enrich_context(project_id)
        project.status = "analysed"
        self._projects.save(project)
        self._session.commit()

        return ClarificationAnswerSubmissionResponse(
            project_id=project_id,
            answers_saved=saved_count,
            context_updated=context_updated,
        )

    # --- Internal helpers ---------------------------------------------

    def _enrich_context(self, project_id: str) -> bool:
        """Merge answered clarification questions into the stored context.

        Returns:
            True if a context was found and enriched; False otherwise.
        """
        context = self._contexts.get_latest_for_project(project_id)
        if context is None:
            return False

        questions = self._clarifications.list_questions_for_project(project_id)
        answers = []
        for question in questions:
            if question.answer is not None:
                answers.append(
                    {
                        "question_id": question.stable_id,
                        "question_text": question.question_text,
                        "answer_text": question.answer.answer_text,
                        "skipped": question.answer.skipped,
                    }
                )

        latest_answer_at = max(
            (q.answer.created_at for q in questions if q.answer is not None),
            default=None,
        )
        answered_at_iso = latest_answer_at.isoformat() if latest_answer_at is not None else None
        existing = context.enriched_context or {}
        enriched = {
            **existing,
            "clarification_answers": answers,
            "answered_at": answered_at_iso,
        }
        context.enriched_context = enriched
        return True

    def _parse_question_set(self, response: LLMResponse) -> ClarificationQuestionSet:
        """Validate provider output against :class:`ClarificationQuestionSet`.

        Raises:
            InvalidGeneratedOutputError: On schema-validation failure.
        """
        try:
            return self._provider.parse_structured(response, ClarificationQuestionSet)
        except LLMTimeoutError as exc:
            raise ApiLLMTimeoutError(str(exc)) from exc
        except LLMOutputError as exc:
            raise InvalidGeneratedOutputError(str(exc)) from exc

    def _list_questions(self, project_id: str) -> list[ClarificationQuestion]:
        """Return the persisted questions for a project (may be empty)."""
        return self._clarifications.list_questions_for_project(project_id)
