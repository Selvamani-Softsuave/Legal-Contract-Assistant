import os
import logging
from typing import Optional
from backend.app.core.config import settings
from backend.app.domain.ports.embedding_provider_port import IEmbeddingProviderPort
from backend.app.infrastructure.embeddings.ollama_provider import OllamaEmbeddingProvider
from backend.app.infrastructure.embeddings.gemini_provider import GeminiEmbeddingProvider
from backend.app.infrastructure.embeddings.openai_provider import OpenAIEmbeddingProvider

logger = logging.getLogger(__name__)


class EmbeddingProviderFactory:
    """Factory creating and caching pluggable embedding providers."""

    _instance: Optional[IEmbeddingProviderPort] = None

    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> IEmbeddingProviderPort:
        name = (provider_name or getattr(settings, "EMBEDDING_PROVIDER", None) or getattr(settings, "LLM_PROVIDER", "OLLAMA")).lower()

        if name == "gemini":
            api_key = settings.API_KEY or os.getenv("AI_API_KEY") or os.getenv("GEMINI_API_KEY")
            model = settings.EMBEDDING_MODEL or "gemini-embedding-001"
            return GeminiEmbeddingProvider(api_key=api_key or "", model_name=model)

        elif name in ("openrouter", "openai"):
            api_key = settings.API_KEY or os.getenv("AI_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
            base_url = "https://openrouter.ai/api/v1" if name == "openrouter" else "https://api.openai.com/v1"
            default_model = "jinaeu/jina-embeddings-v2-base-en" if name == "openrouter" else "text-embedding-3-small"
            model = settings.EMBEDDING_MODEL or default_model
            return OpenAIEmbeddingProvider(api_key=api_key or "", base_url=base_url, model_name=model)

        else:
            # Default to Ollama
            base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
            model = getattr(settings, "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
            timeout = getattr(settings, "OLLAMA_EMBEDDING_TIMEOUT", 120.0)
            return OllamaEmbeddingProvider(base_url=base_url, model_name=model, timeout=timeout)
