"""Pydantic schemas for clarification questions and answers (Phase 1B).

Questions carry stable string IDs (``q-...``) so clients can submit answers by
referencing the ID returned by the API. The schema supports the fields planned
in PROMPT_AND_OUTPUT_DESIGN §2.4 and USER_WORKFLOW §6: question text, reason,
expected answer type, required (critical) status, and the target gap.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class AnswerType(StrEnum):
    """Supported free-text answer types for clarification questions."""

    TEXT = "text"
    NUMBER = "number"
    LIST = "list"
    BOOLEAN = "boolean"


class ClarificationQuestionDraft(BaseModel):
    """A generated clarification question before persistence (output of the
    clarification-generation task, PROMPT_AND_OUTPUT_DESIGN §2.4)."""

    model_config = ConfigDict(extra="forbid")

    question_text: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    is_critical: bool = False
    target_gap: str = Field(min_length=1)
    expected_answer_type: AnswerType = AnswerType.TEXT

    @model_validator(mode="before")
    @classmethod
    def repair_target_gap_key(cls, data: Any) -> Any:
        """Repair one unambiguous localized/corrupted target-gap field name."""
        if not isinstance(data, dict) or "target_gap" in data:
            return data
        candidates = [
            key
            for key in data
            if isinstance(key, str)
            and key.startswith("target")
            and key not in {"target_gap"}
        ]
        if len(candidates) != 1:
            return data
        repaired = dict(data)
        repaired["target_gap"] = repaired.pop(candidates[0])
        logger.warning("Repaired an unambiguous malformed target_gap field name")
        return repaired


class ClarificationQuestionSet(BaseModel):
    """Structured output of the clarification-generation LLM task."""

    model_config = ConfigDict(extra="forbid")

    questions: list[ClarificationQuestionDraft] = Field(min_length=1)


class ClarificationAnswerItem(BaseModel):
    """API request item: one answer submitted for a question."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    answer_text: str = ""
    skipped: bool = False

    @field_validator("answer_text", "question_id")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        """Strip surrounding whitespace from user-supplied text."""
        return value.strip()

    @model_validator(mode="after")
    def require_text_when_not_skipped(self) -> ClarificationAnswerItem:
        """A non-skipped answer must not be empty (API_CONTRACT §4)."""
        if not self.skipped and not self.answer_text:
            raise ValueError("answer_text must not be empty when skipped is false")
        return self


class ClarificationAnswerSubmission(BaseModel):
    """Request body for submitting one or more clarification answers."""

    model_config = ConfigDict(extra="forbid")

    answers: list[ClarificationAnswerItem] = Field(min_length=1)


class ClarificationAnswerRead(BaseModel):
    """API representation of one stored answer."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    question_id: str
    answer_text: str
    skipped: bool
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def use_stable_question_id(cls, data: Any) -> Any:
        """Expose the stable question ID (``q-001``) as ``question_id``."""
        if hasattr(data, "api_question_id"):
            return {
                "id": data.id,
                "question_id": data.api_question_id,
                "answer_text": data.answer_text,
                "skipped": data.skipped,
                "created_at": data.created_at,
            }
        return data


class ClarificationQuestionRead(BaseModel):
    """API representation of a clarification question with its answer."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    question_text: str
    reason: str
    is_critical: bool
    display_order: int
    expected_answer_type: str = "text"
    target_gap: str
    created_at: datetime
    answer: ClarificationAnswerRead | None = None

    @model_validator(mode="before")
    @classmethod
    def use_stable_id(cls, data: Any) -> Any:
        """Expose the stable question ID (``q-001``) as the API ``id``."""
        if hasattr(data, "stable_id"):
            return {
                "id": data.stable_id,
                "project_id": data.project_id,
                "question_text": data.question_text,
                "reason": data.reason,
                "is_critical": data.is_critical,
                "display_order": data.display_order,
                "expected_answer_type": data.expected_answer_type,
                "target_gap": data.target_gap,
                "created_at": data.created_at,
                "answer": data.answer,
            }
        return data


class ClarificationQuestionListResponse(BaseModel):
    """Response body for ``GET /projects/{id}/clarifications``."""

    project_id: str
    questions: list[ClarificationQuestionRead]


class ClarificationAnswerSubmissionResponse(BaseModel):
    """Response body for ``POST /projects/{id}/clarifications``."""

    project_id: str
    answers_saved: int
    context_updated: bool


def generate_question_id(index: int) -> str:
    """Return a stable, human-readable question ID for the given order index.

    IDs are deterministic across generations for the same project flow
    (USER_WORKFLOW requires stable IDs).
    """
    return f"q-{index:03d}"
