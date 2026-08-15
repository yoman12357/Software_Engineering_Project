"""Unit tests for OllamaQwenProvider (Phase 2A).

Tests use mocked HTTP calls so they don't require a real Ollama instance.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.core.config import Settings
from src.llm.base import LLMOutputError, LLMRequest, LLMResponse, LLMTask, LLMTimeoutError
from src.llm.ollama_provider import OllamaQwenProvider, SyncOllamaQwenProvider
from src.llm.ollama_schema import build_ollama_generation_schema
from src.schemas.analysis import ProjectAnalysis
from src.schemas.clarification import ClarificationQuestionSet
from src.schemas.srs import SRSSchema

SAMPLE_DESCRIPTION = "I want to build a firewall and monitoring system for my college network."

VALID_ANALYSIS_JSON = json.dumps(
    {
        "stakeholders": ["Campus IT", "Students"],
        "assets": ["Campus network"],
        "users": ["Network admins"],
        "constraints": ["Budget limits"],
        "goals": ["Block malicious traffic"],
        "inferred_categories": ["CAT-02", "CAT-03"],
        "missing_information": ["Number of nodes"],
        "project_summary": "A firewall system for college campus.",
    }
)

VALID_CLARIFICATION_JSON = json.dumps(
    {
        "questions": [
            {
                "question_text": "How many network nodes?",
                "reason": "Scale affects architecture",
                "is_critical": True,
                "target_gap": "Number of nodes",
                "expected_answer_type": "number",
            }
        ]
    }
)


def _make_ollama_response(content: str) -> dict:
    """Create a mock Ollama /api/chat response."""
    return {
        "model": "qwen3:4b-instruct-2507-q4_K_M",
        "created_at": "2026-01-01T00:00:00Z",
        "message": {"role": "assistant", "content": content},
        "done": True,
        "total_duration": 1000000000,
    }


@pytest.fixture
def ollama_settings() -> Settings:
    """Settings configured for Ollama provider."""
    return Settings(
        _env_file=None,
        llm_provider="ollama",
        ollama_base_url="http://127.0.0.1:11434",
        model_name="qwen3:4b-instruct-2507-q4_K_M",
        ollama_timeout_seconds=300,
        llm_timeout_seconds=30,
        llm_max_retries=2,
    )


@pytest.fixture
def mock_httpx_client() -> MagicMock:
    """Mock httpx.AsyncClient for testing."""
    with patch("src.llm.ollama_provider.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        yield mock_client


class TestOllamaQwenProvider:
    """Tests for the async OllamaQwenProvider."""

    @pytest.mark.asyncio
    async def test_init_sets_correct_attributes(self, ollama_settings: Settings) -> None:
        """Provider initialises with correct configuration."""
        provider = OllamaQwenProvider(ollama_settings)
        assert provider.provider_name == "ollama"
        assert provider.model_name == "qwen3:4b-instruct-2507-q4_K_M"
        assert provider._config.base_url == "http://127.0.0.1:11434"
        assert provider._config.timeout_seconds == 300
        assert provider._config.max_retries == 2

    @pytest.mark.asyncio
    async def test_generate_analysis_success(
        self, ollama_settings: Settings, mock_httpx_client: MagicMock
    ) -> None:
        """Successful analysis generation returns validated response."""
        mock_response = MagicMock()
        mock_response.json = lambda: _make_ollama_response(VALID_ANALYSIS_JSON)
        mock_httpx_client.post.return_value = mock_response

        provider = OllamaQwenProvider(ollama_settings)
        request = LLMRequest(
            task=LLMTask.ANALYSIS,
            system_prompt="test prompt",
            user_content=SAMPLE_DESCRIPTION,
        )
        response = await provider._generate_async(request)

        assert isinstance(response, LLMResponse)
        assert response.model_name == "qwen3:4b-instruct-2507-q4_K_M"
        assert response.is_deterministic is False
        payload = mock_httpx_client.post.call_args.kwargs["json"]
        assert payload["format"] == "json"
        assert "tools" not in payload

        # Parse and validate
        analysis = provider.parse_structured(response, ProjectAnalysis)
        assert analysis.inferred_categories == ["CAT-02", "CAT-03"]
        assert analysis.stakeholders == ["Campus IT", "Students"]

    @pytest.mark.asyncio
    async def test_generate_clarification_success(
        self, ollama_settings: Settings, mock_httpx_client: MagicMock
    ) -> None:
        """Successful clarification generation returns validated response."""
        mock_response = MagicMock()
        mock_response.json = lambda: _make_ollama_response(VALID_CLARIFICATION_JSON)
        mock_httpx_client.post.return_value = mock_response

        provider = OllamaQwenProvider(ollama_settings)
        request = LLMRequest(
            task=LLMTask.CLARIFICATION,
            system_prompt="test prompt",
            user_content=SAMPLE_DESCRIPTION,
        )
        response = await provider._generate_async(request)

        question_set = provider.parse_structured(response, ClarificationQuestionSet)
        assert len(question_set.questions) == 1
        assert question_set.questions[0].question_text == "How many network nodes?"
        assert question_set.questions[0].expected_answer_type.value == "number"

    @pytest.mark.asyncio
    async def test_generate_handles_connection_error_retries(
        self, ollama_settings: Settings, mock_httpx_client: MagicMock
    ) -> None:
        """Connection errors trigger retries with exponential backoff."""
        mock_httpx_client.post.side_effect = httpx.ConnectError("Connection refused")

        provider = OllamaQwenProvider(ollama_settings)
        request = LLMRequest(
            task=LLMTask.ANALYSIS,
            system_prompt="test",
            user_content=SAMPLE_DESCRIPTION,
        )

        with pytest.raises(LLMOutputError, match="failed after 3 attempts"):
            await provider._generate_async(request)

        # Should have retried max_retries + 1 times (initial + 2 retries = 3)
        assert mock_httpx_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_handles_timeout_retries(
        self, ollama_settings: Settings, mock_httpx_client: MagicMock
    ) -> None:
        """Timeout errors trigger retries and surface a timeout-specific error."""
        mock_httpx_client.post.side_effect = httpx.ReadTimeout("Request timed out")

        provider = OllamaQwenProvider(ollama_settings)
        request = LLMRequest(
            task=LLMTask.ANALYSIS,
            system_prompt="test",
            user_content=SAMPLE_DESCRIPTION,
        )

        with pytest.raises(LLMTimeoutError, match="timed out"):
            await provider._generate_async(request)

        assert mock_httpx_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_handles_model_not_found(
        self, ollama_settings: Settings, mock_httpx_client: MagicMock
    ) -> None:
        """404 for missing model raises clear error without retries."""
        response_mock = AsyncMock()
        response_mock.status_code = 404
        
        def raise_404():
            raise httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=response_mock
            )
        response_mock.raise_for_status = raise_404
        response_mock.json = lambda: {}
        mock_httpx_client.post.return_value = response_mock

        provider = OllamaQwenProvider(ollama_settings)
        request = LLMRequest(
            task=LLMTask.ANALYSIS,
            system_prompt="test",
            user_content=SAMPLE_DESCRIPTION,
        )

        with pytest.raises(LLMOutputError, match="not found in Ollama"):
            await provider._generate_async(request)

        # Should not retry on 404
        assert mock_httpx_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_generate_handles_http_error_retries(
        self, ollama_settings: Settings, mock_httpx_client: MagicMock
    ) -> None:
        """Other HTTP errors trigger retries."""
        response_mock = AsyncMock()
        response_mock.status_code = 500
        
        def raise_500():
            raise httpx.HTTPStatusError(
                "Internal Server Error", request=MagicMock(), response=response_mock
            )
        response_mock.raise_for_status = raise_500
        response_mock.json = lambda: {}
        mock_httpx_client.post.return_value = response_mock

        provider = OllamaQwenProvider(ollama_settings)
        request = LLMRequest(
            task=LLMTask.ANALYSIS,
            system_prompt="test",
            user_content=SAMPLE_DESCRIPTION,
        )

        with pytest.raises(LLMOutputError, match="failed after 3 attempts"):
            await provider._generate_async(request)

        assert mock_httpx_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_handles_empty_response(
        self, ollama_settings: Settings, mock_httpx_client: MagicMock
    ) -> None:
        """Empty response content raises LLMOutputError."""
        mock_response = MagicMock()
        mock_response.json = lambda: _make_ollama_response("")
        mock_httpx_client.post.return_value = mock_response

        provider = OllamaQwenProvider(ollama_settings)
        request = LLMRequest(
            task=LLMTask.ANALYSIS,
            system_prompt="test",
            user_content=SAMPLE_DESCRIPTION,
        )

        with pytest.raises(LLMOutputError, match="Empty response from Ollama"):
            await provider._generate_async(request)

    @pytest.mark.asyncio
    async def test_generate_handles_malformed_json_response(
        self, ollama_settings: Settings, mock_httpx_client: MagicMock
    ) -> None:
        """Non-JSON response from Ollama raises LLMOutputError."""
        # Ollama returns valid HTTP but the content is not parseable as our schema
        bad_json = json.dumps({"not": "the right schema"})
        mock_response = MagicMock()
        mock_response.json = lambda: _make_ollama_response(bad_json)
        mock_httpx_client.post.return_value = mock_response

        provider = OllamaQwenProvider(ollama_settings)
        request = LLMRequest(
            task=LLMTask.ANALYSIS,
            system_prompt="test",
            user_content=SAMPLE_DESCRIPTION,
        )
        response = await provider._generate_async(request)

        # The generation succeeds but parsing fails
        with pytest.raises(LLMOutputError):
            provider.parse_structured(response, ProjectAnalysis)

    @pytest.mark.asyncio
    async def test_parse_structured_rejects_invalid_json(self, ollama_settings: Settings) -> None:
        """Non-JSON content raises LLMOutputError."""
        provider = OllamaQwenProvider(ollama_settings)
        bad_response = LLMResponse(
            content="not valid json {",
            model_name="test",
            is_deterministic=False,
        )

        with pytest.raises(LLMOutputError, match="not valid JSON"):
            provider.parse_structured(bad_response, ProjectAnalysis)

    @pytest.mark.asyncio
    async def test_parse_structured_rejects_schema_violations(
        self, ollama_settings: Settings
    ) -> None:
        """Valid JSON that fails schema validation raises LLMOutputError."""
        provider = OllamaQwenProvider(ollama_settings)
        invalid_payload = json.dumps(
            {
                "stakeholders": [],
                "assets": [],
                "users": [],
                "constraints": [],
                "goals": [],
                "inferred_categories": ["CAT-99"],
                "missing_information": [],
                "project_summary": "",
            }
        )
        bad_response = LLMResponse(
            content=invalid_payload,
            model_name="test",
            is_deterministic=False,
        )

        with pytest.raises(LLMOutputError):
            provider.parse_structured(bad_response, ProjectAnalysis)


class TestSyncOllamaQwenProvider:
    """Tests for the synchronous wrapper."""

    def test_init_creates_async_provider(self, ollama_settings: Settings) -> None:
        """Sync wrapper initialises async provider."""
        provider = SyncOllamaQwenProvider(ollama_settings)
        assert provider.provider_name == "ollama"
        assert provider.model_name == "qwen3:4b-instruct-2507-q4_K_M"
        assert hasattr(provider, "_async_provider")

    def test_generate_delegates_to_async(
        self, ollama_settings: Settings
    ) -> None:
        """Sync generation uses the configured structured Ollama payload."""
        mock_response = MagicMock()
        mock_response.json = lambda: _make_ollama_response(VALID_ANALYSIS_JSON)

        provider = SyncOllamaQwenProvider(ollama_settings)
        provider._client.post = MagicMock(return_value=mock_response)
        request = LLMRequest(
            task=LLMTask.ANALYSIS,
            system_prompt="test",
            user_content=SAMPLE_DESCRIPTION,
        )
        response = provider.generate(request)

        assert isinstance(response, LLMResponse)
        assert response.model_name == "qwen3:4b-instruct-2507-q4_K_M"
        payload = provider._client.post.call_args.kwargs["json"]
        assert payload["format"] == "json"

    def test_srs_request_uses_canonical_schema_without_tools(
        self, ollama_settings: Settings
    ) -> None:
        """SRS decoding uses the Pydantic schema and does not enable tools."""
        mock_response = MagicMock()
        mock_response.json = lambda: _make_ollama_response("{}")
        provider = SyncOllamaQwenProvider(ollama_settings)
        provider._client.post = MagicMock(return_value=mock_response)

        provider.generate(
            LLMRequest(
                task=LLMTask.SRS,
                system_prompt="generate",
                user_content="project",
                response_schema=SRSSchema,
            )
        )

        payload = provider._client.post.call_args.kwargs["json"]
        assert payload["format"] == build_ollama_generation_schema(SRSSchema)
        assert "tools" not in payload

    def test_legacy_analysis_validation_keeps_json_mode(
        self, ollama_settings: Settings
    ) -> None:
        """Canonical validation does not force schema grammar on legacy stages."""
        mock_response = MagicMock()
        mock_response.json = lambda: _make_ollama_response(VALID_ANALYSIS_JSON)
        provider = SyncOllamaQwenProvider(ollama_settings)
        provider._client.post = MagicMock(return_value=mock_response)

        analysis = provider.generate_with_validation(
            LLMRequest(
                task=LLMTask.ANALYSIS,
                system_prompt="analyse",
                user_content=SAMPLE_DESCRIPTION,
            ),
            ProjectAnalysis,
        )

        assert analysis.inferred_categories == ["CAT-02", "CAT-03"]
        payload = provider._client.post.call_args.kwargs["json"]
        assert payload["format"] == "json"
