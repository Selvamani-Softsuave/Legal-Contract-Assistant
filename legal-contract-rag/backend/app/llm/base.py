from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any
from backend.app.llm.models import LLMRequest, LLMResponse


class LLMProvider(ABC):
    """
    Generic, provider-independent contract for LLM generation.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'ollama', 'gemini', 'openrouter')."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model identifier for this provider."""
        pass

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Executes a single generation call and returns normalized LLMResponse.
        """
        pass

    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """
        Optional streaming interface for future streaming support.
        """
        response = await self.generate(request)
        yield response.content

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Performs connectivity/health check for the configured provider.
        """
        pass
