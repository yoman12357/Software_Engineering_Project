"""Pydantic request/response schemas for the Project resource."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProjectCreate(BaseModel):
    """Request body for creating a project.

    ``name`` is required and limited to 200 characters (SEC-010). The
    ``description`` is required and must be at least 10 characters after
    trimming (API_CONTRACT). Unknown keys are rejected (SEC-026).
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=10)

    @field_validator("name", "description")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be empty or whitespace-only")
        return stripped


class ProjectUpdate(BaseModel):
    """Request body for partial updates of a project.

    At least one field is required. Fields that are absent (None) are not
    updated. ``description`` follows the same rules as creation.
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=10)

    @field_validator("name", "description")
    @classmethod
    def strip_whitespace(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be empty or whitespace-only")
        return stripped

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "ProjectUpdate":
        """Reject an empty update body (no fields provided)."""
        if self.name is None and self.description is None:
            raise ValueError("at least one of 'name' or 'description' must be provided")
        return self


class ProjectRead(BaseModel):
    """Full project representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    status: str
    inferred_categories: list[str]
    created_at: datetime
    updated_at: datetime


class ProjectListItem(BaseModel):
    """Compact project representation used in list responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: str
    inferred_categories: list[str]
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """List of projects with a total count."""

    projects: list[ProjectListItem]
    total: int


def generate_uuid() -> str:
    """Return a fresh UUID v4 string for entity primary keys."""
    return str(uuid.uuid4())
