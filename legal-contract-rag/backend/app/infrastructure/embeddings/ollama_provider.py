import httpx
import logging
from typing import List
from backend.app.infrastructure.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "nomic-embed-text", timeout: float = 60.0):
        super().__init__(model_name=model_name, timeout=timeout)
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "ollama"

    def get_embedding(self, text: str) -> List[float]:
        url = f"{self.base_url}/api/embeddings"
        payload = {"model": self.model_name, "prompt": text}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("embedding", [])
        except Exception as e:
            logger.error(f"Ollama embedding error ({url}): {e}")
            raise
