"""LLM provider layer (Phase 1B: deterministic mock only).

Phase 2 will add an ``OllamaQwenProvider`` behind the same :class:`LLMProvider`
contract without changing application business logic.
"""

from .base import LLMProvider, LLMTask
from .factory import create_llm_provider
from .mock_provider import MockLLMProvider

__all__ = ["LLMProvider", "LLMTask", "MockLLMProvider", "create_llm_provider"]
