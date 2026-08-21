"""Integration tests for validated conversational chat endpoints."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from src.core.config import Settings
from src.llm.base import LLMRequest, LLMResponse
from src.llm.mock_provider import MockLLMProvider
from src.prompts.chat import GENERAL_CHAT_SYSTEM_PROMPT
from src.schemas.chat import ChatMessage
from src.services.chat_service import ChatService


class RecordingChatProvider(MockLLMProvider):
    """Capture the request used for a general chat completion."""

    last_request: LLMRequest | None = None

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Record and delegate one model request."""
        self.last_request = request
        return super().generate(request)


def test_chat_completion_returns_visible_validated_answer(client: TestClient) -> None:
    """A normal prompt returns a non-empty schema-validated assistant response."""
    response = client.post(
        "/api/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "What is network segmentation?"}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["content"]
    assert body["model_name"] == "cybersrs-mock-1b"
    assert body["rag_enabled"] is False
    assert body["citations"] == []
    assert body["warnings"]


def test_chat_greeting_returns_immediately_without_rag(client: TestClient) -> None:
    """A greeting avoids unnecessary retrieval and model inference."""
    response = client.post(
        "/api/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hi!"}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert "CyberSRS" in body["content"]
    assert body["rag_enabled"] is False
    assert body["citations"] == []
    assert body["warnings"] == []


def test_chat_returns_current_india_time_without_rag(client: TestClient) -> None:
    """Current India clock questions use the server clock, including common typos."""
    response = client.post(
        "/api/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "What is the fdate and time of India?"}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert "IST (UTC+05:30)" in body["content"]
    assert body["rag_enabled"] is False
    assert body["citations"] == []
    assert body["warnings"] == []


def test_india_and_pacific_time_share_one_instant_and_cross_dates() -> None:
    """IST/PDT conversion handles the 12:30 offset and previous-day rollover."""
    fixed_utc = datetime(2026, 8, 20, 22, 24, 25, tzinfo=UTC)
    question = "What is the current date and time in India and USA PDT?"
    reply = ChatService._real_time_reply(
        question,
        [ChatMessage(role="user", content=question)],
        now_utc=fixed_utc,
    )

    assert reply is not None
    assert "Friday, 21 August 2026 at 03:54:25 AM" in reply
    assert "Thursday, 20 August 2026 at 03:24:25 PM" in reply
    assert "PDT (UTC-07:00)" in reply
    assert "12 hours 30 minutes ahead" in reply


def test_pdt_followup_uses_previous_clock_question(client: TestClient) -> None:
    """A terse PDT follow-up is answered by the clock utility, not the LLM."""
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "messages": [
                {"role": "user", "content": "What is the date and time in India?"},
                {"role": "assistant", "content": "The India time was shown."},
                {"role": "user", "content": "PDT"},
            ]
        },
    )

    assert response.status_code == 200
    assert "U.S. Pacific" in response.json()["content"]
    assert "UTC-07:00" in response.json()["content"]


def test_general_chat_recognizes_jakes_resume_variants_without_rag() -> None:
    """Named-template variants resolve locally instead of relying on model recall."""
    provider = RecordingChatProvider()
    service = ChatService(provider, Settings(_env_file=None, rag_enabled=False))
    for query in (
        "what is jaek resume format",
        "What is Jake's Resume format?",
        "What is Jake’s Resume format?",
    ):
        response = service.complete(
            [ChatMessage(role="user", content=query)],
            is_project_description=False,
        )

        assert "Jake's Resume" in response.content
        assert "LaTeX" in response.content
        assert "Education" in response.content
        assert response.rag_enabled is False
    assert provider.last_request is None


def test_other_general_chat_uses_non_rag_system_prompt() -> None:
    """Ordinary questions use a prompt that does not impose retrieval grounding."""
    provider = RecordingChatProvider()
    service = ChatService(provider, Settings(_env_file=None, rag_enabled=False))
    service.complete(
        [ChatMessage(role="user", content="Explain the difference between a list and a tuple")],
        is_project_description=False,
    )

    assert provider.last_request is not None
    assert provider.last_request.system_prompt == GENERAL_CHAT_SYSTEM_PROMPT
    assert "retrieved_knowledge" not in provider.last_request.user_content


def test_chat_completion_detects_project_description(client: TestClient) -> None:
    """A cybersecurity proposal is marked for later SRS workflow handoff."""
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "I want to build a firewall and monitoring system for a campus network."
                    ),
                }
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["is_project_description"] is True


def test_intent_separates_description_from_generation_command(client: TestClient) -> None:
    """Description capture and explicit generation remain separate deterministic intents."""
    description = client.post(
        "/api/v1/chat/intent",
        json={"message": "I want to build a zero trust network gateway."},
    )
    generation = client.post(
        "/api/v1/chat/intent",
        json={"message": "Generate an SRS for this project."},
    )

    assert description.status_code == 200
    assert description.json()["intent"] == "project_description"
    assert generation.status_code == 200
    assert generation.json()["intent"] == "srs_generation"


def test_clarifying_stage_routes_numbered_answers_deterministically(
    client: TestClient,
) -> None:
    """Composer answer sets enter clarification handling without an LLM call."""
    response = client.post(
        "/api/v1/chat/intent",
        json={
            "message": "1. 500 users\n2. Azure AD\n3. 99.9% uptime",
            "workflow_stage": "clarifying",
        },
    )
    assert response.status_code == 200
    assert response.json()["intent"] == "clarification"

    general = client.post(
        "/api/v1/chat/intent",
        json={
            "message": "ask: why is this information needed?",
            "workflow_stage": "clarifying",
        },
    )
    assert general.status_code == 200
    assert general.json()["intent"] == "general_question"


def test_detailed_srs_document_starts_guided_workflow(client: TestClient) -> None:
    """A pasted project SRS is not misclassified as an ordinary chat question."""
    document = """
    # Software Requirements Specification (SRS): Secure Zero-Trust VPN Gateway

    ## Overview
    This document outlines requirements for building a secure zero-trust VPN gateway
    for a mid-size company with MFA, device attestation, and audit logging.

    ## Functional Requirements
    The system shall validate user identity and device posture before access.

    ## Scope
    The gateway shall provide application-level access using least privilege.

    ## Architecture
    Integrate an identity provider, policy engine, gateway, and audit service.
    """
    response = client.post(
        "/api/v1/chat/intent",
        json={"message": document},
    )

    assert response.status_code == 200
    assert response.json()["intent"] == "srs_project_request"


def test_compact_generate_srs_request_with_project_context_starts_workflow(
    client: TestClient,
) -> None:
    """A one-message generation request retains its VPN description."""
    response = client.post(
        "/api/v1/chat/intent",
        json={"message": "Generate an SRS for a secure zero-trust VPN gateway with MFA."},
    )
    assert response.status_code == 200
    assert response.json()["intent"] == "srs_project_request"


def test_srs_definition_question_remains_general_chat(client: TestClient) -> None:
    """Asking what SRS means does not accidentally create a project."""
    response = client.post(
        "/api/v1/chat/intent",
        json={"message": "What is an SRS for a VPN project?"},
    )
    assert response.status_code == 200
    assert response.json()["intent"] == "general_question"


def test_chat_rejects_missing_user_message(client: TestClient) -> None:
    """Assistant-only history is rejected with the standard structured error envelope."""
    response = client.post(
        "/api/v1/chat/completions",
        json={"messages": [{"role": "assistant", "content": "How can I help?"}]},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "bad_request"
