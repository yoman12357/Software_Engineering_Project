"""Model registry for CyberSRS.

Maps model variants (base, finetuned) to their runtime configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from ..core.model_constants import DEFAULT_BASE_MODEL_NAME, DEFAULT_FINETUNED_MODEL_NAME

if TYPE_CHECKING:
    from ..core.config import Settings


class ModelVariant(StrEnum):
    """Supported model variants."""

    BASE = "base"
    FINETUNED = "finetuned"


@dataclass(frozen=True)
class ModelConfig:
    """Runtime configuration for a model variant."""

    variant: ModelVariant
    runtime: str  # "ollama"
    model_name: str
    adapter_name: str | None = None


# Central registry mapping variant -> configuration.
# The finetuned model is expected to be available as an Ollama model
# named "cybersrs-qwen3-4b-ft" (loaded via Modelfile with the QLoRA adapter).
MODEL_REGISTRY: dict[ModelVariant, ModelConfig] = {
    ModelVariant.BASE: ModelConfig(
        variant=ModelVariant.BASE,
        runtime="ollama",
        model_name=DEFAULT_BASE_MODEL_NAME,
        adapter_name=None,
    ),
    ModelVariant.FINETUNED: ModelConfig(
        variant=ModelVariant.FINETUNED,
        runtime="ollama",
        model_name=DEFAULT_FINETUNED_MODEL_NAME,
        adapter_name=DEFAULT_FINETUNED_MODEL_NAME,
    ),
}


def resolve_model_config(settings: Settings) -> ModelConfig:
    """Resolve the active model configuration from settings.

    Args:
        settings: Application settings containing model_variant,
            base_model_name, finetuned_model_name.

    Returns:
        The resolved ModelConfig for the active variant.

    Raises:
        ValueError: If the configured model_variant is unknown or the
            finetuned model is selected but not available.
    """
    variant_str = settings.model_variant.strip().lower()
    try:
        variant = ModelVariant(variant_str)
    except ValueError as exc:
        supported = ", ".join(v.value for v in ModelVariant)
        raise ValueError(
            f"Unknown CYBERSRS_MODEL_VARIANT '{settings.model_variant}'. "
            f"Supported variants: {supported}."
        ) from exc

    registered = MODEL_REGISTRY[variant]
    if variant == ModelVariant.BASE:
        model_name = settings.base_model_name.strip()
        if (
            "model_name" in settings.model_fields_set
            and "base_model_name" not in settings.model_fields_set
        ):
            model_name = settings.model_name.strip()
    else:
        model_name = settings.finetuned_model_name.strip()

    if not model_name:
        variable = (
            "CYBERSRS_BASE_MODEL_NAME"
            if variant == ModelVariant.BASE
            else "CYBERSRS_FINETUNED_MODEL_NAME"
        )
        raise ValueError(f"{variable} must contain an Ollama model name.")

    return ModelConfig(
        variant=variant,
        runtime=registered.runtime,
        model_name=model_name,
        adapter_name=model_name if variant == ModelVariant.FINETUNED else None,
    )


def resolve_model_name(settings: Settings) -> str:
    """Backward-compatible accessor returning the active model name.

    This preserves backward compatibility with code that reads
    ``settings.model_name`` directly.
    """
    config = resolve_model_config(settings)
    return config.model_name


def resolve_adapter_name(settings: Settings) -> str | None:
    """Return the adapter name for the active variant, if any."""
    config = resolve_model_config(settings)
    return config.adapter_name
