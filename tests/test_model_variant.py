"""Tests for model variant configuration and registry (Phase 8)."""

from __future__ import annotations

import pytest

from src.core.config import Settings
from src.llm.registry import (
    MODEL_REGISTRY,
    ModelVariant,
    resolve_adapter_name,
    resolve_model_config,
    resolve_model_name,
)


class TestModelVariant:
    """Tests for the ModelVariant enum and registry."""

    def test_variant_values(self) -> None:
        assert ModelVariant.BASE == "base"
        assert ModelVariant.FINETUNED == "finetuned"

    def test_registry_contains_base_and_finetuned(self) -> None:
        assert ModelVariant.BASE in MODEL_REGISTRY
        assert ModelVariant.FINETUNED in MODEL_REGISTRY
        assert len(MODEL_REGISTRY) == 2

    def test_base_config(self) -> None:
        config = MODEL_REGISTRY[ModelVariant.BASE]
        assert config.variant == ModelVariant.BASE
        assert config.runtime == "ollama"
        assert config.model_name == "qwen3:4b-instruct-2507-q4_K_M"
        assert config.adapter_name is None

    def test_finetuned_config(self) -> None:
        config = MODEL_REGISTRY[ModelVariant.FINETUNED]
        assert config.variant == ModelVariant.FINETUNED
        assert config.runtime == "ollama"
        assert config.model_name == "cybersrs-qwen3-4b-ft"
        assert config.adapter_name == "cybersrs-qwen3-4b-ft"


class TestResolveModelName:
    """Tests for resolve_model_name function."""

    def test_base_variant_resolves_to_base_model(self) -> None:
        assert resolve_model_name(Settings(model_variant="base")) == "qwen3:4b-instruct-2507-q4_K_M"

    def test_finetuned_variant_resolves_to_finetuned_model(self) -> None:
        assert resolve_model_name(Settings(model_variant="finetuned")) == "cybersrs-qwen3-4b-ft"

    def test_case_insensitive(self) -> None:
        assert resolve_model_name(Settings(model_variant="BASE")) == "qwen3:4b-instruct-2507-q4_K_M"
        assert resolve_model_name(Settings(model_variant="Finetuned")) == "cybersrs-qwen3-4b-ft"

    def test_invalid_variant_raises(self) -> None:
        with pytest.raises(ValueError) as exc_info:
            resolve_model_name(Settings(model_variant="invalid"))
        message = str(exc_info.value).lower()
        assert "invalid" in message
        assert "base" in message
        assert "finetuned" in message


class TestResolveModelConfig:
    """Tests for resolve_model_config function."""

    def test_base_variant(self) -> None:
        settings = Settings(model_variant="base")
        config = resolve_model_config(settings)
        assert config.variant == ModelVariant.BASE
        assert config.model_name == "qwen3:4b-instruct-2507-q4_K_M"
        assert config.adapter_name is None

    def test_finetuned_variant(self) -> None:
        settings = Settings(model_variant="finetuned")
        config = resolve_model_config(settings)
        assert config.variant == ModelVariant.FINETUNED
        assert config.model_name == "cybersrs-qwen3-4b-ft"
        assert config.adapter_name == "cybersrs-qwen3-4b-ft"

    def test_invalid_variant_raises(self) -> None:
        with pytest.raises(ValueError, match="invalid"):
            resolve_model_config(Settings(model_variant="invalid"))

    def test_finetuned_without_model_name_raises(self) -> None:
        with pytest.raises(ValueError, match="CYBERSRS_FINETUNED_MODEL_NAME"):
            resolve_model_config(
                Settings(model_variant="finetuned", finetuned_model_name="")
            )

    def test_configured_model_names_are_respected(self) -> None:
        assert (
            resolve_model_name(Settings(model_variant="base", base_model_name="base-local"))
            == "base-local"
        )
        assert (
            resolve_model_name(
                Settings(model_variant="finetuned", finetuned_model_name="ft-local")
            )
            == "ft-local"
        )

    def test_legacy_model_name_remains_a_base_override(self) -> None:
        settings = Settings(model_variant="base", model_name="legacy-base-local")
        assert resolve_model_name(settings) == "legacy-base-local"


class TestResolveAdapterName:
    """Tests for resolve_adapter_name function."""

    def test_base_variant_returns_none(self) -> None:
        assert resolve_adapter_name(Settings(model_variant="base")) is None

    def test_finetuned_variant_returns_adapter_name(self) -> None:
        assert resolve_adapter_name(Settings(model_variant="finetuned")) == "cybersrs-qwen3-4b-ft"


class TestSettingsDefaults:
    """Tests for default values in Settings."""

    def test_default_model_variant_is_base(self) -> None:
        settings = Settings(_env_file=None)
        assert settings.model_variant == "base"

    def test_model_name_defaults_to_base(self) -> None:
        settings = Settings(_env_file=None)
        assert settings.model_name == "qwen3:4b-instruct-2507-q4_K_M"

    def test_base_model_name_field(self) -> None:
        settings = Settings(_env_file=None)
        assert settings.base_model_name == "qwen3:4b-instruct-2507-q4_K_M"

    def test_finetuned_model_name_field(self) -> None:
        settings = Settings(_env_file=None)
        assert settings.finetuned_model_name == "cybersrs-qwen3-4b-ft"
