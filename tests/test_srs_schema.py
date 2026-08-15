"""SRS schema validation tests (Phase 1C)."""

import pytest
from pydantic import ValidationError

from src.schemas.srs import (
    Requirement,
    SRSSchema,
    validate_requirement_id,
)

VALID_REQUIREMENT = {
    "id": "FR-001",
    "category": "functional",
    "title": "Traffic Filtering",
    "statement": "The system shall filter inbound traffic according to rules.",
    "rationale": "Core control for perimeter security.",
    "priority": "must",
    "acceptance_criteria": "Verify denied traffic is blocked under test.",
    "dependencies": [],
    "source_references": [],
    "confidence": "high",
    "user_confirmed": False,
}


def _valid_srs(**overrides):
    """Return a valid SRSSchema payload with optional overrides."""
    payload = {
        "metadata": {
            "project_name": "Campus Firewall",
            "version": 1,
            "generated_at": "2026-01-01T00:00:00Z",
            "model_name": "cybersrs-mock-1b",
            "adapter_name": None,
            "inferred_categories": ["CAT-02", "CAT-03"],
        },
        "project_overview": {
            "description": "A firewall for the campus network.",
            "purpose": "Filter traffic and monitor for threats.",
            "context": "College campus.",
        },
        "scope": {
            "in_scope": ["Firewall", "Monitoring"],
            "out_of_scope": ["Penetration testing"],
        },
        "assumptions": ["Existing infrastructure is in place."],
        "stakeholders": ["IT department"],
        "user_roles": ["Administrators"],
        "functional_requirements": [VALID_REQUIREMENT],
        "non_functional_requirements": [
            {
                **VALID_REQUIREMENT,
                "id": "NFR-001",
                "category": "non_functional",
                "title": "Availability",
                "statement": "The system shall remain available with no more than 5 "
                "minutes downtime per month.",
            }
        ],
        "security_requirements": [],
        "data_requirements": [],
        "network_requirements": [],
        "architecture_summary": {
            "overview": "Layered security.",
            "components": [
                {
                    "name": "Firewall",
                    "description": "Edge filtering.",
                    "responsibilities": ["Filter traffic"],
                }
            ],
            "data_flows": [],
            "deployment_notes": "",
        },
        "threats": [],
        "mitigations": [],
        "testing_strategy": [],
        "risks": [],
        "unresolved_questions": [],
        "references": [],
        "validation_report": None,
    }
    payload.update(overrides)
    return payload


def test_valid_srs_passes() -> None:
    """A well-formed SRS validates."""
    srs = SRSSchema.model_validate(_valid_srs())
    assert srs.metadata.version == 1
    assert len(srs.functional_requirements) == 1


def test_requires_functional_requirements() -> None:
    """At least one functional requirement is required."""
    with pytest.raises(ValidationError):
        SRSSchema.model_validate(_valid_srs(functional_requirements=[]))


def test_rejects_duplicate_requirement_ids_across_sections() -> None:
    """Duplicate IDs across different sections are rejected (FR-047)."""
    payload = _valid_srs(
        non_functional_requirements=[
            {
                **VALID_REQUIREMENT,
                "id": "FR-001",  # duplicate of the functional requirement
                "category": "non_functional",
            }
        ]
    )
    with pytest.raises(ValidationError, match="duplicate requirement id"):
        SRSSchema.model_validate(payload)


def test_rejects_malformed_requirement_id() -> None:
    """Requirement IDs must follow the documented pattern."""
    payload = _valid_srs(functional_requirements=[{**VALID_REQUIREMENT, "id": "FR-1"}])
    with pytest.raises(ValidationError):
        SRSSchema.model_validate(payload)


def test_rejects_empty_statement() -> None:
    """Requirement statements must not be empty."""
    payload = _valid_srs(functional_requirements=[{**VALID_REQUIREMENT, "statement": ""}])
    with pytest.raises(ValidationError):
        SRSSchema.model_validate(payload)


def test_rejects_statement_without_shall_language() -> None:
    """Statements should use testable 'shall' language."""
    payload = _valid_srs(
        functional_requirements=[{**VALID_REQUIREMENT, "statement": "Traffic is filtered."}]
    )
    with pytest.raises(ValidationError, match="shall"):
        SRSSchema.model_validate(payload)


def test_rejects_missing_acceptance_criteria() -> None:
    """Acceptance criteria are required on every requirement."""
    payload = _valid_srs(functional_requirements=[{**VALID_REQUIREMENT, "acceptance_criteria": ""}])
    with pytest.raises(ValidationError):
        SRSSchema.model_validate(payload)


def test_rejects_invalid_priority() -> None:
    """Priorities must be one of must/should/could."""
    payload = _valid_srs(functional_requirements=[{**VALID_REQUIREMENT, "priority": "critical"}])
    with pytest.raises(ValidationError):
        SRSSchema.model_validate(payload)


def test_rejects_extra_fields() -> None:
    """Unknown keys are rejected (strict mode, SEC-026)."""
    with pytest.raises(ValidationError):
        SRSSchema.model_validate(_valid_srs(extra_field="nope"))


def test_requirement_matches_approved_format() -> None:
    """A requirement carries all documented fields (PROMPT_AND_OUTPUT_DESIGN §4)."""
    requirement = Requirement.model_validate(VALID_REQUIREMENT)
    assert requirement.id == "FR-001"
    assert requirement.title
    assert requirement.rationale
    assert requirement.priority.value == "must"
    assert requirement.user_confirmed is False
    assert requirement.source_references == []


def test_validate_requirement_id_accepts_valid_pattern() -> None:
    """FR-001, NFR-001, SEC-001, DATA-001, NET-001 all validate."""
    for value in ("FR-001", "NFR-012", "SEC-999", "DATA-004", "NET-007"):
        assert validate_requirement_id(value) == value


def test_validate_requirement_id_rejects_bad_pattern() -> None:
    """Malformed IDs are rejected."""
    for value in ("FR-1", "FR", "123", "FR-0000", "X-001"):
        with pytest.raises(ValueError):
            validate_requirement_id(value)
