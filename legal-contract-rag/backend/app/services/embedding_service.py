import logging
from typing import List, Optional
from backend.app.domain.ports.embedding_provider_port import IEmbeddingProviderPort
from backend.app.infrastructure.embeddings.factory import EmbeddingProviderFactory

logger = logging.getLogger(__name__)


class EmbeddingService(IEmbeddingProviderPort):
    """
    Enterprise Embedding Service Facade.
    Delegates to pluggable IEmbeddingProvider implementations (Ollama, Gemini, OpenAI)
    configured via factory and environment settings.
    """

    def __init__(self, provider: Optional[IEmbeddingProviderPort] = None):
        self._provider = provider or EmbeddingProviderFactory.get_provider()

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    @property
    def model_name(self) -> str:
        return self._provider.model_name

    def get_embedding(self, text: str) -> List[float]:
        return self._provider.get_embedding(text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self._provider.get_embeddings(texts)
