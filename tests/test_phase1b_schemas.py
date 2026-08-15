"""Schema validation tests for Phase 1B analysis and clarification models."""

import pytest
from pydantic import ValidationError

from src.schemas.analysis import ProjectAnalysis
from src.schemas.clarification import (
    ClarificationAnswerItem,
    ClarificationAnswerSubmission,
    ClarificationQuestionSet,
)

VALID_ANALYSIS = {
    "stakeholders": ["IT"],
    "assets": ["Network"],
    "users": ["Admins"],
    "constraints": ["Budget"],
    "goals": ["Secure"],
    "inferred_categories": ["CAT-02"],
    "missing_information": ["Scale"],
    "project_summary": "A firewall system.",
}


def test_valid_project_analysis_passes() -> None:
    """A well-formed analysis validates and preserves its values."""
    analysis = ProjectAnalysis.model_validate(VALID_ANALYSIS)
    assert analysis.inferred_categories == ["CAT-02"]
    assert analysis.missing_information == ["Scale"]


def test_analysis_rejects_invalid_category() -> None:
    """A category outside CAT-01..CAT-08 is rejected."""
    payload = {**VALID_ANALYSIS, "inferred_categories": ["CAT-99"]}
    with pytest.raises(ValidationError):
        ProjectAnalysis.model_validate(payload)


def test_analysis_rejects_empty_stakeholders() -> None:
    """The stakeholders array must be non-empty (PROMPT_AND_OUTPUT_DESIGN)."""
    payload = {**VALID_ANALYSIS, "stakeholders": []}
    with pytest.raises(ValidationError):
        ProjectAnalysis.model_validate(payload)


def test_analysis_rejects_duplicate_categories() -> None:
    """Duplicate inferred categories are rejected."""
    payload = {**VALID_ANALYSIS, "inferred_categories": ["CAT-02", "CAT-02"]}
    with pytest.raises(ValidationError):
        ProjectAnalysis.model_validate(payload)


def test_analysis_rejects_extra_fields() -> None:
    """Unknown keys are rejected (strict mode, SEC-026)."""
    payload = {**VALID_ANALYSIS, "malicious": "ignored"}
    with pytest.raises(ValidationError):
        ProjectAnalysis.model_validate(payload)


def test_valid_question_set_passes() -> None:
    """A well-formed clarification question set validates."""
    question_set = ClarificationQuestionSet.model_validate(
        {
            "questions": [
                {
                    "question_text": "How many nodes?",
                    "reason": "Scale matters.",
                    "is_critical": True,
                    "target_gap": "Node count",
                    "expected_answer_type": "number",
                }
            ]
        }
    )
    assert len(question_set.questions) == 1
    assert question_set.questions[0].expected_answer_type.value == "number"


def test_question_set_rejects_empty_questions() -> None:
    """At least one question is required."""
    with pytest.raises(ValidationError):
        ClarificationQuestionSet.model_validate({"questions": []})


def test_question_set_rejects_unknown_answer_type() -> None:
    """An answer type outside the supported enum is rejected."""
    with pytest.raises(ValidationError):
        ClarificationQuestionSet.model_validate(
            {
                "questions": [
                    {
                        "question_text": "Q?",
                        "reason": "R.",
                        "is_critical": False,
                        "target_gap": "Gap",
                        "expected_answer_type": "password",
                    }
                ]
            }
        )


def test_question_set_repairs_one_malformed_target_gap_key(caplog) -> None:
    """A single target-prefixed field typo is repaired and recorded."""
    question_set = ClarificationQuestionSet.model_validate(
        {
            "questions": [
                {
                    "question_text": "Which policy applies?",
                    "reason": "The policy determines controls.",
                    "is_critical": True,
                    "target_constraint": "Policy scope",
                    "expected_answer_type": "text",
                }
            ]
        }
    )
    assert question_set.questions[0].target_gap == "Policy scope"
    assert "malformed target_gap" in caplog.text


def test_question_set_does_not_repair_unrelated_extra_fields() -> None:
    """The repair does not weaken strict rejection of arbitrary fields."""
    with pytest.raises(ValidationError):
        ClarificationQuestionSet.model_validate(
            {
                "questions": [
                    {
                        "question_text": "Which policy applies?",
                        "reason": "The policy determines controls.",
                        "is_critical": True,
                        "unrelated": "Policy scope",
                        "expected_answer_type": "text",
                    }
                ]
            }
        )


def test_answer_item_requires_text_when_not_skipped() -> None:
    """A non-skipped answer must not be empty (API_CONTRACT §4)."""
    with pytest.raises(ValidationError):
        ClarificationAnswerItem.model_validate(
            {"question_id": "q-001", "answer_text": "", "skipped": False}
        )


def test_skipped_answer_allows_empty_text() -> None:
    """A skipped answer may have empty text."""
    item = ClarificationAnswerItem.model_validate(
        {"question_id": "q-001", "answer_text": "", "skipped": True}
    )
    assert item.skipped is True
    assert item.answer_text == ""


def test_submission_requires_at_least_one_answer() -> None:
    """An empty answers list is rejected."""
    with pytest.raises(ValidationError):
        ClarificationAnswerSubmission.model_validate({"answers": []})
