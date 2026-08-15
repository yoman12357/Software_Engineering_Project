"""Ollama-backed Qwen provider for CyberSRS (Phase 2A).

Implements the LLMProvider abstraction using the local Ollama API.
Only communicates with the locally hosted Ollama instance — no external APIs.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from ..core.config import Settings
from .base import LLMOutputError, LLMProvider, LLMRequest, LLMResponse, LLMTask, LLMTimeoutError
from .ollama_schema import build_ollama_generation_schema

logger = logging.getLogger(__name__)


def _response_format(request: LLMRequest) -> str | dict[str, Any]:
    """Return Ollama's structured-output format from the canonical schema."""
    if request.response_schema is None:
        return "json"
    return build_ollama_generation_schema(request.response_schema)


@dataclass(frozen=True)
class OllamaConfig:
    """Configuration for Ollama provider."""

    base_url: str
    model_name: str
    timeout_seconds: int
    max_retries: int
    num_ctx: int
    num_predict: int
    repeat_penalty: float
    repeat_last_n: int
    temperature: float
    top_p: float


class OllamaQwenProvider(LLMProvider):
    """Ollama-backed provider using Qwen3-4B-Instruct-2507.

    Communicates exclusively with the local Ollama instance.
    Implements bounded retries with corrective prompts for schema validation.
    """

    provider_name = "ollama"

    def __init__(self, settings: Settings) -> None:
        """Initialise the provider with settings.

        Args:
            settings: Application settings containing Ollama configuration.
        """
        model_name = settings.model_name
        super().__init__(model_name)

        self._config = OllamaConfig(
            base_url=settings.ollama_base_url.rstrip("/"),
            model_name=model_name,
            timeout_seconds=settings.ollama_timeout_seconds or settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
            num_ctx=settings.ollama_num_ctx,
            num_predict=settings.ollama_num_predict,
            repeat_penalty=settings.ollama_repeat_penalty,
            repeat_last_n=settings.ollama_repeat_last_n,
            temperature=settings.ollama_temperature,
            top_p=settings.ollama_top_p,
        )
        self._client = httpx.AsyncClient(
            base_url=self._config.base_url,
            timeout=httpx.Timeout(
                connect=10.0,
                read=self._config.timeout_seconds,
                write=10.0,
                pool=10.0,
            ),
        )

    async def __aenter__(self) -> OllamaQwenProvider:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._client.aclose()

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response synchronously (for compatibility with existing code).

        This is a blocking wrapper around the async implementation.
        """
        return asyncio.run(self._generate_async(request))

    async def _generate_async(self, request: LLMRequest) -> LLMResponse:
        """Async implementation of generation with retries and corrective prompts."""
        last_error: Exception | None = None
        timed_out = False
        corrective_prompt = ""

        for attempt in range(self._config.max_retries + 1):
            try:
                payload = self._build_chat_payload(request, corrective_prompt)
                response = await self._client.post("/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()

                content = data.get("message", {}).get("content", "")
                if not content:
                    raise LLMOutputError("Empty response from Ollama")

                # Log generation metadata (without user content per SEC-031)
                logger.info(
                    "LLM generation completed",
                    extra={
                        "task": request.task.value,
                        "model": self.model_name,
                        "attempt": attempt + 1,
                        "latency_ms": int(data.get("total_duration", 0) / 1_000_000),
                    },
                )

                return LLMResponse(
                    content=content,
                    model_name=self.model_name,
                    is_deterministic=False,
                    prompt_eval_count=data.get("prompt_eval_count"),
                    eval_count=data.get("eval_count"),
                )

            except httpx.ConnectError as exc:
                last_error = exc
                logger.warning(
                    "Ollama connection failed",
                    extra={"attempt": attempt + 1, "max_retries": self._config.max_retries},
                )
            except httpx.ReadTimeout as exc:
                timed_out = True
                last_error = exc
                logger.warning(
                    "Ollama read timed out",
                    extra={"attempt": attempt + 1, "timeout_seconds": self._config.timeout_seconds},
                )
            except httpx.TimeoutException as exc:
                timed_out = True
                last_error = exc
                logger.warning(
                    "Ollama request timed out",
                    extra={"attempt": attempt + 1, "timeout_seconds": self._config.timeout_seconds},
                )
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code == 404:
                    # Model not found
                    raise LLMOutputError(
                        f"Model '{self._config.model_name}' not found in Ollama. "
                        f"Run: ollama pull {self._config.model_name}"
                    ) from exc
                logger.warning(
                    "Ollama HTTP error",
                    extra={"status": exc.response.status_code, "attempt": attempt + 1},
                )
            except LLMOutputError:
                # Re-raise validation errors immediately (they come from parse_structured)
                raise
            except Exception as exc:
                last_error = exc
                logger.exception("Unexpected error during LLM generation")

            if attempt < self._config.max_retries:
                # Exponential backoff: 1s, 2s, 4s...
                backoff = 2**attempt
                logger.info(f"Retrying in {backoff}s...")
                await asyncio.sleep(backoff)

        if timed_out:
            raise LLMTimeoutError(
                "Ollama timed out while waiting for a response. Please try again."
            ) from last_error

        # All retries exhausted
        raise LLMOutputError(
            f"LLM generation failed after {self._config.max_retries + 1} attempts: {last_error}"
        ) from last_error

    def _build_chat_payload(
        self,
        request: LLMRequest,
        corrective_prompt: str = "",
    ) -> dict[str, Any]:
        """Build the Ollama chat API payload."""
        messages = [
            {"role": "system", "content": request.system_prompt},
        ]
        user_content = request.user_content
        if corrective_prompt:
            user_content = f"{user_content}\n\n{corrective_prompt}"
        messages.append({"role": "user", "content": user_content})

        return {
            "model": self._config.model_name,
            "messages": messages,
            "format": _response_format(request),
            "stream": False,
            "options": {
                "temperature": self._config.temperature,
                "top_p": self._config.top_p,
                "num_ctx": self._config.num_ctx,
                "num_predict": self._config.num_predict,
                "repeat_penalty": self._config.repeat_penalty,
                "repeat_last_n": self._config.repeat_last_n,
            },
        }

    def parse_structured(self, response: LLMResponse, schema: type) -> Any:
        """Parse and validate response against a Pydantic schema.

        Uses the base class implementation but with enhanced error context.
        """
        try:
            return super().parse_structured(response, schema)
        except LLMOutputError as exc:
            # Add context about the task for debugging
            raise LLMOutputError(f"{exc}") from exc

    # --- Sectioned Generation Helpers ---

    async def generate_section(
        self,
        system_prompt: str,
        user_content: str,
        schema: type,
    ) -> Any:
        """Generate a single SRS section with validation and retries."""
        request = LLMRequest(
            task=LLMTask.SRS,  # Task type for logging
            system_prompt=system_prompt,
            user_content=user_content,
            response_schema=schema,
        )
        response = await self._generate_async(request)
        return self.parse_structured(response, schema)

    def generate_section_sync(
        self,
        system_prompt: str,
        user_content: str,
        schema: type,
    ) -> Any:
        """Synchronous wrapper for section generation."""
        return asyncio.run(self.generate_section(system_prompt, user_content, schema))


# --- Synchronous wrapper for backward compatibility ---


class SyncOllamaQwenProvider(LLMProvider):
    """Synchronous wrapper using synchronous httpx client."""

    provider_name = "ollama"

    def __init__(self, settings: Settings) -> None:
        model_name = settings.model_name
        super().__init__(model_name)
        self._settings = settings
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = model_name
        # Use Ollama-specific timeout (CYBERSRS_OLLAMA_TIMEOUT_SECONDS) as authoritative
        self._timeout = settings.ollama_timeout_seconds
        self._max_retries = settings.llm_max_retries
        self._num_ctx = settings.ollama_num_ctx
        self._num_predict = settings.ollama_num_predict
        self._repeat_penalty = settings.ollama_repeat_penalty
        self._repeat_last_n = settings.ollama_repeat_last_n
        self._temperature = settings.ollama_temperature
        self._top_p = settings.ollama_top_p
        # Backward-compatible attribute for older tests/callers. This wrapper
        # now uses a synchronous client directly.
        self._async_provider = None
        # Configure timeout with long read timeout for SRS generation
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=httpx.Timeout(
                connect=10.0,
                read=self._timeout,
                write=10.0,
                pool=10.0,
            ),
        )

    def generate(self, request: LLMRequest) -> LLMResponse:
        last_error = None
        for attempt in range(self._max_retries + 1):
            try:
                payload = {
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": request.system_prompt},
                        {"role": "user", "content": request.user_content},
                    ],
                    "format": _response_format(request),
                    "stream": False,
                    "options": {
                        "temperature": self._temperature,
                        "top_p": self._top_p,
                        "num_ctx": self._num_ctx,
                        "num_predict": self._num_predict,
                        "repeat_penalty": self._repeat_penalty,
                        "repeat_last_n": self._repeat_last_n,
                    },
                }
                response = self._client.post("/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()

                content = data.get("message", {}).get("content", "")
                if not content:
                    raise LLMOutputError("Empty response from Ollama")

                return LLMResponse(
                    content=content,
                    model_name=self.model_name,
                    is_deterministic=False,
                    prompt_eval_count=data.get("prompt_eval_count"),
                    eval_count=data.get("eval_count"),
                )

            except httpx.ConnectError as exc:
                last_error = exc
            except httpx.TimeoutException as exc:
                last_error = exc
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code == 404:
                    raise LLMOutputError(
                        f"Model '{self._model}' not found in Ollama. Run: ollama pull {self._model}"
                    ) from exc
                # Log the actual error response for debugging
                try:
                    error_detail = exc.response.text
                except Exception:
                    error_detail = "Could not read error response"
                logger.error(f"Ollama HTTP {exc.response.status_code}: {error_detail}")
                if exc.response.status_code == 400:
                    # Try to parse the error for more details
                    try:
                        error_json = exc.response.json()
                        error_msg = error_json.get("error", error_detail)
                    except Exception:
                        error_msg = error_detail
                    raise LLMOutputError(f"Ollama 400 Bad Request: {error_msg}") from exc
            except LLMOutputError:
                raise
            except Exception as exc:
                last_error = exc

            if attempt < self._max_retries:
                time.sleep(2**attempt)
            else:
                break

        raise LLMOutputError(
            f"LLM generation failed after {self._max_retries + 1} attempts: {last_error}"
        ) from last_error

    def parse_structured(self, response: LLMResponse, schema: type) -> Any:
        try:
            return super().parse_structured(response, schema)
        except LLMOutputError as exc:
            raise LLMOutputError(f"{exc}") from exc

    def generate_with_validation(
        self,
        request: LLMRequest,
        schema: type,
        max_retries: int | None = None,
    ) -> Any:
        """Generate and validate against schema with corrective retries.

        Args:
            request: The LLM request
            schema: Pydantic schema to validate against
            max_retries: Maximum validation retries (defaults to config max_retries)

        Returns:
            Validated schema instance

        Raises:
            LLMOutputError: If all retries exhausted
        """
        max_retries = self._max_retries if max_retries is None else max_retries
        last_error = None
        current_request = LLMRequest(
            task=request.task,
            system_prompt=request.system_prompt,
            user_content=request.user_content,
            response_schema=request.response_schema,
        )

        for attempt in range(max_retries + 1):
            try:
                response = self.generate(current_request)
                return self.parse_structured(response, schema)
            except LLMOutputError as exc:
                last_error = exc
                if attempt < max_retries:
                    # Build corrective prompt with schema and error
                    error_msg = str(exc)
                    corrective = (
                        f"Your previous response failed validation: {error_msg}\n"
                        "Correct the listed fields and return only the complete JSON object. "
                        "The canonical response schema is enforced separately."
                    )
                    # Create new request with corrective prompt (LLMRequest is frozen)
                    current_request = LLMRequest(
                        task=current_request.task,
                        system_prompt=current_request.system_prompt,
                        user_content=f"{current_request.user_content}\n\n{corrective}",
                        response_schema=current_request.response_schema,
                    )
                    logger.warning(
                        "Validation failed, retrying with corrective prompt (attempt %s/%s): %s",
                        attempt + 2,
                        max_retries + 1,
                        error_msg,
                    )
                    continue
                raise

        raise LLMOutputError(
            f"Validation failed after {max_retries + 1} attempts: {last_error}"
        ) from last_error

    def __del__(self):
        # Best-effort cleanup
        try:
            self._client.close()
        except Exception:
            pass
