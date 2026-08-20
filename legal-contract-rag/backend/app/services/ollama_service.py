import logging
from typing import Optional, Dict, Any
from backend.app.llm.factory import LLMProviderFactory
from backend.app.llm.models import LLMRequest

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Backward-compatibility bridge.
    Delegates to the modern LLMProvider architecture while preserving the old interface.
    """

    def __init__(self, provider_name: Optional[str] = None):
        self.provider = LLMProviderFactory.get_provider(provider_name or "ollama")

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        request = LLMRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.0
        )
        response = await self.provider.generate(request)
        return response.content

    async def health_check(self) -> Dict[str, Any]:
        return await self.provider.health_check()
