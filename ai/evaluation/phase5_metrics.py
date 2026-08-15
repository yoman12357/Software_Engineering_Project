"""Deterministic metrics for the Phase 5 four-way evaluation."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from src.schemas.srs import SRSSchema
from src.services.srs_output_validation import validate_srs_output

REQUIREMENT_SECTIONS = (
    "functional_requirements",
    "non_functional_requirements",
    "security_requirements",
    "data_requirements",
    "network_requirements",
)


class ConfigVariant(StrEnum):
    """Canonical Phase 5 experiment configurations."""

    BASE = "base"
    BASE_RAG = "base_rag"
    FINETUNED = "finetuned"
    FINETUNED_RAG = "finetuned_rag"

    @property
    def model_variant(self) -> str:
        """Return the canonical runtime model variant."""
        return "base" if self in (self.BASE, self.BASE_RAG) else "finetuned"

    @property
    def rag_enabled(self) -> bool:
        """Return whether retrieval is enabled for this configuration."""
        return self in (self.BASE_RAG, self.FINETUNED_RAG)

    @property
    def label(self) -> str:
        """Return the stable portable-artifact label."""
        return self.name

    @classmethod
    def all(cls) -> tuple[ConfigVariant, ...]:
        """Return the four configurations in comparison order."""
        return (cls.BASE, cls.BASE_RAG, cls.FINETUNED, cls.FINETUNED_RAG)


@dataclass(frozen=True)
class OutputMetrics:
    """Deterministic measurements for one raw or final SRS representation."""

    json_valid: bool
    schema_valid: bool
    requirement_count: int
    functional_requirement_count: int
    non_functional_requirement_count: int
    security_requirement_count: int
    data_requirement_count: int
    network_requirement_count: int
    threat_count: int
    clarification_count: int
    missing_statements: int
    missing_acceptance_criteria: int
    invalid_priorities: int
    double_shall_violations: int
    acceptance_criteria_format_warnings: int
    acceptance_criteria_paraphrases: int
    unsupported_numeric_claims: int
    numeric_provenance_violations: int
    generic_rationale_violations: int
    citation_count: int
    citation_presence_rate: float
    valid_citation_count: int
    invalid_citation_count: int
    retrieval_success: bool
    retrieved_chunk_count: int
    atomicity_violations: None = None
    atomicity_metric_status: str = "manual_unsupported"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable metric mapping."""
        return asdict(self)


