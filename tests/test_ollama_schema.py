"""Regression tests for Ollama generation-schema compatibility."""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from pydantic import ValidationError

from src.llm.base import LLMRequest, LLMTask
from src.llm.mock_provider import MockLLMProvider
from src.llm.ollama_provider import _response_format
from src.llm.ollama_schema import (
    SchemaProbeClassification,
    build_ollama_generation_schema,
    probe_ollama_schema,
)
from src.schemas.srs import SRSSchema


def _valid_srs_payload() -> dict[str, Any]:
    """Return the deterministic mock provider's canonical SRS payload."""
    context = {
        "project_name": "Schema Test",
        "description": "A campus firewall.",
        "inferred_categories": ["CAT-02"],
        "stakeholders": ["Campus IT"],
        "users": ["Network administrators"],
        "version": 1,
    }
    response = MockLLMProvider().generate(
        LLMRequest(
            task=LLMTask.SRS,
            system_prompt="generate",
            user_content=json.dumps(context),
        )
    )
    return json.loads(response.content)


def _collect_keyword_values(value: Any, keyword: str) -> list[Any]:
    """Collect values for one JSON-Schema keyword recursively."""
    values: list[Any] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == keyword:
                values.append(item)
            values.extend(_collect_keyword_values(item, keyword))
    elif isinstance(value, list):
        for item in value:
            values.extend(_collect_keyword_values(item, keyword))
    return values


def test_generation_schema_is_deterministic_and_does_not_mutate_canonical() -> None:
    """Compatibility derivation is stable and leaves Pydantic output unchanged."""
    canonical = SRSSchema.model_json_schema()
    original = copy.deepcopy(canonical)

    first = build_ollama_generation_schema(SRSSchema)
    second = build_ollama_generation_schema(SRSSchema)

    assert first == second
    assert canonical == original
    assert SRSSchema.model_json_schema() == original


def test_generation_schema_preserves_all_structural_fields() -> None:
    """Top-level and nested properties/required lists are never removed or added."""
    canonical = SRSSchema.model_json_schema()
    compatible = build_ollama_generation_schema(SRSSchema)

    assert compatible["properties"].keys() == canonical["properties"].keys()
    assert compatible["required"] == canonical["required"]
    assert compatible["$defs"].keys() == canonical["$defs"].keys()
    for name, definition in canonical["$defs"].items():
        transformed = compatible["$defs"][name]
        assert transformed.get("properties", {}).keys() == definition.get(
            "properties", {}
        ).keys()
        assert transformed.get("required", []) == definition.get("required", [])


def test_generation_schema_only_normalizes_digit_pattern_escape() -> None:
    """The compatibility delta is limited to equivalent regex spelling."""
    canonical = SRSSchema.model_json_schema()
    compatible = build_ollama_generation_schema(SRSSchema)
    canonical_patterns = _collect_keyword_values(canonical, "pattern")
    compatible_patterns = _collect_keyword_values(compatible, "pattern")

    assert len(canonical_patterns) == len(compatible_patterns) == 5
    assert all(r"\d" in pattern for pattern in canonical_patterns)
    assert all(r"\d" not in pattern for pattern in compatible_patterns)
    assert compatible_patterns == [
        pattern.replace(r"\d", "[0-9]") for pattern in canonical_patterns
    ]


def test_final_canonical_validation_remains_strict() -> None:
    """Generation compatibility never relaxes canonical semantic validation."""
    payload = _valid_srs_payload()
    malformed_threat = copy.deepcopy(payload)
    malformed_threat["threats"][0]["threat_id"] = "THR-1"
    missing_requirements = copy.deepcopy(payload)
    missing_requirements["functional_requirements"] = []

    with pytest.raises(ValidationError):
        SRSSchema.model_validate(malformed_threat)
    with pytest.raises(ValidationError):
        SRSSchema.model_validate(missing_requirements)


def test_generation_schema_does_not_fabricate_citations() -> None:
    """Schema derivation and final validation do not add source references."""
    build_ollama_generation_schema(SRSSchema)
    validated = SRSSchema.model_validate(_valid_srs_payload())
    assert all(
        requirement.source_references == []
        for requirements in validated.requirement_sections().values()
        for requirement in requirements
    )


@pytest.mark.parametrize(
    ("status_code", "error", "expected"),
    [
        (200, None, SchemaProbeClassification.SCHEMA_ACCEPTED),
        (
            400,
            '{"message":"Failed to initialize samplers: failed to parse grammar"}',
            SchemaProbeClassification.GRAMMAR_REJECTED,
        ),
        (500, "server unavailable", SchemaProbeClassification.OTHER_ERROR),
    ],
)
def test_probe_classifies_ollama_results(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    error: str | None,
    expected: SchemaProbeClassification,
) -> None:
    """Grammar rejection is distinct from acceptance and unrelated errors."""
    class Response:
        def __init__(self) -> None:
            self.status_code = status_code

        def json(self) -> dict[str, Any]:
            return {} if error is None else {"error": error}

    monkeypatch.setattr("src.llm.ollama_schema.httpx.post", lambda *a, **k: Response())
    result = probe_ollama_schema(
        base_url="http://127.0.0.1:11434",
        model_name="cybersrs-qwen3-4b-ft",
        schema={"type": "object"},
    )
    assert result.classification == expected
    assert result.status_code == status_code


def test_legacy_requests_remain_in_json_mode() -> None:
    """Schema compatibility does not alter base or legacy request behavior."""
    request = LLMRequest(
        task=LLMTask.ANALYSIS,
        system_prompt="analyse",
        user_content="project",
    )
    assert _response_format(request) == "json"
