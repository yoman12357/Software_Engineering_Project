"""Conversational assistant routes backed by the provider-independent LLM service."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ...core.config import Settings
from ...core.exceptions import BadRequestError
from ...llm.base import LLMProvider
from ...schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    IntentClassificationRequest,
    IntentClassificationResponse,
    IntentType,
    SRSEditChatRequest,
    SRSEditChatResponse,
)
from ...schemas.chat_session import (
    ChatSessionListResponse,
    ChatSessionRead,
    ChatSessionUpdate,
    ChatSessionWrite,
)
from ...schemas.srs import SRSEditRequest, SRSSection
from ...services.chat_service import ChatService
from ...services.chat_session_service import ChatSessionService
from ...services.srs_generation_service import SRSGenerationService
from ..dependencies import (
    enforce_request_body_size,
    get_app_settings,
    get_db,
    get_general_llm_provider,
    get_srs_llm_provider,
)

router = APIRouter(tags=["chat"])


@router.get("/chat/sessions", response_model=ChatSessionListResponse)
def list_chat_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ChatSessionListResponse:
    """List SQLite-backed chat sessions in sidebar order."""
    sessions = ChatSessionService(db).list_recent(limit)
    return ChatSessionListResponse(sessions=sessions, total=len(sessions))


@router.put("/chat/sessions/{session_id}", response_model=ChatSessionRead)
def save_chat_session(
    session_id: str,
    payload: ChatSessionWrite,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_request_body_size),
) -> ChatSessionRead:
    """Create or replace a complete chat-session snapshot."""
    return ChatSessionService(db).save(session_id, payload)


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionRead)
def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> ChatSessionRead:
    """Restore one complete chat-session snapshot."""
    return ChatSessionService(db).get(session_id)


@router.patch("/chat/sessions/{session_id}", response_model=ChatSessionRead)
def update_chat_session(
    session_id: str,
    payload: ChatSessionUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(enforce_request_body_size),
) -> ChatSessionRead:
    """Rename or change the pinned state of a chat session."""
    return ChatSessionService(db).update(session_id, payload)


@router.delete(
    "/chat/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Permanently delete a chat session and all of its messages."""
    ChatSessionService(db).delete(session_id)


_PROJECT_ACTIONS = (
    "i want to build",
    "i want to create",
    "i need a",
    "we need",
    "we want",
    "create a",
    "implement a",
    "design a",
    "develop a",
    "set up a",
    "deploy a",
    "build a",
    "make a",
    "building a",
    "requirements for",
    "specification for",
    "document outlines",
)
_PROJECT_NOUNS = (
    "firewall",
    "vpn",
    "gateway",
    "siem",
    "ids",
    "ips",
    "zero trust",
    "monitoring system",
    "intrusion detection",
    "security platform",
    "network",
    "infrastructure",
    "identity management",
    "access management",
    "secure api",
    "api security",
    "secure web",
    "logging platform",
    "edr",
    "xdr",
    "dlp",
    "waf",
)
_SRS_DOCUMENT_TERMS = (
    "software requirements specification",
    "requirements specification",
    "requirements document",
    "srs document",
    "srs for",
    "functional requirements",
    "non-functional requirements",
)
_SRS_REQUEST_ACTIONS = (
    "generate",
    "create",
    "write",
    "draft",
    "prepare",
    "make",
    "need",
    "want",
)


def _has_project_domain(text: str) -> bool:
    """Return whether text names a supported cybersecurity project domain."""
    return any(noun in text for noun in _PROJECT_NOUNS) or any(
        term in text
        for term in (
            "cybersecurity",
            "identity and access",
            "device attestation",
            "audit logging",
            "zero-trust",
            "zero trust",
        )
    )


def detect_project_description(text: str) -> bool:
    """Return whether text looks like a cybersecurity project proposal."""
    lowered = " ".join(text.lower().split())
    has_action = any(action in lowered for action in _PROJECT_ACTIONS)
    has_structured_detail = len(lowered) >= 180 and any(
        marker in lowered
        for marker in (
            "overview",
            "scope",
            "functional requirements",
            "non-functional requirements",
            "security architecture",
            "stakeholders",
        )
    )
    return _has_project_domain(lowered) and (has_action or has_structured_detail)