def _first_json_object(content: str) -> dict[str, Any] | None:
    """Extract the first balanced JSON object for secondary quality checks."""
    start = content.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(content[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    value = json.loads(content[start : index + 1])
                except json.JSONDecodeError:
                    return None
                return value if isinstance(value, dict) else None
    return None


def parse_raw_output(content: str | None) -> tuple[dict[str, Any] | None, bool]:
    """Return a raw payload and strict JSON-validity flag without repairing it."""
    if not content:
        return None, False
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return _first_json_object(content), False
    return (value if isinstance(value, dict) else None), isinstance(value, dict)


def evaluate_output(
    payload: dict[str, Any] | None,
    *,
    json_valid: bool,
    clarification_count: int,
    retrieved_chunk_ids: list[str] | None = None,
) -> OutputMetrics:
    """Measure an SRS payload using schema and deterministic validation rules."""
    payload = payload or {}
    retrieved_ids = set(retrieved_chunk_ids or [])
    requirements = [
        item
        for section in REQUIREMENT_SECTIONS
        for item in payload.get(section, [])
        if isinstance(item, dict)
    ]
    schema: SRSSchema | None = None
    try:
        schema = SRSSchema.model_validate(payload)
    except (TypeError, ValueError):
        pass

    issues = validate_srs_output(schema) if schema is not None else []
    issue_counts: dict[str, int] = {}
    for issue in issues:
        issue_counts[issue.code] = issue_counts.get(issue.code, 0) + 1

    citations = [
        reference
        for requirement in requirements
        for reference in requirement.get("source_references", [])
        if isinstance(reference, dict)
    ]
    cited_requirements = sum(
        bool(requirement.get("source_references")) for requirement in requirements
    )
    valid_citations = sum(
        str(reference.get("source_id", "")) in retrieved_ids for reference in citations
    )
    missing_statements = sum(
        not isinstance(req.get("statement"), str) or not req.get("statement", "").strip()
        for req in requirements
    )
    missing_acceptance = sum(
        not isinstance(req.get("acceptance_criteria"), str)
        or not req.get("acceptance_criteria", "").strip()
        for req in requirements
    )
    invalid_priorities = sum(
        req.get("priority") not in {"must", "should", "could"} for req in requirements
    )
    double_shall = sum(
        len(re.findall(r"\bshall\b", str(req.get("statement", "")), re.IGNORECASE)) > 1
        for req in requirements
    )

    counts = {
        section: len(payload.get(section, []))
        if isinstance(payload.get(section, []), list)
        else 0
        for section in REQUIREMENT_SECTIONS
    }
    threats = payload.get("threat_model", [])
    if isinstance(threats, dict):
        threats = threats.get("threats", [])

    return OutputMetrics(
        json_valid=json_valid,
        schema_valid=schema is not None,
        requirement_count=len(requirements),
        functional_requirement_count=counts["functional_requirements"],
        non_functional_requirement_count=counts["non_functional_requirements"],
        security_requirement_count=counts["security_requirements"],
        data_requirement_count=counts["data_requirements"],
        network_requirement_count=counts["network_requirements"],
        threat_count=len(threats) if isinstance(threats, list) else 0,
        clarification_count=clarification_count,
        missing_statements=missing_statements,
        missing_acceptance_criteria=missing_acceptance,
        invalid_priorities=invalid_priorities,
        double_shall_violations=double_shall,
        acceptance_criteria_format_warnings=issue_counts.get(
            "ACCEPTANCE_CRITERIA_FORMAT", 0
        ),
        acceptance_criteria_paraphrases=issue_counts.get(
            "ACCEPTANCE_CRITERIA_PARAPHRASE", 0
        ),
        unsupported_numeric_claims=issue_counts.get("UNSUPPORTED_NUMERIC_CONSTRAINT", 0),
        numeric_provenance_violations=issue_counts.get(
            "UNSUPPORTED_NUMERIC_CONSTRAINT", 0
        ),
        generic_rationale_violations=issue_counts.get("GENERIC_RATIONALE", 0),
        citation_count=len(citations),
        citation_presence_rate=(cited_requirements / len(requirements) if requirements else 0.0),
        valid_citation_count=valid_citations,
        invalid_citation_count=len(citations) - valid_citations,
        retrieval_success=bool(retrieved_ids),
        retrieved_chunk_count=len(retrieved_ids),
    )


def compute_phase5_aggregate(
    config: ConfigVariant, results: list[dict[str, Any]]
) -> dict[str, Any]:
    """Aggregate completed case results without fabricating unavailable values."""
    attempted = len(results)
    successful = [result for result in results if result.get("status") == "COMPLETED"]
    aggregate: dict[str, Any] = {
        "configuration": config.label,
        "model_variant": config.model_variant,
        "rag_enabled": config.rag_enabled,
        "status": "COMPLETED" if attempted else "NOT_RUN",
        "total_cases": attempted,
        "successful_cases": len(successful),
        "generation_success_rate": len(successful) / attempted if attempted else None,
    }
    if not successful:
        aggregate["raw_metrics"] = None
        aggregate["final_metrics"] = None
        aggregate["latency"] = None
        return aggregate

    def average(stage: str, field: str) -> float:
        values = [float(result[stage][field]) for result in successful]
        return sum(values) / len(values)

    metric_fields = (
        "schema_valid",
        "requirement_count",
        "functional_requirement_count",
        "security_requirement_count",
        "threat_count",
        "clarification_count",
        "double_shall_violations",
        "missing_acceptance_criteria",
        "unsupported_numeric_claims",
        "numeric_provenance_violations",
        "generic_rationale_violations",
        "citation_presence_rate",
        "invalid_citation_count",
        "retrieved_chunk_count",
    )
    aggregate["raw_metrics"] = {field: average("raw_metrics", field) for field in metric_fields}
    aggregate["final_metrics"] = {
        field: average("final_metrics", field) for field in metric_fields
    }
    aggregate["latency"] = {
        field: sum(float(result["latencies"][field]) for result in successful) / len(successful)
        for field in ("analysis_seconds", "clarification_seconds", "srs_seconds", "total_seconds")
    }
    return aggregate


def generate_comparison_markdown(config_summaries: list[dict[str, Any]]) -> str:
    """Render a portable comparison with explicit unavailable statuses."""
    by_name = {item["configuration"]: item for item in config_summaries}
    labels = [config.label for config in ConfigVariant.all()]
    lines = [
        "# Phase 5 Evaluation Comparison",
        "",
        "| Metric | " + " | ".join(labels) + " |",
        "|---|" + "---|" * len(labels),
    ]
    metrics = (
        ("Status", None, None),
        ("Successful cases", None, "successful_cases"),
        ("Final schema-valid rate", "final_metrics", "schema_valid"),
        ("Final requirement count", "final_metrics", "requirement_count"),
        ("Raw schema-valid rate", "raw_metrics", "schema_valid"),
        ("Raw double-shall violations", "raw_metrics", "double_shall_violations"),
        ("Final invalid citations", "final_metrics", "invalid_citation_count"),
        ("Average total latency (s)", "latency", "total_seconds"),
    )
    for title, group, field in metrics:
        values = []
        for label in labels:
            summary = by_name.get(label)
            if summary is None:
                values.append("NOT_RUN")
            elif title == "Status":
                values.append(str(summary["status"]))
            elif group is None:
                values.append(str(summary.get(field, "NOT_RUN")))
            elif summary.get(group) is None:
                values.append(str(summary["status"]))
            else:
                values.append(f"{summary[group][field]:.3f}")
        lines.append(f"| {title} | " + " | ".join(values) + " |")
    lines.extend(
        [
            "",
            "Raw metrics are measured before deterministic validation/repair; "
            "final metrics are measured after it.",
            "Atomicity is marked `manual_unsupported` per case because no "
            "deterministic atomicity rule is implemented.",
        ]
    )
    return "\n".join(lines) + "\n"
