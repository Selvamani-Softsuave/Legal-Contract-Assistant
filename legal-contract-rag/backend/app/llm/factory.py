import os
import logging
from typing import Dict, Type, Optional
from backend.app.llm.base import LLMProvider
from backend.app.llm.providers.ollama_provider import OllamaProvider
from backend.app.llm.providers.gemini_provider import GeminiProvider
from backend.app.llm.providers.openrouter_provider import OpenRouterProvider
from backend.app.llm.exceptions import LLMProviderError

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """
    Registry & factory for creating and managing a single active LLMProvider instance.
    At any time, exactly one configured LLMProvider is active for processing requests.
    """

    _registry: Dict[str, Type[LLMProvider]] = {
        "ollama": OllamaProvider,
        "gemini": GeminiProvider,
        "openrouter": OpenRouterProvider,
    }

    _singleton_instance: Optional[LLMProvider] = None
    _current_provider_key: Optional[str] = None

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[LLMProvider]) -> None:
        """Register a new LLM provider class into the factory registry."""
        cls._registry[name.lower()] = provider_cls

    @classmethod
    def get_provider(
        cls,
        provider_name: Optional[str] = None,
        force_new: bool = False
    ) -> LLMProvider:
        """
        Returns the single active configured LLM provider instance.
        """
        resolved_name = (
            provider_name
            or os.getenv("LLM_PROVIDER")
            or os.getenv("AI_PROVIDER")
            or "ollama"
        ).lower()

        # Cache/singleton return if active provider has not changed
        if not force_new and cls._singleton_instance and cls._current_provider_key == resolved_name:
            return cls._singleton_instance

        if resolved_name not in cls._registry:
            supported = ", ".join(cls._registry.keys())
            raise LLMProviderError(
                f"Unsupported LLM provider '{resolved_name}'. Supported providers: {supported}",
                provider=resolved_name
            )

        provider_cls = cls._registry[resolved_name]
        logger.info(f"Initializing active LLM provider: {resolved_name.upper()}")

        instance = provider_cls()
        cls._singleton_instance = instance
        cls._current_provider_key = resolved_name
        return instance
