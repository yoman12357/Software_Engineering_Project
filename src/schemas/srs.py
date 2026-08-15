"""Pydantic schemas for the structured SRS document (Phase 1C).

The canonical SRS representation is validated structured JSON (ADR-0003). PDF
rendering, the frontend, and user editing all consume this validated structure;
it is never replaced by Markdown or PDF as the source of truth.

Section layout follows the Phase 1C milestone's documented section list and
the requirement format from PROMPT_AND_OUTPUT_DESIGN §4.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# --- Enums ----------------------------------------------------------------


class RequirementCategory(StrEnum):
    """Category of a generated requirement."""

    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    SECURITY = "security"
    DATA = "data"
    NETWORK = "network"


class Priority(StrEnum):
    """Requirement priority per MoSCoW (DATA_MODEL §2.7)."""

    MUST = "must"
    SHOULD = "should"
    COULD = "could"


class Confidence(StrEnum):
    """Model self-assessed confidence (PROMPT_AND_OUTPUT_DESIGN §4)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Severity(StrEnum):
    """Threat severity (DATA_MODEL §2.9)."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValidationSeverity(StrEnum):
    """Severity of a deterministic validation issue."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# --- Requirement identifiers ----------------------------------------------

# Requirement IDs use an alphabetic prefix (e.g. FR, NFR, SEC, DATA, NET)
# followed by a three-digit sequence number. The prefix length is 2-4 to cover
# FR/NFR/SEC/DATA/NET (DATA_MODEL §2.7 pattern, extended for the milestone's
# data and network requirement categories).
_REQUIREMENT_ID_PATTERN = re.compile(r"^(?:[A-Z]{2,4})-\d{3}$")


def validate_requirement_id(value: str) -> str:
    """Ensure a requirement ID follows the documented pattern (DATA_MODEL §2.7)."""
    if not _REQUIREMENT_ID_PATTERN.match(value):
        raise ValueError(
            "requirement id must follow the pattern 'FR-001', 'SEC-012', "
            "'DATA-001', 'NET-001', etc."
        )
    return value


def _non_empty_strings(value: list[str]) -> list[str]:
    """Reject arrays containing empty or blank strings."""
    if any(not item.strip() for item in value):
        raise ValueError("array items must not be empty or whitespace-only")
    return value


# --- Reusable components ---------------------------------------------------


class SourceReference(BaseModel):
    """A retrieved-chunk citation on a requirement.

    RAG does not exist yet (Phase 1C), so this list must remain empty; it is
    defined so Phase 4 can populate it without changing the schema.
    """

    model_config = ConfigDict(extra="forbid")

    source_id: str
    document_title: str
    section_heading: str | None = None
    relevance_score: float = Field(ge=0.0, le=1.0)


class Requirement(BaseModel):
    """A single functional, non-functional, security, data, or network
    requirement (PROMPT_AND_OUTPUT_DESIGN §4 / DATA_MODEL §2.7)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    category: RequirementCategory
    title: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    priority: Priority = Priority.MUST
    acceptance_criteria: str = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(default_factory=list)
    confidence: Confidence = Confidence.MEDIUM
    user_confirmed: bool = False

    @field_validator("id")
    @classmethod
    def check_id(cls, value: str) -> str:
        """Validate the requirement ID pattern."""
        return validate_requirement_id(value)

    @field_validator("statement")
    @classmethod
    def check_statement(cls, value: str) -> str:
        """Require testable 'shall' language for statements."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("statement must not be empty")
        if not stripped.lower().startswith("the system shall"):
            raise ValueError(
                "statement should begin with 'The system shall' or equivalent testable language"
            )
        return stripped


class AcceptanceCriterion(BaseModel):
    """A specific acceptance criterion (DATA_MODEL §2.8)."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(pattern=r"^AC-\d{3}$")
    description: str = Field(min_length=1)
    related_requirement_ids: list[str] = Field(default_factory=list)


class Mitigation(BaseModel):
    """A mitigation strategy for a threat (DATA_MODEL §2.10)."""

    model_config = ConfigDict(extra="forbid")

    mitigation_id: str = Field(pattern=r"^MIT-\d{3}$")
    description: str = Field(min_length=1)
    related_requirement_ids: list[str] = Field(default_factory=list)


class Threat(BaseModel):
    """A threat identified in the threat model (DATA_MODEL §2.9)."""

    model_config = ConfigDict(extra="forbid")

    threat_id: str = Field(pattern=r"^THR-\d{3}$")
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: str | None = None  # STRIDE category or similar
    severity: Severity = Severity.MEDIUM
    affected_assets: list[str] = Field(default_factory=list)
    mitigations: list[Mitigation] = Field(default_factory=list)


class ArchitectureComponent(BaseModel):
    """A component in the high-level system architecture."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    responsibilities: list[str] = Field(min_length=1)


class ValidationIssue(BaseModel):
    """A single deterministic validation finding."""

    model_config = ConfigDict(extra="forbid")

    issue_id: str = Field(default="", pattern=r"^VAL-\d{3}$")
    severity: ValidationSeverity = ValidationSeverity.WARNING
    section: str = Field(min_length=1)
    requirement_id: str | None = None
    message: str = Field(min_length=1)


class ValidationReport(BaseModel):
    """Result of deterministic SRS validation (FR-050..FR-054)."""

    model_config = ConfigDict(extra="forbid")

    overall_score: int = Field(ge=0, le=100)
    issues: list[ValidationIssue] = Field(default_factory=list)


# --- The full SRS document --------------------------------------------------


