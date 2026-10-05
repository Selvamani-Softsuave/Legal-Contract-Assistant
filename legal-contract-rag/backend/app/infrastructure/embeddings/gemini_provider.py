import httpx
import logging
from typing import List
from backend.app.infrastructure.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-embedding-001", timeout: float = 60.0):
        super().__init__(model_name=model_name, timeout=timeout)
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai"

    @property
    def provider_name(self) -> str:
        return "gemini"

    def get_embedding(self, text: str) -> List[float]:
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "input": text
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            raise
