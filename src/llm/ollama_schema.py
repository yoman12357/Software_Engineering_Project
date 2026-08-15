"""Ollama JSON-Schema compatibility and lightweight grammar probing."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import httpx
from pydantic import BaseModel


class SchemaProbeClassification(StrEnum):
    """Stable outcomes from a lightweight Ollama grammar probe."""

    SCHEMA_ACCEPTED = "SCHEMA_ACCEPTED"
    GRAMMAR_REJECTED = "GRAMMAR_REJECTED"
    OTHER_ERROR = "OTHER_ERROR"


@dataclass(frozen=True)
class SchemaProbeResult:
    """Result of asking Ollama to compile a generation schema."""

    classification: SchemaProbeClassification
    status_code: int | None
    error_message: str | None = None


def build_ollama_generation_schema(schema_model: type[BaseModel]) -> dict[str, Any]:
    """Derive an Ollama-compatible generation schema from a Pydantic model.

    Ollama 0.32.11 rejects JSON-Schema ``pattern`` values containing the
    shorthand ``\\d`` escape. Replacing it with the equivalent explicit ASCII
    digit class preserves the ID constraints used by CyberSRS while leaving
    every field, required list, reference, union, and other constraint intact.
    The canonical Pydantic schema remains unchanged and is still used for final
    validation.
    """
    schema = copy.deepcopy(schema_model.model_json_schema())
    return _normalize_pattern_escapes(schema)


def _normalize_pattern_escapes(value: Any) -> Any:
    """Recursively normalize regex escapes unsupported by Ollama's grammar."""
    if isinstance(value, list):
        return [_normalize_pattern_escapes(item) for item in value]
    if not isinstance(value, dict):
        return value

    normalized: dict[str, Any] = {}
    for key, item in value.items():
        if key == "pattern" and isinstance(item, str):
            normalized[key] = item.replace(r"\d", "[0-9]")
        else:
            normalized[key] = _normalize_pattern_escapes(item)
    return normalized


def probe_ollama_schema(
    *,
    base_url: str,
    model_name: str,
    schema: dict[str, Any],
    num_ctx: int = 8192,
    timeout_seconds: float = 30.0,
) -> SchemaProbeResult:
    """Quickly classify whether Ollama can compile a JSON generation schema."""
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Return the smallest valid object."}],
        "format": schema,
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "num_ctx": num_ctx,
            "num_predict": 1,
            "temperature": 0.0,
        },
    }
    try:
        response = httpx.post(
            f"{base_url.rstrip('/')}/api/chat",
            json=payload,
            timeout=timeout_seconds,
        )
    except httpx.HTTPError as exc:
        return SchemaProbeResult(
            classification=SchemaProbeClassification.OTHER_ERROR,
            status_code=None,
            error_message=type(exc).__name__,
        )

    if response.status_code == 200:
        return SchemaProbeResult(
            classification=SchemaProbeClassification.SCHEMA_ACCEPTED,
            status_code=200,
        )

    try:
        error_message = str(response.json().get("error", "request failed"))
    except (ValueError, AttributeError):
        error_message = "request failed"
    classification = (
        SchemaProbeClassification.GRAMMAR_REJECTED
        if "parse grammar" in error_message.lower()
        else SchemaProbeClassification.OTHER_ERROR
    )
    return SchemaProbeResult(
        classification=classification,
        status_code=response.status_code,
        error_message=error_message[:500],
    )
