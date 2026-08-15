"""Data-access operations for ProjectContext and clarification entities."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import (
    ClarificationAnswer,
    ClarificationQuestion,
    ProjectContext,
)


class ProjectContextRepository:
    """Persistence helpers for :class:`ProjectContext` and related queries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, context: ProjectContext) -> ProjectContext:
        """Persist a new project context and return it with timestamps."""
        self._session.add(context)
        self._session.flush()
        return context

    def get_latest_for_project(self, project_id: str) -> ProjectContext | None:
        """Return the most recently created context for a project, or None."""
        stmt = (
            select(ProjectContext)
            .where(ProjectContext.project_id == project_id)
            .order_by(ProjectContext.created_at.desc())
            .limit(1)
        )
        return self._session.scalars(stmt).first()


class ClarificationRepository:
    """Persistence helpers for clarification questions and answers."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # --- Questions ----------------------------------------------------

    def add_question(self, question: ClarificationQuestion) -> ClarificationQuestion:
        """Persist a clarification question."""
        self._session.add(question)
        self._session.flush()
        return question

    def delete_questions_for_project(self, project_id: str) -> None:
        """Delete all questions (and answers via cascade) for a project."""
        stmt = select(ClarificationQuestion).where(ClarificationQuestion.project_id == project_id)
        for question in self._session.scalars(stmt):
            self._session.delete(question)
        self._session.flush()

    def list_questions_for_project(self, project_id: str) -> list[ClarificationQuestion]:
        """Return all questions for a project ordered by display order."""
        stmt = (
            select(ClarificationQuestion)
            .where(ClarificationQuestion.project_id == project_id)
            .order_by(ClarificationQuestion.display_order.asc())
        )
        return list(self._session.scalars(stmt))

    def get_question(self, question_id: str, project_id: str) -> ClarificationQuestion | None:
        """Return a question by its stable ID (``q-001``) scoped to a project."""
        stmt = select(ClarificationQuestion).where(
            ClarificationQuestion.stable_id == question_id,
            ClarificationQuestion.project_id == project_id,
        )
        return self._session.scalars(stmt).first()

    # --- Answers ------------------------------------------------------

    def add_answer(self, answer: ClarificationAnswer) -> ClarificationAnswer:
        """Persist a clarification answer."""
        self._session.add(answer)
        self._session.flush()
        return answer
