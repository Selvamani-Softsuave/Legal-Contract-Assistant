from abc import ABC, abstractmethod
from typing import List


class IEmbeddingProviderPort(ABC):
    """Port for text embedding providers (Ollama, Gemini, OpenAI, etc.)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the embedding provider."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Active embedding model identifier."""
        pass

    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for a single text string."""
        pass

    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a batch of text strings."""
        pass
