"""Abstract LLM provider contract.

Phase 1B ships only :class:`MockLLMProvider`; Phase 2 will add an
``OllamaQwenProvider`` implementing the same interface. Business logic must
depend only on this abstraction so the real model can replace the mock without
application changes.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


def load_json_object(content: str) -> tuple[dict[str, Any], bool]:
    """Load one JSON object and report whether wrapper text was removed."""
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        return payload, False
    if payload is not None:
        raise LLMOutputError("response JSON is not an object")

    start = content.find("{")
    if start < 0:
        raise LLMOutputError("response is not valid JSON")
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(content[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    extracted = json.loads(content[start : index + 1])
                except json.JSONDecodeError as exc:
                    raise LLMOutputError("response is not valid JSON") from exc
                if not isinstance(extracted, dict):
                    raise LLMOutputError("response JSON is not an object")
                return extracted, True
    raise LLMOutputError("response is not valid JSON: incomplete object")


class LLMTask(StrEnum):
    """The kind of structured output a provider is asked to produce."""

    ANALYSIS = "analysis"
    CLARIFICATION = "clarification"
    SRS = "srs"


class LLMOutputError(ValueError):
    """Raised when a provider returns content that cannot be parsed/validated.

    Application code catches this error to trigger corrective retries or a
    structured 422 response. The message must not contain raw user content.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(f"LLM returned invalid structured output: {reason}")


class LLMTimeoutError(LLMOutputError):
    """Raised when the provider times out waiting for an Ollama response."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)


@dataclass(frozen=True)
class LLMRequest:
    """A single generation request.

    Attributes:
        task: Identifies the expected structured output schema.
        system_prompt: Fixed instructions describing the output contract.
        user_content: Sanitised user content (e.g. the project description).
    """

    task: LLMTask
    system_prompt: str
    user_content: str
    response_schema: type[BaseModel] | None = None


@dataclass(frozen=True)
class LLMResponse:
    """The provider's raw generation result.

    Attributes:
        content: Raw text produced by the provider.
        model_name: The model identifier used for the call.
        is_deterministic: True when the output is generated without real LLM
            inference (mock providers, Phase 1B).
    """

    content: str
    model_name: str
    is_deterministic: bool = True
    prompt_eval_count: int | None = None
    eval_count: int | None = None


class LLMProvider(ABC):
    """Provider-independent interface for LLM generation.

    Implementations must:

    - Accept an :class:`LLMRequest` and return an :class:`LLMResponse`.
    - Raise :class:`LLMOutputError` when the produced content cannot be
      interpreted as the task's structured output (schema validation is the
      caller's responsibility via :meth:`parse_structured`).
    """

    provider_name: str = "abstract"

    def __init__(self, model_name: str) -> None:
        """Store the configured model identifier used for this provider."""
        self.model_name = model_name

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a raw response for the given request.

        Raises:
            LLMOutputError: If the provider produces content it knows is
                unusable (e.g. an Ollama transport error in Phase 2).
        """

    def parse_structured(self, response: LLMResponse, schema: type[T]) -> T:
        """Parse and validate provider output against a Pydantic schema.

        The raw JSON dict is extracted from ``response.content`` and validated
        against ``schema``. On failure an :class:`LLMOutputError` is raised so
        callers can retry with a corrective prompt or surface a structured
        error. Arbitrary dicts never cross the service layer without passing
        through this contract.

        Raises:
            LLMOutputError: If the content is not valid JSON or fails schema
                validation.
        """
        payload, wrapper_removed = load_json_object(response.content)
        if wrapper_removed:
            logger.warning(
                "Recovered structured output by removing a non-JSON wrapper",
                extra={"model": response.model_name},
            )
        try:
            return schema.model_validate(payload)
        except ValidationError as exc:
            first_error = exc.errors()[0] if exc.errors() else None
            if first_error is None:
                raise LLMOutputError("validation failed") from exc
            error_data: dict[str, Any] = dict(first_error)
            loc = error_data.get("loc", ())
            if isinstance(loc, (list, tuple)):
                location = ".".join(str(part) for part in loc) or "<root>"
            else:
                location = "<root>"
            message = str(error_data.get("msg", "unknown validation error"))
            raise LLMOutputError(f"{location}: {message}") from exc

    @staticmethod
    def dump_example(schema: type[T]) -> str:
        """Return the JSON-schema example used in system prompts."""
        return json.dumps(schema.model_json_schema(), indent=2)

    def generate_with_validation(
        self,
        request: LLMRequest,
        schema: type[T],
        max_retries: int | None = None,
    ) -> T:
        """Generate and validate against schema with retries.

        Default implementation just calls generate + parse_structured.
        Concrete providers should override with corrective retry logic.

        Args:
            request: The LLM request
            schema: Pydantic schema to validate against
            max_retries: Maximum validation retries (provider-specific)

        Returns:
            Validated schema instance

        Raises:
            LLMOutputError: If generation or validation fails
        """
        response = self.generate(request)
        return self.parse_structured(response, schema)
