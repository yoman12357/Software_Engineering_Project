"""Factory for constructing the configured :class:`LLMProvider`.

Phase 1B uses the deterministic ``mock`` provider. Phase 2 adds ``ollama``
behind the same factory; the business layer never constructs a provider directly.
Phase 8 adds model variant support (base / finetuned) resolved from the
model registry.
"""

from __future__ import annotations

from ..core.config import Settings
from .base import LLMProvider
from .mock_provider import MockLLMProvider
from .ollama_provider import SyncOllamaQwenProvider
from .registry import resolve_model_name

SUPPORTED_PROVIDERS: tuple[str, ...] = ("mock", "ollama")


def create_llm_provider(settings: Settings) -> LLMProvider:
    """Instantiate the LLM provider selected by ``CYBERSRS_LLM_PROVIDER``.

    The active model variant (base/finetuned) is resolved from
    ``CYBERSRS_MODEL_VARIANT`` via the model registry.

    Args:
        settings: Application settings; ``llm_provider`` selects the concrete
            implementation and model variant settings select the model.

    Returns:
        A configured provider instance.

    Raises:
        ValueError: If ``settings.llm_provider`` names an unsupported provider
            or the model variant configuration is invalid.
    """
    provider_name = settings.llm_provider.strip().lower()
    if provider_name == "mock":
        return MockLLMProvider()

    if provider_name == "ollama":
        # Resolve model name from variant; raises ValueError if invalid.
        model_name = resolve_model_name(settings)
        # Create updated settings with the resolved model name
        settings_dict = settings.model_dump(exclude={"model_name"})
        updated_settings = Settings(**settings_dict, model_name=model_name)
        return SyncOllamaQwenProvider(updated_settings)

    supported = ", ".join(SUPPORTED_PROVIDERS)
    raise ValueError(
        f"Unsupported CYBERSRS_LLM_PROVIDER '{settings.llm_provider}'. "
        f"Supported providers: {supported}."
    )
