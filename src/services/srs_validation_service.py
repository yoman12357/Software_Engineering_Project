"""Deterministic SRS validation (Phase 1C).

Checks (without LLM) that the SRS is structurally sound: duplicate requirement
IDs, missing IDs, empty statements, missing acceptance criteria, invalid
priorities, and malformed sections. Produces a :class:`ValidationReport` with
an overall quality score (FR-050..FR-054).
"""

from __future__ import annotations

from ..db.models import SRSVersion
from ..schemas.srs import (
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    validate_requirement_id,
)

# Requirement-bearing sections supported by the schema.
REQUIREMENT_SECTIONS: tuple[str, ...] = (
    "functional_requirements",
    "non_functional_requirements",
    "security_requirements",
    "data_requirements",
    "network_requirements",
)

VALID_PRIORITIES: frozenset[str] = frozenset({"must", "should", "could"})

# Sections that must be present and non-empty for a complete SRS (FR-050).
MANDATORY_SECTIONS: tuple[str, ...] = (
    "functional_requirements",
    "non_functional_requirements",
    "architecture_summary",
)

MAX_SCORE = 100


class SRSValidationService:
    """Runs deterministic validation rules over a stored SRS version."""

    def validate(self, version: SRSVersion) -> ValidationReport:
        """Validate the SRS JSON of a persisted version.

        Returns:
            A validation report with an overall score (0-100) and a list of
            issues. Malformed SRS JSON (not a dict) is reported as a single
            fatal issue with score 0.
        """
        raw = version.srs_json
        if not isinstance(raw, dict):
            return self._fatal_report("srs_json is not an object")

        issues: list[ValidationIssue] = []
        next_issue = 1

        def add_issue(
            section: str,
            message: str,
            severity: ValidationSeverity = ValidationSeverity.WARNING,
            requirement_id: str | None = None,
        ) -> None:
            nonlocal next_issue
            issues.append(
                ValidationIssue(
                    issue_id=f"VAL-{next_issue:03d}",
                    severity=severity,
                    section=section,
                    requirement_id=requirement_id,
                    message=message,
                )
            )
            next_issue += 1

        all_requirement_ids: dict[str, str] = {}

        for section in REQUIREMENT_SECTIONS:
            payload = raw.get(section)
            if payload is None:
                if section in MANDATORY_SECTIONS:
                    add_issue(
                        section,
                        "Mandatory section is missing.",
                        ValidationSeverity.ERROR,
                    )
                continue
            if not isinstance(payload, list):
                add_issue(
                    section,
                    "Section is not a list.",
                    ValidationSeverity.ERROR,
                )
                continue

            for item in payload:
                if not isinstance(item, dict):
                    add_issue(
                        section,
                        "Entry is not an object.",
                        ValidationSeverity.ERROR,
                    )
                    continue

                req_id = item.get("id")
                if not isinstance(req_id, str) or not req_id.strip():
                    add_issue(
                        section,
                        "Requirement is missing an ID.",
                        ValidationSeverity.ERROR,
                    )
                else:
                    # Malformed ID pattern.
                    try:
                        validate_requirement_id(req_id)
                    except ValueError:
                        add_issue(
                            section,
                            f"Requirement ID {req_id!r} is malformed.",
                            ValidationSeverity.ERROR,
                            requirement_id=str(req_id),
                        )
                    # Duplicate ID across sections.
                    previous_section = all_requirement_ids.get(req_id)
                    if previous_section is not None and previous_section != section:
                        add_issue(
                            section,
                            f"Duplicate requirement ID {req_id!r} (also in {previous_section}).",
                            ValidationSeverity.ERROR,
                            requirement_id=req_id,
                        )
                    else:
                        all_requirement_ids[req_id] = section

                # Empty statement.
                statement = item.get("statement", "")
                if not isinstance(statement, str) or not statement.strip():
                    add_issue(
                        section,
                        "Requirement has an empty statement.",
                        ValidationSeverity.ERROR,
                        requirement_id=str(req_id or ""),
                    )

                # Missing acceptance criteria.
                acceptance = item.get("acceptance_criteria")
                if not isinstance(acceptance, str) or not acceptance.strip():
                    add_issue(
                        section,
                        "Requirement is missing acceptance criteria.",
                        ValidationSeverity.WARNING,
                        requirement_id=str(req_id or ""),
                    )

                # Invalid priority.
                priority = item.get("priority")
                if priority is not None and priority not in VALID_PRIORITIES:
                    add_issue(
                        section,
                        f"Invalid priority {priority!r}.",
                        ValidationSeverity.ERROR,
                        requirement_id=str(req_id or ""),
                    )

        # Malformed architecture summary.
        architecture = raw.get("architecture_summary")
        if not isinstance(architecture, dict):
            add_issue(
                "architecture_summary",
                "Architecture summary is missing or malformed.",
                ValidationSeverity.ERROR,
            )

        score = self._calculate_score(issues)
        version.status = "validated" if score >= 60 else "draft"

        return ValidationReport(overall_score=score, issues=issues)

    def _calculate_score(self, issues: list[ValidationIssue]) -> int:
        """Compute a deterministic quality score based on issue severity.

        Starts at 100 and subtracts per issue: 10 per error, 3 per warning,
        1 per info, floored at 0. Missing mandatory sections also reduce the
        score via their error issues.
        """
        error_count = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        info_count = sum(1 for i in issues if i.severity == ValidationSeverity.INFO)
        score = MAX_SCORE - (error_count * 10) - (warning_count * 3) - info_count
        return max(score, 0)

    def _fatal_report(self, message: str) -> ValidationReport:
        """Return a report for SRS JSON that cannot be interpreted at all."""
        return ValidationReport(
            overall_score=0,
            issues=[
                ValidationIssue(
                    issue_id="VAL-001",
                    severity=ValidationSeverity.ERROR,
                    section="srs_json",
                    message=message,
                )
            ],
        )
