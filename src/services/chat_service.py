"""Validated, provider-independent conversational chat with optional local RAG."""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from ..core.config import Settings
from ..llm.base import LLMProvider, LLMRequest, LLMTask
from ..prompts.chat import GENERAL_CHAT_SYSTEM_PROMPT, RAG_CHAT_SYSTEM_PROMPT
from ..rag.chromadb_client import create_chromadb_client
from ..rag.embedding_provider import create_embedding_provider
from ..rag.retrieval import RetrievedChunk, create_retriever
from ..schemas.chat import (
    ChatCitation,
    ChatCompletionResponse,
    ChatMessage,
    ChatModelOutput,
)

logger = logging.getLogger(__name__)

_QUICK_REPLIES = {
    "hi": (
        "Hello! I'm CyberSRS. Ask me a cybersecurity or networking question, "
        "or describe a project and I can help you generate its SRS."
    ),
    "hello": (
        "Hello! I'm CyberSRS. Ask me a cybersecurity or networking question, "
        "or describe a project and I can help you generate its SRS."
    ),
    "hey": (
        "Hello! I'm CyberSRS. Ask me a cybersecurity or networking question, "
        "or describe a project and I can help you generate its SRS."
    ),
    "thanks": "You're welcome. What would you like to work on next?",
    "thank you": "You're welcome. What would you like to work on next?",
}

_CYBERSECURITY_TERMS = (
    "access control",
    "api security",
    "authentication",
    "authorization",
    "compliance",
    "cyber",
    "data protection",
    "encryption",
    "firewall",
    "ids",
    "ips",
    "iso 27001",
    "malware",
    "network",
    "nist",
    "owasp",
    "phishing",
    "ransomware",
    "requirement",
    "risk",
    "secure",
    "security",
    "siem",
    "srs",
    "threat",
    "vulnerability",
    "vpn",
    "zero trust",
)


def sanitize_chat_text(value: str) -> str:
    """Remove control characters while preserving ordinary Unicode and whitespace."""
    normalized = unicodedata.normalize("NFKC", value)
    return "".join(
        character
        for character in normalized
        if character in "\n\t" or not unicodedata.category(character).startswith("C")
    ).strip()


