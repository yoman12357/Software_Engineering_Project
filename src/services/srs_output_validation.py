"""Deterministic SRS output validation for CyberSRS.

Validates generated SRS against quality rules that cannot be enforced by schema alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from src.schemas.srs import Requirement, SRSSchema


@dataclass
class ValidationIssue:
    """A single validation finding."""

    code: str
    severity: str  # "error" | "warning" | "info"
    section: str
    requirement_id: str | None
    message: str


def validate_srs_output(
    srs: SRSSchema, retrieval_context: list[Any] | None = None
) -> list[ValidationIssue]:
    """Run all deterministic validations on generated SRS.

    Args:
        srs: The validated SRSSchema object.
        retrieval_context: List of retrieved chunks with chunk_id, metadata for citation validation.

    Returns:
        List of ValidationIssue objects (empty if all checks pass).
    """
    issues: list[ValidationIssue] = []

    # Build citation lookup if retrieval context provided
    citation_lookup = {}
    if retrieval_context:
        for chunk in retrieval_context:
            cid = _chunk_value(chunk, "chunk_id") or _chunk_value(chunk, "id")
            if cid:
                citation_lookup[cid] = chunk

    # Validate all requirement sections
    for section_name, requirements in srs.requirement_sections().items():
        for req in requirements:
            issues.extend(_validate_requirement(req, section_name, citation_lookup))

    # Validate double-shall across all text fields
    issues.extend(_validate_double_shall(srs))

    # Validate generic rationales
    issues.extend(_validate_generic_rationales(srs))

    return issues


def _chunk_value(chunk: Any, key: str) -> Any:
    """Return a field from either a retrieved-chunk dict or dataclass."""
    if isinstance(chunk, dict):
        return chunk.get(key)
    return getattr(chunk, key, None)


def _validate_requirement(
    req: Requirement, section: str, citation_lookup: dict
) -> list[ValidationIssue]:
    """Validate a single requirement against quality rules."""
    issues: list[ValidationIssue] = []

    # 1. Double-shall detection in statement
    if _has_double_shall(req.statement):
        issues.append(
            ValidationIssue(
                code="DOUBLE_SHALL",
                severity="error",
                section=section,
                requirement_id=req.id,
                message=f"Requirement statement contains duplicate 'shall': {req.statement[:100]}",
            )
        )

    # 2. Acceptance criteria quality
    issues.extend(_validate_acceptance_criteria(req, section))

    # 3. Numeric constraint provenance
    issues.extend(_validate_numeric_constraints(req, section))

    # 4. Citation validity
    issues.extend(_validate_citations(req, section, citation_lookup))

    # 5. Rationale quality
    issues.extend(_validate_rationale(req, section))

    # 6. Statement starts with "The system shall"
    if not req.statement.lower().startswith("the system shall"):
        issues.append(
            ValidationIssue(
                code="MISSING_SHALL_PREFIX",
                severity="error",
                section=section,
                requirement_id=req.id,
                message="Requirement statement must begin with 'The system shall'",
            )
        )

    return issues


def _validate_acceptance_criteria(req: Requirement, section: str) -> list[ValidationIssue]:
    """Validate acceptance criteria are testable and not paraphrases."""
    issues: list[ValidationIssue] = []
    ac = req.acceptance_criteria.strip()

    if not ac:
        return [
            ValidationIssue(
                code="EMPTY_ACCEPTANCE_CRITERIA",
                severity="error",
                section=section,
                requirement_id=req.id,
                message="Acceptance criteria is empty",
            )
        ]

    # Forbidden patterns
    forbidden_patterns = [
        r"^verify that .+ is implemented\.?$",
        r"^verify that the system .+ is implemented\.?$",
        r"^ensure .+ is implemented\.?$",
        r"^test that .+ is implemented\.?$",
        r"^verify that .+ works\.?$",
        r"^check that .+ is implemented\.?$",
    ]

    ac_lower = ac.lower()
    for pattern in forbidden_patterns:
        if re.match(pattern, ac_lower, re.IGNORECASE):
            issues.append(
                ValidationIssue(
                    code="ACCEPTANCE_CRITERIA_PARAPHRASE",
                    severity="error",
                    section=section,
                    requirement_id=req.id,
                    message=f"Acceptance criteria is a paraphrase of requirement: '{ac[:100]}'",
                )
            )
            break

    # Check for GIVEN-WHEN-THEN format (warning, not error - some may use alternative formats)
    has_gwt = bool(re.search(r"\bgiven\b.*\bwhen\b.*\bthen\b", ac, re.IGNORECASE))
    if not has_gwt:
        issues.append(
            ValidationIssue(
                code="ACCEPTANCE_CRITERIA_FORMAT",
                severity="warning",
                section=section,
                requirement_id=req.id,
                message="Acceptance criteria should use GIVEN-WHEN-THEN format for testability",
            )
        )

    # Check if acceptance criteria is just a restatement
    stmt_words = set(req.statement.lower().split())
    ac_words = set(ac.lower().split())
    overlap = stmt_words & ac_words
    if len(overlap) / max(len(stmt_words), 1) > 0.7:
        issues.append(
            ValidationIssue(
                code="ACCEPTANCE_CRITERIA_HIGH_OVERLAP",
                severity="warning",
                section=section,
                requirement_id=req.id,
                message="Acceptance criteria has high word overlap with requirement statement",
            )
        )

    return issues


def _validate_numeric_constraints(req: Requirement, section: str) -> list[ValidationIssue]:
    """Detect unsupported numeric constraints in requirement statement and rationale."""
    issues: list[ValidationIssue] = []

    # Common invented numeric patterns
    numeric_patterns = [
        (r"\b\d+\s*(?:ms|milliseconds?|seconds?|s)\b", "response time / latency"),
        (r"\b99\.9\d?%\b", "uptime percentage"),
        (
            r"\b\d{4,}\s*(?:connections?|users?|requests?|TPS|RPS)\b",
            "connection/throughput count",
        ),
        (r"\b\d{1,3}%\s*(?:scalability|capacity|utilization)\b", "scalability percentage"),
        (
            r"\b\d+\s*(?:hours?|days?|weeks?)\s*"
            r"(?:patch|update|retention|backup|rotation)\b",
            "time deadline",
        ),
        (r"\b(?:256|128|192|512)\s*-?\s*bit\b", "encryption key size"),
        (r"\b\d+\s*(?:MB|GB|TB)\s*(?:per\s+)?(?:day|hour|month)\b", "data volume"),
    ]

    text_to_check = f"{req.statement} {req.rationale}"

    for pattern, desc in numeric_patterns:
        matches = re.finditer(pattern, text_to_check, re.IGNORECASE)
        for match in matches:
            # Check if rationale explains the provenance
            rationale_lower = req.rationale.lower()
            has_provenance = any(
                keyword in rationale_lower
                for keyword in [
                    "user specified",
                    "user requirement",
                    "clarification",
                    "from user",
                    "retrieved",
                    "source",
                    "document",
                    "standard",
                    "guideline",
                    "assumption",
                    "assumed",
                    "estimated",
                    "assumption requiring",
                ]
            )

            if not has_provenance:
                issues.append(
                    ValidationIssue(
                        code="UNSUPPORTED_NUMERIC_CONSTRAINT",
                        severity="error",
                        section=section,
                        requirement_id=req.id,
                        message=(
                            f"Unsupported numeric constraint detected ({desc}): "
                            f"'{match.group()}' must be USER_SPECIFIED, "
                            "RAG_SUPPORTED (with citation), or "
                            "ASSUMPTION_REQUIRING_CONFIRMATION"
                        ),
                    )
                )

    return issues


def _validate_citations(
    req: Requirement, section: str, citation_lookup: dict
) -> list[ValidationIssue]:
    """Validate that all citations resolve to actual retrieved chunks."""
    issues: list[ValidationIssue] = []

    for ref in req.source_references:
        if not ref.source_id:
            issues.append(
                ValidationIssue(
                    code="CITATION_MISSING_SOURCE_ID",
                    severity="error",
                    section=section,
                    requirement_id=req.id,
                    message="Citation missing source_id",
                )
            )
            continue

        if citation_lookup and ref.source_id not in citation_lookup:
            issues.append(
                ValidationIssue(
                    code="CITATION_INVALID_SOURCE_ID",
                    severity="error",
                    section=section,
                    requirement_id=req.id,
                    message=f"Citation source_id '{ref.source_id}' not found in retrieved chunks",
                )
            )

        # Check required fields
        if not ref.document_title:
            issues.append(
                ValidationIssue(
                    code="CITATION_MISSING_TITLE",
                    severity="warning",
                    section=section,
                    requirement_id=req.id,
                    message=f"Citation {ref.source_id} missing document_title",
                )
            )

    return issues


def _validate_rationale(req: Requirement, section: str) -> list[ValidationIssue]:
    """Validate rationale is specific and not generic."""
    issues: list[ValidationIssue] = []

    generic_phrases = [
        "generated from the project context by the local model",
        "generated from project context",
        "by the local model",
        "required by the project context",
        "based on the project context",
        "derived from the project context",
    ]

    rationale_lower = req.rationale.lower()
    for phrase in generic_phrases:
        if phrase in rationale_lower:
            issues.append(
                ValidationIssue(
                    code="GENERIC_RATIONALE",
                    severity="error",
                    section=section,
                    requirement_id=req.id,
                    message=f"Rationale uses forbidden generic phrase: '{phrase}'",
                )
            )
            break

    # Check minimum length and specificity
    if len(req.rationale.strip()) < 20:
        issues.append(
            ValidationIssue(
                code="RATIONALE_TOO_SHORT",
                severity="warning",
                section=section,
                requirement_id=req.id,
                message="Rationale is very short, may lack specificity",
            )
        )

    return issues


def _validate_double_shall(srs: SRSSchema) -> list[ValidationIssue]:
    """Check for double-shall constructions across all text fields."""
    issues: list[ValidationIssue] = []

    # Check requirement statements
    for section_name, requirements in srs.requirement_sections().items():
        for req in requirements:
            if _has_double_shall(req.statement):
                issues.append(
                    ValidationIssue(
                        code="DOUBLE_SHALL",
                        severity="error",
                        section=section_name,
                        requirement_id=req.id,
                        message=f"Double 'shall' in statement: {req.statement[:120]}",
                    )
                )

            if _has_double_shall(req.rationale):
                issues.append(
                    ValidationIssue(
                        code="DOUBLE_SHALL_RATIONALE",
                        severity="warning",
                        section=section_name,
                        requirement_id=req.id,
                        message="Double 'shall' in rationale",
                    )
                )

            if _has_double_shall(req.acceptance_criteria):
                issues.append(
                    ValidationIssue(
                        code="DOUBLE_SHALL_ACCEPTANCE",
                        severity="warning",
                        section=section_name,
                        requirement_id=req.id,
                        message="Double 'shall' in acceptance criteria",
                    )
                )

    return issues


def _has_double_shall(text: str) -> bool:
    """Detect duplicate 'shall' modal constructions."""
    if not text:
        return False
    # Count 'shall' occurrences
    count = len(re.findall(r"\bshall\b", text, re.IGNORECASE))
    return count > 1


def _validate_generic_rationales(srs: SRSSchema) -> list[ValidationIssue]:
    """Check all rationales for generic forbidden phrases."""
    issues: list[ValidationIssue] = []
    generic_phrases = [
        "generated from the project context by the local model",
        "generated from project context",
        "by the local model",
        "required by the project context",
        "based on the project context",
        "derived from the project context",
    ]

    for section_name, requirements in srs.requirement_sections().items():
        for req in requirements:
            rationale_lower = req.rationale.lower()
            for phrase in generic_phrases:
                if phrase in rationale_lower:
                    issues.append(
                        ValidationIssue(
                            code="GENERIC_RATIONALE",
                            severity="error",
                            section=section_name,
                            requirement_id=req.id,
                            message=f"Rationale uses forbidden generic phrase: '{phrase}'",
                        )
                    )
                    break

    return issues


# --- Test helpers ---


def assert_no_copied_acceptance_criteria(srs: SRSSchema) -> None:
    """Test helper: assert no acceptance criteria are paraphrases."""
    issues = validate_srs_output(srs)
    ac_issues = [i for i in issues if i.code == "ACCEPTANCE_CRITERIA_PARAPHRASE"]
    assert not ac_issues, f"Found copied acceptance criteria: {ac_issues}"


def assert_no_unsupported_numbers(srs: SRSSchema) -> None:
    """Test helper: assert no unsupported numeric constraints."""
    issues = validate_srs_output(srs)
    num_issues = [i for i in issues if i.code == "UNSUPPORTED_NUMERIC_CONSTRAINT"]
    assert not num_issues, f"Found unsupported numeric constraints: {num_issues}"


def assert_no_invalid_citations(srs: SRSSchema, retrieval_context: list[dict]) -> None:
    """Test helper: assert all citations are valid."""
    issues = validate_srs_output(srs, retrieval_context)
    cite_issues = [
        i for i in issues if i.code in ("CITATION_INVALID_SOURCE_ID", "CITATION_MISSING_SOURCE_ID")
    ]
    assert not cite_issues, f"Found invalid citations: {cite_issues}"


def assert_no_double_shall(srs: SRSSchema) -> None:
    """Test helper: assert no double-shall statements."""
    issues = validate_srs_output(srs)
    double_issues = [i for i in issues if i.code.startswith("DOUBLE_SHALL")]
    assert not double_issues, f"Found double-shall: {double_issues}"


def assert_no_generic_rationales(srs: SRSSchema) -> None:
    """Test helper: assert no generic rationales."""
    issues = validate_srs_output(srs)
    generic_issues = [i for i in issues if i.code == "GENERIC_RATIONALE"]
    assert not generic_issues, f"Found generic rationales: {generic_issues}"
