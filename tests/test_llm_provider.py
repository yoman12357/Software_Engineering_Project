"""Provider-contract and deterministic mock tests (Phase 1B)."""

import json

import pytest

from src.core.config import Settings
from src.llm.base import (
    LLMOutputError,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMTask,
    load_json_object,
)
from src.llm.factory import create_llm_provider
from src.llm.mock_provider import MOCK_MODEL_NAME, MockLLMProvider
from src.schemas.analysis import ProjectAnalysis
from src.schemas.clarification import ClarificationQuestionSet

SAMPLE_DESCRIPTION = "I want to build a firewall and monitoring system for my college network."


def test_factory_returns_mock_provider_by_default() -> None:
    """The default settings produce the deterministic mock provider."""
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    provider = create_llm_provider(settings)
    assert isinstance(provider, MockLLMProvider)
    assert provider.provider_name == "mock"


def test_factory_rejects_unknown_provider() -> None:
    """An unsupported CYBERSRS_LLM_PROVIDER raises a clear error."""
    settings = Settings(_env_file=None, llm_provider="unknown_provider")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="Unsupported CYBERSRS_LLM_PROVIDER"):
        create_llm_provider(settings)


def test_factory_accepts_ollama_provider() -> None:
    """The factory accepts 'ollama' as a valid provider."""
    settings = Settings(_env_file=None, llm_provider="ollama")  # type: ignore[call-arg]
    provider = create_llm_provider(settings)
    assert provider.provider_name == "ollama"
    assert provider.model_name == "qwen3:4b-instruct-2507-q4_K_M"


def test_provider_is_an_llm_provider() -> None:
    """The mock implements the LLMProvider contract."""
    provider: LLMProvider = MockLLMProvider()
    assert isinstance(provider, LLMProvider)
    assert provider.model_name == MOCK_MODEL_NAME


def test_analysis_output_validates_and_is_deterministic() -> None:
    """The same description produces identical, schema-valid analysis JSON."""
    provider = MockLLMProvider()
    request = LLMRequest(
        task=LLMTask.ANALYSIS,
        system_prompt="analyse",
        user_content=SAMPLE_DESCRIPTION,
    )
    first = provider.generate(request)
    second = provider.generate(request)

    assert first.content == second.content
    assert first.is_deterministic is True

    analysis = provider.parse_structured(first, ProjectAnalysis)
    assert analysis.inferred_categories == ["CAT-02", "CAT-03"]
    assert analysis.stakeholders
    assert analysis.goals
    assert "Expected number of network nodes" in analysis.missing_information


def test_structured_parser_recovers_logged_tool_call_suffix(caplog) -> None:
    """A stray tool-call suffix is removed while schema validation remains strict."""
    provider = MockLLMProvider()
    valid = provider.generate(
        LLMRequest(
            task=LLMTask.ANALYSIS,
            system_prompt="analyse",
            user_content=SAMPLE_DESCRIPTION,
        )
    )
    wrapped = LLMResponse(
        content=f"</tool_call>\n\n{valid.content}",
        model_name="cybersrs-qwen3-4b-ft",
        is_deterministic=False,
    )

    analysis = provider.parse_structured(wrapped, ProjectAnalysis)

    assert analysis.inferred_categories == ["CAT-02", "CAT-03"]
    assert "removing a non-JSON wrapper" in caplog.text


def test_json_object_loader_leaves_valid_json_unchanged() -> None:
    """Canonical JSON passes without reporting deterministic wrapper removal."""
    payload, wrapper_removed = load_json_object('{"value": 1}')
    assert payload == {"value": 1}
    assert wrapper_removed is False


def test_clarification_output_validates_and_is_deterministic() -> None:
    """The same description produces identical, schema-valid questions JSON."""
    provider = MockLLMProvider()
    request = LLMRequest(
        task=LLMTask.CLARIFICATION,
        system_prompt="clarify",
        user_content=SAMPLE_DESCRIPTION,
    )
    first = provider.generate(request)
    second = provider.generate(request)

    assert first.content == second.content

    question_set = provider.parse_structured(first, ClarificationQuestionSet)
    assert len(question_set.questions) >= 1
    first_q = question_set.questions[0]
    assert first_q.question_text
    assert first_q.reason
    assert first_q.target_gap
    assert first_q.expected_answer_type.value in {"text", "number", "list", "boolean"}


def test_fallback_analysis_is_deterministic_for_unknown_description() -> None:
    """Descriptions outside the fixed catalog still get deterministic output."""
    provider = MockLLMProvider()
    description = "A completely custom security monitoring system."
    first = provider.generate(
        LLMRequest(task=LLMTask.ANALYSIS, system_prompt="x", user_content=description)
    )
    second = provider.generate(
        LLMRequest(task=LLMTask.ANALYSIS, system_prompt="x", user_content=description)
    )
    assert first.content == second.content
    analysis = provider.parse_structured(first, ProjectAnalysis)
    assert analysis.inferred_categories


def test_parse_structured_rejects_invalid_json() -> None:
    """Non-JSON provider content raises LLMOutputError."""
    provider = MockLLMProvider()
    response = provider.generate(
        LLMRequest(task=LLMTask.ANALYSIS, system_prompt="x", user_content="data")
    )
    # Corrupt the content after generation.
    from src.llm.base import LLMResponse

    bad = LLMResponse(content="not json {", model_name=response.model_name)
    with pytest.raises(LLMOutputError):
        provider.parse_structured(bad, ProjectAnalysis)


def test_parse_structured_rejects_schema_violations() -> None:
    """Provider content failing the schema raises LLMOutputError."""
    provider = MockLLMProvider()
    from src.llm.base import LLMResponse

    invalid_payload = json.dumps(
        {
            "stakeholders": [],
            "assets": [],
            "users": [],
            "constraints": [],
            "goals": [],
            "inferred_categories": ["CAT-99"],
            "missing_information": [],
            "project_summary": "",
        }
    )
    bad = LLMResponse(content=invalid_payload, model_name="mock")
    with pytest.raises(LLMOutputError):
        provider.parse_structured(bad, ProjectAnalysis)