class ChatService:
    """Generate schema-validated conversational answers with verified citations."""

    def __init__(self, provider: LLMProvider, settings: Settings) -> None:
        self._provider = provider
        self._settings = settings

    def complete(
        self,
        messages: list[ChatMessage],
        *,
        is_project_description: bool,
    ) -> ChatCompletionResponse:
        """Return one answer using recent chat history and optional retrieved knowledge."""
        latest_question = next(
            sanitize_chat_text(message.content)
            for message in reversed(messages)
            if message.role == "user"
        )
        quick_reply = self._quick_reply(latest_question)
        if quick_reply is not None:
            return ChatCompletionResponse(
                content=quick_reply,
                is_project_description=is_project_description,
                model_name=self._provider.model_name,
                rag_enabled=False,
                citations=[],
                warnings=[],
            )
        known_topic_reply = self._known_topic_reply(latest_question)
        if known_topic_reply is not None:
            return ChatCompletionResponse(
                content=known_topic_reply,
                is_project_description=is_project_description,
                model_name=self._provider.model_name,
                rag_enabled=False,
                citations=[],
                warnings=[],
            )
        real_time_reply = self._real_time_reply(latest_question, messages)
        if real_time_reply is not None:
            return ChatCompletionResponse(
                content=real_time_reply,
                is_project_description=is_project_description,
                model_name=self._provider.model_name,
                rag_enabled=False,
                citations=[],
                warnings=[],
            )
        retrieved_chunks, warnings = self._retrieve(latest_question)
        prompt_payload: dict[str, object] = {
            "conversation": [
                {
                    "role": message.role,
                    "content": self._normalize_query_aliases(sanitize_chat_text(message.content)),
                }
                for message in messages[-12:]
            ],
            "current_time_context": self._current_time_context(),
        }
        if retrieved_chunks:
            prompt_payload["retrieved_knowledge"] = [
                {
                    "chunk_id": chunk.chunk_id,
                    "document_title": str(chunk.metadata.get("document_title", "")),
                    "page_or_section": self._page_or_section(chunk),
                    "relevance_score": round(chunk.relevance_score, 4),
                    "content": chunk.text[: self._settings.rag_max_chunk_chars],
                }
                for chunk in retrieved_chunks
            ]
        request = LLMRequest(
            task=LLMTask.CHAT,
            system_prompt=(
                RAG_CHAT_SYSTEM_PROMPT if retrieved_chunks else GENERAL_CHAT_SYSTEM_PROMPT
            ),
            user_content=json.dumps(prompt_payload, ensure_ascii=False),
            response_schema=ChatModelOutput,
        )
        generated = self._provider.generate_with_validation(request, ChatModelOutput)
        citations = self._validate_citations(generated.cited_source_ids, retrieved_chunks)
        if retrieved_chunks and not citations:
            warnings.append("Retrieved knowledge was available, but the answer did not cite it.")

        return ChatCompletionResponse(
            content=generated.answer,
            is_project_description=is_project_description,
            model_name=self._provider.model_name,
            rag_enabled=bool(retrieved_chunks),
            citations=citations,
            warnings=warnings,
        )

    @staticmethod
    def _quick_reply(question: str) -> str | None:
        """Return an immediate response for greetings that need no model or RAG."""
        normalized = re.sub(r"[^a-z ]", "", question.lower()).strip()
        return _QUICK_REPLIES.get(normalized)

    @staticmethod
    def _known_topic_reply(question: str) -> str | None:
        """Resolve a small number of commonly misspelled named resources."""
        normalized = question.lower()
        asks_about_jakes_resume = bool(
            re.search(r"\b(?:jake|jaek)(?:['’]s)?\s+resume\b", normalized)
            and re.search(r"\b(?:what|explain|format|template)\b", normalized)
        )
        if not asks_about_jakes_resume:
            return None
        return (
            "**Jake's Resume** is a simple, single-column LaTeX resume template created "
            "by Jake Gutierrez and commonly used through Overleaf. It normally follows this "
            "one-page structure:\n\n"
            "1. Name and contact links\n"
            "2. Education\n"
            "3. Experience in reverse chronological order\n"
            "4. Projects\n"
            "5. Technical skills\n\n"
            "It uses compact headings and accomplishment-focused bullet points with minimal "
            "graphics. Its text-based layout is generally ATS-friendly, although no template "
            "can guarantee compatibility with every employer's parser. The original template "
            "is available as **Jake's Resume** on Overleaf."
        )

    @classmethod
    def _real_time_reply(
        cls,
        question: str,
        messages: list[ChatMessage],
        now_utc: datetime | None = None,
    ) -> str | None:
        """Answer India/Pacific clock questions from one UTC instant."""
        normalized = question.lower().replace("fdate", "date")
        recent_context = " ".join(message.content.lower() for message in messages[-6:])
        asks_for_clock = any(term in normalized for term in ("date", "time", "clock", "now"))
        asks_for_india = any(
            location in normalized for location in ("india", "ist", "kolkata", "calcutta")
        )
        asks_for_pacific = any(
            location in normalized
            for location in ("pdt", "pst", "pacific", "los angeles", "california")
        )
        is_zone_followup = normalized.strip(" ?.!-") in {"pdt", "pst", "pacific"} and any(
            term in recent_context for term in ("date", "time", "clock")
        )
        is_offset_followup = any(
            term in normalized for term in ("ahead", "behind", "hours", "hour", "am", "pm")
        ) and all(term in recent_context for term in ("india", "pdt"))
        is_correction_followup = any(
            term in normalized for term in ("why", "wrong", "correct", "19:54")
        ) and all(term in recent_context for term in ("india", "pdt"))
        if not (
            (asks_for_clock and (asks_for_india or asks_for_pacific))
            or is_zone_followup
            or is_offset_followup
            or is_correction_followup
        ):
            return None

        india_now, pacific_now = cls._clock_snapshot(now_utc)
        pacific_abbreviation = pacific_now.tzname() or "Pacific Time"
        difference = india_now.utcoffset() - pacific_now.utcoffset()
        assert difference is not None
        difference_hours, remainder = divmod(int(difference.total_seconds()), 3600)
        difference_minutes = remainder // 60
        relation = (
            f"India is **{difference_hours} hours {difference_minutes} minutes ahead** "
            f"of U.S. Pacific Time ({pacific_abbreviation})."
        )
        india_text = cls._format_zoned_time(india_now, "India")
        pacific_text = cls._format_zoned_time(pacific_now, "U.S. Pacific")

        if is_offset_followup or is_correction_followup:
            day_note = (
                " The Pacific date is the previous calendar day for this conversion."
                if pacific_now.date() < india_now.date()
                else " Both locations are currently on the same calendar date."
            )
            return f"{relation}\n\n{india_text}\n\n{pacific_text}{day_note}"
        if asks_for_india and asks_for_pacific:
            return f"{india_text}\n\n{pacific_text}\n\n{relation}"
        if asks_for_pacific or is_zone_followup:
            return pacific_text
        return india_text

    @staticmethod
    def _clock_snapshot(now_utc: datetime | None = None) -> tuple[datetime, datetime]:
        """Convert one UTC instant to IST and DST-aware U.S. Pacific time."""
        instant = now_utc or datetime.now(UTC)
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=UTC)
        india_timezone = timezone(timedelta(hours=5, minutes=30), name="IST")
        return (
            instant.astimezone(india_timezone),
            instant.astimezone(ZoneInfo("America/Los_Angeles")),
        )

    @staticmethod
    def _format_zoned_time(value: datetime, label: str) -> str:
        """Format a timezone-aware clock value with its actual UTC offset."""
        offset = value.strftime("%z")
        formatted_offset = f"UTC{offset[:3]}:{offset[3:]}"
        return (
            f"The current date and time in {label} is **"
            f"{value.strftime('%A, %d %B %Y at %I:%M:%S %p')} "
            f"{value.tzname()} ({formatted_offset})**."
        )

    @classmethod
    def _current_time_context(cls) -> dict[str, str]:
        """Return consistent local clock facts for conversational follow-ups."""
        india_now, pacific_now = cls._clock_snapshot()
        difference = india_now.utcoffset() - pacific_now.utcoffset()
        assert difference is not None
        return {
            "utc": india_now.astimezone(UTC).isoformat(),
            "india": india_now.isoformat(),
            "us_pacific": pacific_now.isoformat(),
            "us_pacific_abbreviation": pacific_now.tzname() or "Pacific Time",
            "india_ahead_seconds": str(int(difference.total_seconds())),
        }

    @staticmethod
    def _normalize_query_aliases(value: str) -> str:
        """Expand a small set of common user typos without changing intent."""
        return re.sub(
            r"\bjaek(?:['’]s)?\s+resume\b",
            "Jake's Resume (the popular one-page ATS-friendly LaTeX resume template)",
            value,
            flags=re.IGNORECASE,
        )

    @staticmethod
    def _should_use_rag(question: str) -> bool:
        """Return whether the question belongs to the indexed CyberSRS knowledge domain."""
        lowered = question.lower()
        return any(term in lowered for term in _CYBERSECURITY_TERMS)

    def _retrieve(self, question: str) -> tuple[list[RetrievedChunk], list[str]]:
        """Retrieve local knowledge, falling back gracefully when RAG is unavailable."""
        if not self._should_use_rag(question):
            return [], []
        if not self._settings.rag_enabled:
            return [], ["RAG is disabled; this answer uses model knowledge only."]
        try:
            retriever = create_retriever(
                self._settings,
                create_chromadb_client(self._settings),
                create_embedding_provider(self._settings),
            )
            context = retriever.retrieve_for_question(
                question,
                self._settings.knowledge_base_version,
                top_k=min(self._settings.rag_top_k, 5),
            )
            if not context.chunks:
                return [], ["No sufficiently relevant local knowledge was found."]
            return context.chunks, []
        except Exception:
            logger.warning("Chat RAG retrieval failed; continuing without retrieved context")
            return [], [
                "Local knowledge retrieval was unavailable; the answer uses model knowledge only."
            ]

    @staticmethod
    def _page_or_section(chunk: RetrievedChunk) -> str | None:
        """Return the most useful location label available for a chunk."""
        section = str(chunk.metadata.get("section_heading", "")).strip()
        if section:
            return section
        page = chunk.metadata.get("page_number")
        return f"Page {page}" if page else None

    def _validate_citations(
        self,
        source_ids: list[str],
        chunks: list[RetrievedChunk],
    ) -> list[ChatCitation]:
        """Keep only citations that exactly match chunks retrieved for this answer."""
        by_id = {chunk.chunk_id: chunk for chunk in chunks}
        citations: list[ChatCitation] = []
        for source_id in dict.fromkeys(source_ids):
            chunk = by_id.get(source_id)
            if chunk is None:
                continue
            citations.append(
                ChatCitation(
                    source_id=chunk.chunk_id,
                    source_document_id=str(chunk.metadata.get("source_id", "")),
                    document_title=str(chunk.metadata.get("document_title", "Unknown source")),
                    chunk_index=int(chunk.metadata.get("chunk_index", 0)),
                    page_or_section=self._page_or_section(chunk),
                    relevance_score=chunk.relevance_score,
                )
            )
        return citations
