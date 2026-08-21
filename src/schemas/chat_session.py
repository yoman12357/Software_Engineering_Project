"""Schemas for local SQLite-backed chat-session persistence."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StoredChatMessage(BaseModel):
    """One message persisted as part of a chat-session snapshot."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=64)
    role: Literal["user", "assistant"]
    content: str = Field(max_length=12_000)
    type: Literal["text", "analysis", "clarification", "generation", "srs", "error"] | None = None
    metadata: dict[str, object] | None = None
    timestamp: datetime


class ChatSessionWrite(BaseModel):
    """Complete replaceable state of a chat session."""

    model_config = ConfigDict(extra="forbid")

    project_id: str | None = None
    name: str = Field(min_length=1, max_length=200)
    messages: list[StoredChatMessage] = Field(default_factory=list, max_length=500)
    stage: Literal["welcome", "analyzing", "clarifying", "generating", "ready", "error"]
    analysis: dict[str, object] | None = None
    clarification_questions: list[object] | None = None
    srs: dict[str, object] | None = None
    srs_version_id: str | None = None
    pending_project_description: str | None = Field(default=None, max_length=12_000)


class ChatSessionUpdate(BaseModel):
    """Mutable sidebar properties for a persisted chat session."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    pinned: bool | None = None


class ChatSessionRead(ChatSessionWrite):
    """Complete persisted chat session returned to the frontend."""

    id: str
    pinned_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ChatSessionListResponse(BaseModel):
    """Ordered collection of persisted chat sessions."""

    sessions: list[ChatSessionRead]
    total: int
