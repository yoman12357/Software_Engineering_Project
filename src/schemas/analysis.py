"""Pydantic schemas for project-description analysis output (Phase 1B).

Every LLM-generated analysis artefact must pass through these typed schemas
before being stored or returned (AGENTS.md §10). Arbitrary dicts must never
cross business logic when a schema exists.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Canonical supported cybersecurity subdomains (SCOPE.md / PRD.md).
SUPPORTED_CATEGORIES: tuple[str, ...] = (
    "CAT-01",  # Network security systems
    "CAT-02",  # Firewalls and network access control
    "CAT-03",  # Intrusion detection and security monitoring
    "CAT-04",  # Identity and access management (IAM)
    "CAT-05",  # Secure web applications and APIs
    "CAT-06",  # VPN and secure remote-access systems
    "CAT-07",  # Security logging and alerting
    "CAT-08",  # Network segmentation and zero-trust-oriented systems
)


def validate_category(value: str) -> str:
    """Ensure an inferred category is one of CAT-01..CAT-08 (FR-011)."""
    if value not in SUPPORTED_CATEGORIES:
        raise ValueError(f"inferred category must be one of {', '.join(SUPPORTED_CATEGORIES)}")
    return value


class ProjectAnalysis(BaseModel):
    """Structured result of analysing an informal project description.

    Mirrors the ``ProjectAnalysis`` JSON from PROMPT_AND_OUTPUT_DESIGN §2.1.
    Validation rules: the five entity arrays must be non-empty and
    ``inferred_categories`` must contain at least one valid CAT-01..CAT-08
    value (PROMPT_AND_OUTPUT_DESIGN deterministic checks / FR-012).
    """

    model_config = ConfigDict(extra="forbid")

    stakeholders: list[str] = Field(min_length=1)
    assets: list[str] = Field(min_length=1)
    users: list[str] = Field(min_length=1)
    constraints: list[str] = Field(min_length=1)
    goals: list[str] = Field(min_length=1)
    inferred_categories: list[str] = Field(min_length=1)
    missing_information: list[str] = Field(default_factory=list)
    project_summary: str = Field(min_length=1)

    @field_validator("inferred_categories", mode="after")
    @classmethod
    def check_categories(cls, value: list[str]) -> list[str]:
        """Reject categories outside CAT-01..CAT-08 and duplicates."""
        seen: set[str] = set()
        for category in value:
            validate_category(category)
            if category in seen:
                raise ValueError(f"duplicate inferred category {category}")
            seen.add(category)
        return value


class ProjectContextCreate(BaseModel):
    """Values used to persist a :class:`ProjectContext` (DATA_MODEL §2.5)."""

    stakeholders: list[str]
    assets: list[str]
    users: list[str]
    constraints: list[str]
    goals: list[str]
    inferred_categories: list[str]
    missing_information: list[str] | None = None


class ProjectContextRead(BaseModel):
    """API representation of a stored project context."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    stakeholders: list[str]
    assets: list[str]
    users: list[str]
    constraints: list[str]
    goals: list[str]
    inferred_categories: list[str]
    missing_information: list[str] | None = None
    enriched_context: dict | None = None
    created_at: datetime
    updated_at: datetime


class AnalysisResponse(BaseModel):
    """Response body for ``POST /projects/{id}/analyse`` (API_CONTRACT §3)."""

    project_id: str
    analysis: ProjectAnalysis
    has_missing_information: bool
    provider: str
    model_name: str
    generated_at: datetime


def utcnow_iso() -> datetime:
    """Return the current UTC time (used for response timestamps)."""
    return datetime.now(UTC)