class SRSMetadata(BaseModel):
    """Document-level metadata (DATA_MODEL §3 / PDF_AND_REPORT_DESIGN §3)."""

    model_config = ConfigDict(extra="forbid")

    project_name: str = Field(min_length=1)
    version: int = Field(ge=1)
    generated_at: datetime
    model_name: str = Field(min_length=1)
    adapter_name: str | None = None
    inferred_categories: list[str] = Field(default_factory=list)


class ProjectOverview(BaseModel):
    """Executive summary of the project being specified."""

    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    context: str = Field(min_length=1)


class Scope(BaseModel):
    """What is included in and excluded from the SRS."""

    model_config = ConfigDict(extra="forbid")

    in_scope: list[str] = Field(min_length=1)
    out_of_scope: list[str] = Field(default_factory=list)


class ArchitectureSummary(BaseModel):
    """High-level system architecture description."""

    model_config = ConfigDict(extra="forbid")

    overview: str = Field(min_length=1)
    components: list[ArchitectureComponent] = Field(min_length=1)
    data_flows: list[str] = Field(default_factory=list)
    deployment_notes: str = Field(default="")


class TestingRecommendation(BaseModel):
    """A testing recommendation for the project."""

    model_config = ConfigDict(extra="forbid")

    recommendation_id: str = Field(pattern=r"^TEST-\d{3}$")
    description: str = Field(min_length=1)
    type: str = Field(min_length=1)  # unit | integration | system | security | performance
    related_requirement_ids: list[str] = Field(default_factory=list)


class Risk(BaseModel):
    """A project risk recorded in the SRS."""

    model_config = ConfigDict(extra="forbid")

    risk_id: str = Field(pattern=r"^RISK-\d{3}$")
    description: str = Field(min_length=1)
    likelihood: str = Field(min_length=1)
    impact: str = Field(min_length=1)
    mitigation: str = Field(default="")


class SRSSchema(BaseModel):
    """The complete structured Software Requirements Specification.

    Sections follow the Phase 1C milestone's documented list. ``references``
    and requirement ``source_references`` remain empty because RAG does not
    exist yet (Phase 1C rule: never invent external citations).
    """

    model_config = ConfigDict(extra="forbid")

    metadata: SRSMetadata
    project_overview: ProjectOverview
    scope: Scope
    assumptions: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(min_length=1)
    user_roles: list[str] = Field(min_length=1)
    functional_requirements: list[Requirement] = Field(min_length=1)
    non_functional_requirements: list[Requirement] = Field(default_factory=list)
    security_requirements: list[Requirement] = Field(default_factory=list)
    data_requirements: list[Requirement] = Field(default_factory=list)
    network_requirements: list[Requirement] = Field(default_factory=list)
    architecture_summary: ArchitectureSummary
    threats: list[Threat] = Field(default_factory=list)
    mitigations: list[Mitigation] = Field(default_factory=list)
    testing_strategy: list[TestingRecommendation] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    references: list[dict] = Field(default_factory=list)  # empty until RAG exists
    validation_report: ValidationReport | None = None
    generation_metadata: dict | None = None

    @field_validator("assumptions", "stakeholders", "user_roles", "unresolved_questions")
    @classmethod
    def non_blank_strings(cls, value: list[str]) -> list[str]:
        """Reject blank entries in string-list sections."""
        return _non_empty_strings(value)

    @model_validator(mode="after")
    def check_unique_requirement_ids(self) -> SRSSchema:
        """Reject duplicate requirement IDs across all requirement sections
        (FR-047 / duplicate-ID detection)."""
        seen: dict[str, str] = {}
        for section, requirements in self.requirement_sections().items():
            for requirement in requirements:
                previous = seen.get(requirement.id)
                if previous is not None:
                    raise ValueError(
                        f"duplicate requirement id {requirement.id!r} "
                        f"in sections {previous!r} and {section!r}"
                    )
                seen[requirement.id] = section
        return self

    def requirement_sections(self) -> dict[str, list[Requirement]]:
        """Return all requirement-bearing sections keyed by section name."""
        return {
            "functional_requirements": self.functional_requirements,
            "non_functional_requirements": self.non_functional_requirements,
            "security_requirements": self.security_requirements,
            "data_requirements": self.data_requirements,
            "network_requirements": self.network_requirements,
        }


class SRSVersionRead(BaseModel):
    """API representation of a stored SRSVersion (DATA_MODEL §2.6)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    version_number: int
    status: str
    quality_score: float | None = None
    created_at: datetime
    srs: SRSSchema | None = None


class SRSVersionSummary(BaseModel):
    """Compact version summary used in list responses."""

    id: str
    version_number: int
    quality_score: float | None = None
    status: str
    created_at: datetime


class SRSVersionListResponse(BaseModel):
    """List of SRS versions for a project."""

    project_id: str
    versions: list[SRSVersionSummary]


class SRSGenerationResponse(BaseModel):
    """Response body for ``POST /projects/{id}/srs/generate``."""

    project_id: str
    version_id: str
    version_number: int
    status: str


class SRSSection(BaseModel):
    """Identifies a section for validation or editing."""

    model_config = ConfigDict(extra="forbid")

    section: str
    requirement_id: str
    field: str
    new_value: str


class SRSEditRequest(BaseModel):
    """Request body for ``PUT /projects/{id}/srs/versions/{vid}``."""

    model_config = ConfigDict(extra="forbid")

    updates: list[SRSSection] = Field(min_length=1)


class SRSValidationResponse(BaseModel):
    """Response body for the validate endpoint."""

    srs_version_id: str
    overall_score: int
    issues: list[ValidationIssue]
