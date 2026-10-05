from abc import ABC, abstractmethod
from typing import List
from backend.app.domain.ports.embedding_provider_port import IEmbeddingProviderPort


class BaseEmbeddingProvider(IEmbeddingProviderPort, ABC):
    """Abstract base class for all embedding providers."""

    def __init__(self, model_name: str, timeout: float = 60.0):
        self._model_name = model_name
        self.timeout = timeout

    @property
    def model_name(self) -> str:
        return self._model_name

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Default batch embedding implementation delegating to get_embedding sequentially."""
        return [self.get_embedding(t) for t in texts]
