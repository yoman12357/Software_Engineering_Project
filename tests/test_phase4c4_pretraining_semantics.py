"""Regression tests for the Phase 4C.4 pre-training semantic patch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ai.finetuning.scripts.audit_dataset import (
    build_review_sample,
    cross_stage_consistency_validation,
    nfr_classification_validation,
    read_jsonl,
)
from ai.finetuning.scripts.generate_dataset import (
    _full_srs_payload,
    _safe_context_analysis,
    _synthesized_nfr,
    generate_dataset,
)
from ai.finetuning.scripts.scenario_library import SCENARIOS


@pytest.fixture(scope="module")
def generated_records(tmp_path_factory: pytest.TempPathFactory) -> list[dict[str, Any]]:
    """Generate temporary Phase 4C.4 task records for review-sample checks."""
    out_dir = tmp_path_factory.mktemp("phase4c4-data")
    generate_dataset(out_dir)
    records: list[dict[str, Any]] = []
    for path in sorted(Path(out_dir).glob("*.jsonl")):
        records.extend(read_jsonl(path))
    return sorted(records, key=lambda row: row["record_id"])


def _scenario(scenario_id: str) -> dict[str, Any]:
    """Return one scenario by stable ID."""
    return next(scenario for scenario in SCENARIOS if scenario["id"] == scenario_id)


def _fake_nfr_record(title: str, statement: str, acceptance: str) -> dict[str, Any]:
    """Build a minimal NFR record for classification validation."""
    requirement = {
        "id": "NFR-001",
        "category": "non_functional",
        "title": title,
        "statement": statement,
        "rationale": "Classification regression fixture.",
        "priority": "should",
        "acceptance_criteria": acceptance,
        "dependencies": [],
        "source_references": [],
        "confidence": "medium",
        "user_confirmed": False,
    }
    return {
        "record_id": "SCN-009|classification_fixture",
        "task": "non_functional_requirements",
        "scenario_id": "SCN-009",
        "messages": [
            {"role": "system", "content": ""},
            {"role": "user", "content": ""},
            {
                "role": "assistant",
                "content": json.dumps({"non_functional_requirements": [requirement]}),
            },
        ],
    }


def test_medical_devices_do_not_confirm_patient_data_processing() -> None:
    """Medical-device monitoring must not imply patient-data handling."""
    scenario = _scenario("SCN-009")
    analysis = _safe_context_analysis(scenario)
    nfr = _synthesized_nfr(scenario)

    assert all("patient data" not in asset.lower() for asset in analysis["assets"])
    assert any("health data remains unresolved" in gap for gap in analysis["missing_information"])
    assert nfr is not None
    assert nfr["title"] == "Medical-Device Event Reliability"
    assert "health-related data" not in nfr["statement"].lower()
    assert "handles health" not in nfr["rationale"].lower()


def test_scn001_unresolved_passivity_is_not_promoted_to_srs_scope() -> None:
    """SCN-001 no-control semantics must remain unresolved across the full SRS."""
    payload = _full_srs_payload(_scenario("SCN-001"))
    scope_text = " ".join(
        [*payload["scope"]["in_scope"], *payload["scope"]["out_of_scope"]]
    ).lower()
    architecture_text = json.dumps(payload["architecture_summary"]).lower()
    requirement_text = json.dumps(
        [
            *payload["functional_requirements"],
            *payload["non_functional_requirements"],
            *payload["security_requirements"],
            *payload["data_requirements"],
            *payload["network_requirements"],
        ]
    ).lower()

    assert "passive" not in scope_text
    assert "sending commands" not in scope_text
    assert "automatic pump control" not in scope_text
    assert "passive" not in architecture_text
    assert "sending commands" not in requirement_text
    assert "automatic pump control" not in requirement_text
    assert any(
        "remains unresolved" in assumption.lower()
        for assumption in payload["assumptions"]
    )


def test_reclassified_nfr_does_not_create_full_srs_filler() -> None:
    """A scenario without a defensible NFR must keep the full-SRS NFR section empty."""
    payload = _full_srs_payload(_scenario("SCN-003"))

    assert payload["non_functional_requirements"] == []


def test_scope_validator_detects_no_control_equivalents() -> None:
    """The cross-stage audit must catch semantic no-control scope promotions."""
    record = {
        "record_id": "SCN-001|scope_fixture",
        "task": "srs_generation",
        "scenario_id": "SCN-001",
        "messages": [
            {"role": "system", "content": ""},
            {"role": "user", "content": ""},
            {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "scope": {
                            "in_scope": [],
                            "out_of_scope": [
                                "Sending commands to field devices",
                                "Automatic pump control",
                            ],
                        },
                        "assumptions": [],
                        "architecture_summary": {},
                        "risks": [],
                        "threats": [],
                    }
                ),
            },
        ],
    }

    report = cross_stage_consistency_validation([record])

    assert report["scope_level_assumption_promotions"] == 2
    assert report["requirement_level_assumption_promotions"] == 0
    assert report["failure_count"] == 2


@pytest.mark.parametrize(
    ("title", "statement", "acceptance"),
    [
        (
            "Privileged Data Exposure Control",
            "The system shall restrict confidential-data access to authorized roles.",
            "GIVEN confidential data, WHEN access is attempted, THEN unauthorized "
            "access shall be denied.",
        ),
        (
            "Tenant Data Privacy Boundary",
            "The system shall preserve tenant authorization boundaries.",
            "GIVEN tenant A, WHEN tenant B requests its data, THEN access shall be denied.",
        ),
        (
            "Health Data Privacy Exposure",
            "The system shall limit health-data exposure to authorized users.",
            "GIVEN health data, WHEN access occurs, THEN the authorized role shall be shown.",
        ),
        (
            "Firmware Signature Integrity",
            "The system shall verify firmware signatures before acceptance.",
            "GIVEN firmware, WHEN it is submitted, THEN the signature verification "
            "outcome shall be recorded.",
        ),
        (
            "Signature Evidence Integrity",
            "The system shall require a valid document signature.",
            "GIVEN a document, WHEN it is submitted, THEN its signature verification "
            "outcome shall be shown.",
        ),
    ],
)
def test_security_capabilities_are_rejected_as_nfrs(
    title: str,
    statement: str,
    acceptance: str,
) -> None:
    """Concrete privacy, access, and signature controls must not pass as NFRs."""
    report = nfr_classification_validation(
        [_fake_nfr_record(title, statement, acceptance)]
    )

    assert report["failure_count"] == 1


def test_review_sample_guarantees_threat_and_targeted_scenarios(
    generated_records: list[dict[str, Any]],
) -> None:
    """The manual sample must retain threat and Phase 4C.4 coverage within its cap."""
    sample = build_review_sample(
        generated_records,
        {"highest_similarity_matches": []},
        {},
    )
    record_ids = {record["record_id"] for record in sample}

    assert any(record["task"] == "threat_model" for record in sample)
    assert "SCN-001|context_extraction" in record_ids
    assert "SCN-001|srs_generation" in record_ids
    assert "SCN-009|context_extraction" in record_ids
    assert "SCN-009|functional_requirements" in record_ids
    assert "SCN-009|non_functional_requirements" in record_ids
    assert any(record["task"] == "requirement_validation" for record in sample)
