"""Regression tests for Phase 4C.3 fine-tuning dataset semantics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ai.finetuning.scripts.audit_dataset import (
    cross_stage_consistency_validation,
    nfr_classification_validation,
    nfr_pattern_bias_validation,
    read_jsonl,
    resolved_gap_validation,
    unsupported_provenance_claim_validation,
)
from ai.finetuning.scripts.generate_dataset import (
    _build_context_payload,
    _safe_context_analysis,
    _safe_requirement_items,
    generate_dataset,
)
from ai.finetuning.scripts.scenario_library import SCENARIOS


@pytest.fixture(scope="module")
def generated_records(tmp_path_factory: pytest.TempPathFactory) -> list[dict[str, Any]]:
    """Generate a temporary Phase 4C.3 dataset and return all task records."""
    out_dir = tmp_path_factory.mktemp("phase4c3-data")
    generate_dataset(out_dir)
    task_files = [
        "architecture.jsonl",
        "clarification_questions.jsonl",
        "context_extraction.jsonl",
        "data_requirements.jsonl",
        "functional_requirements.jsonl",
        "network_requirements.jsonl",
        "non_functional_requirements.jsonl",
        "requirement_validation.jsonl",
        "security_requirements.jsonl",
        "srs_generation.jsonl",
        "threat_model.jsonl",
    ]
    records: list[dict[str, Any]] = []
    for file_name in task_files:
        path = Path(out_dir) / file_name
        if path.exists():
            records.extend(read_jsonl(path))
    return sorted(records, key=lambda row: row["record_id"])


def _scenario(scenario_id: str) -> dict[str, Any]:
    """Return one scenario by ID."""
    return next(scenario for scenario in SCENARIOS if scenario["id"] == scenario_id)


def _fake_nfr_record(scenario_id: str, requirement: dict[str, Any]) -> dict[str, Any]:
    """Build a minimal non-functional-requirements record for audit tests."""
    return {
        "record_id": f"{scenario_id}|fake_nfr",
        "task": "non_functional_requirements",
        "scenario_id": scenario_id,
        "messages": [
            {"role": "system", "content": ""},
            {"role": "user", "content": ""},
            {
                "role": "assistant",
                "content": json.dumps({"non_functional_requirements": [requirement]}),
            },
        ],
        "provenance": {"requirement_provenance": "synthesized_nfr"},
    }


def test_confirmed_gap_removed_from_unresolved_state() -> None:
    """A confirmed clarification gap must not remain unresolved in context."""
    context = _build_context_payload(_scenario("SCN-001"))
    confirmed = context["information_state"]["clarification_confirmed"]
    unresolved = context["information_state"]["unconfirmed_or_missing"]

    confirmed_ids = {item["gap_id"] for item in confirmed}
    unresolved_ids = {item["gap_id"] for item in unresolved}

    assert confirmed_ids
    assert not confirmed_ids & unresolved_ids
    assert any("Eleven pump stations" in item["answer"] for item in confirmed)
    assert "Number of pump stations" not in json.dumps(unresolved)


def test_unresolved_gap_cannot_become_mandatory_requirement(
    generated_records: list[dict[str, Any]],
) -> None:
    """Later-stage records must not promote unresolved facts to requirements."""
    report = cross_stage_consistency_validation(generated_records)

    assert report["failure_count"] == 0


def test_clarification_answer_propagated_forward(
    generated_records: list[dict[str, Any]],
) -> None:
    """Confirmed answers must be present in later-stage project context prompts."""
    report = resolved_gap_validation(generated_records)

    assert report["confirmed_answers_not_propagated"] == 0
    assert report["failure_count"] == 0


def test_false_user_explicitly_requires_rationale_rejected() -> None:
    """Unsupported explicit-user provenance claims must be rejected."""
    requirement = {
        "id": "NFR-001",
        "category": "non_functional",
        "title": "Passive Monitoring",
        "statement": "The system shall operate passively for medical-device monitoring.",
        "rationale": "The hospital explicitly requires passive monitoring.",
        "priority": "must",
        "acceptance_criteria": (
            "GIVEN monitoring is active, WHEN device traffic is observed, "
            "THEN the system shall operate passively."
        ),
        "dependencies": [],
        "source_references": [],
        "confidence": "high",
        "user_confirmed": False,
    }

    report = unsupported_provenance_claim_validation(
        [_fake_nfr_record("SCN-009", requirement)]
    )

    assert report["failure_count"] == 1


def test_functional_capability_misclassified_as_nfr_rejected() -> None:
    """Capability-like NFRs such as alert forwarding must be rejected."""
    requirement = {
        "id": "NFR-001",
        "category": "non_functional",
        "title": "Centralised Alert Delivery",
        "statement": "The system shall deliver all branch alerts to the central SOC.",
        "rationale": "Alert delivery is a capability.",
        "priority": "must",
        "acceptance_criteria": (
            "GIVEN a branch alert, WHEN it is generated, "
            "THEN it shall appear at the central SOC."
        ),
        "dependencies": [],
        "source_references": [],
        "confidence": "high",
        "user_confirmed": False,
    }

    report = nfr_classification_validation([_fake_nfr_record("SCN-021", requirement)])

    assert report["failure_count"] == 1


def test_repeated_generic_nfr_template_rejected() -> None:
    """Dominant repeated NFR templates must fail the pattern-bias audit."""
    requirement = {
        "id": "NFR-001",
        "category": "non_functional",
        "title": "Generic Auditability",
        "statement": "The system shall keep all security activity reviewable.",
        "rationale": "Auditability is important.",
        "priority": "should",
        "acceptance_criteria": (
            "GIVEN a security event, WHEN it is reviewed, "
            "THEN the system shall show the event."
        ),
        "dependencies": [],
        "source_references": [],
        "confidence": "medium",
        "user_confirmed": False,
    }
    records = [_fake_nfr_record(f"SCN-{index:03d}", requirement) for index in range(1, 10)]

    report = nfr_pattern_bias_validation(records)

    assert report["failure_count"] > 0


def test_hospital_passive_monitoring_assumption_remains_unresolved() -> None:
    """Hospital non-interference remains a clarification issue, not a requirement."""
    scenario = _scenario("SCN-009")
    analysis = _safe_context_analysis(scenario)
    security_items = _safe_requirement_items(scenario, "security")

    assert any("fully passive" in item for item in analysis["missing_information"])
    assert all("passively" not in item["statement"].lower() for item in security_items)