def detect_srs_project_request(text: str) -> bool:
    """Return whether one message requests SRS work and contains project context."""
    lowered = " ".join(text.lower().split())
    has_srs_signal = bool(re.search(r"\bsrs\b", lowered)) or any(
        term in lowered for term in _SRS_DOCUMENT_TERMS
    )
    if not has_srs_signal or not _has_project_domain(lowered):
        return False
    is_definition_question = bool(
        re.match(r"^(what is|what does|define|explain)\b", lowered) and len(lowered) < 160
    )
    if is_definition_question:
        return False
    has_request_action = any(action in lowered for action in _SRS_REQUEST_ACTIONS)
    has_structured_document = len(lowered) >= 180 and any(
        marker in lowered
        for marker in ("overview", "functional requirements", "scope", "architecture")
    )
    return has_request_action or has_structured_document


def classify_chat_intent(
    message: str,
    has_srs: bool,
    workflow_stage: str | None = None,
) -> IntentType:
    """Classify explicit workflow commands without invoking the LLM."""
    lowered = " ".join(message.lower().split())
    generation_phrases = (
        "generate srs",
        "generate an srs",
        "create srs",
        "create an srs",
        "start srs",
        "make srs",
        "build srs",
    )
    if has_srs and re.search(
        r"\b(change|modify|update|edit|add|remove|delete)\b|\b(FR|NFR|SEC)-\d+\b",
        message,
        re.IGNORECASE,
    ):
        return "srs_modification"
    if lowered.startswith(("answer:", "skip this", "skip question")):
        return "clarification"
    if detect_srs_project_request(message):
        return "srs_project_request"
    if any(phrase in lowered for phrase in generation_phrases):
        return "srs_generation"
    if workflow_stage == "clarifying":
        if lowered.startswith(("ask:", "question:")):
            return "general_question"
        return "clarification"
    if detect_project_description(message):
        return "project_description"
    return "general_question"


@router.post("/chat/completions", response_model=ChatCompletionResponse)
def chat_completion(
    request: ChatCompletionRequest,
    provider: LLMProvider = Depends(get_general_llm_provider),
    settings: Settings = Depends(get_app_settings),
    _: None = Depends(enforce_request_body_size),
) -> ChatCompletionResponse:
    """Return a validated conversational answer with verified local citations."""
    last_user_message = next(
        (message.content for message in reversed(request.messages) if message.role == "user"),
        None,
    )
    if last_user_message is None:
        raise BadRequestError("The conversation must contain a user message.")
    return ChatService(provider, settings).complete(
        request.messages,
        is_project_description=detect_project_description(last_user_message),
    )


@router.post("/chat/intent", response_model=IntentClassificationResponse)
def classify_intent(request: IntentClassificationRequest) -> IntentClassificationResponse:
    """Return the deterministic workflow intent for one user message."""
    intent = classify_chat_intent(
        request.message,
        request.has_srs,
        request.workflow_stage,
    )
    return IntentClassificationResponse(
        intent=intent,
        confidence=0.95 if intent != "general_question" else 0.8,
        extracted_data={},
    )


def _extract_requirement_update(instruction: str) -> tuple[str, str] | None:
    """Extract an existing requirement ID and replacement statement."""
    match = re.search(
        r"\b(?:change|update|modify|edit)\s+((?:FR|NFR|SEC)-\d+)\s+"
        r"(?:to|with)\s+(.+)",
        instruction,
        re.IGNORECASE,
    )
    if match is None:
        return None
    requirement_id = match.group(1).upper()
    prefix, number = requirement_id.split("-", maxsplit=1)
    return f"{prefix}-{int(number):03d}", match.group(2).strip()


@router.post("/chat/srs-edit", response_model=SRSEditChatResponse)
def edit_srs_via_chat(
    request: SRSEditChatRequest,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_srs_llm_provider),
    settings: Settings = Depends(get_app_settings),
    _: None = Depends(enforce_request_body_size),
) -> SRSEditChatResponse:
    """Apply a narrowly scoped natural-language update through the SRS service."""
    extracted = _extract_requirement_update(request.instruction)
    if extracted is None:
        return SRSEditChatResponse(
            success=False,
            message="Use a command such as: change FR-001 to The system shall ...",
        )
    requirement_id, new_statement = extracted
    section = {
        "FR": "functional_requirements",
        "NFR": "non_functional_requirements",
        "SEC": "security_requirements",
    }[requirement_id.split("-", maxsplit=1)[0]]
    updated = SRSGenerationService(db, provider, settings).edit_version(
        request.project_id,
        request.version_id,
        SRSEditRequest(
            updates=[
                SRSSection(
                    section=section,
                    requirement_id=requirement_id,
                    field="statement",
                    new_value=new_statement,
                )
            ]
        ),
    )
    return SRSEditChatResponse(
        success=True,
        message=f"Successfully updated {requirement_id}.",
        updated_srs=updated.srs.model_dump(mode="json") if updated.srs else None,
    )
