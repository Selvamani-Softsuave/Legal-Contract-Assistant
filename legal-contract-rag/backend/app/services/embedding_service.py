import httpx
import logging
import os
from typing import List
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.timeout = float(os.getenv("OLLAMA_EMBEDDING_TIMEOUT", "60.0"))

    def _resolve_config(self):
        provider = (os.getenv("EMBEDDING_PROVIDER") or os.getenv("AI_PROVIDER") or os.getenv("LLM_PROVIDER") or "OLLAMA").upper()

        defaults = {
            "OLLAMA": {
                "base_url": os.getenv("EMBEDDING_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")),
                "model": os.getenv("EMBEDDING_MODEL", os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")),
                "api_key": None
            },
            "OPENROUTER": {
                "base_url": os.getenv("EMBEDDING_BASE_URL", "https://openrouter.ai/api/v1"),
                "model": os.getenv("EMBEDDING_MODEL", os.getenv("OPENROUTER_EMBEDDING_MODEL", "jinaeu/jina-embeddings-v2-base-en")),
                "api_key": os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("AI_API_KEY")
            },
            "OPENAI": {
                "base_url": os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1"),
                "model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                "api_key": os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("AI_API_KEY")
            },
            "GEMINI": {
                "base_url": os.getenv("EMBEDDING_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"),
                "model": os.getenv("EMBEDDING_MODEL", "text-embedding-004"),
                "api_key": os.getenv("EMBEDDING_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("AI_API_KEY")
            }
        }

        if provider in defaults:
            cfg = defaults[provider]
        else:
            cfg = {
                "base_url": os.getenv("EMBEDDING_BASE_URL", "http://localhost:11434/v1"),
                "model": os.getenv("EMBEDDING_MODEL", "default"),
                "api_key": os.getenv("EMBEDDING_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("AI_API_KEY")
            }

        return provider, cfg["base_url"].rstrip("/"), cfg["model"], cfg["api_key"]

    def get_embedding(self, text: str) -> List[float]:
        embeddings = self.get_embeddings([text])
        if embeddings and len(embeddings) > 0:
            return embeddings[0]
        return []

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        provider, base_url, model, api_key = self._resolve_config()
        logger.info(f"Generating embeddings via provider '{provider}' using model '{model}'")

        if provider == "OLLAMA" and not base_url.endswith("/v1"):
            # Native Ollama API
            url = f"{base_url}/api/embed"
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json={"model": model, "input": texts})
                    resp.raise_for_status()
                    data = resp.json()
                    res = data.get("embeddings", [])
                    if res:
                        return res
                    raise ValueError(f"Ollama invalid embedding payload: {data}")
            except Exception as e:
                logger.error(f"Failed to generate embedding from native Ollama: {e}")
                raise ValueError("Failed to generate embedding")

        # OpenAI-Compatible API (OpenRouter, OpenAI, Gemini, Custom)
        url = f"{base_url}/embeddings"
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=headers, json={"model": model, "input": texts})
                resp.raise_for_status()
                data = resp.json()
                if "data" in data:
                    return [item["embedding"] for item in data["data"]]
                raise ValueError(f"Unexpected embedding payload: {data}")
        except Exception as e:
            logger.error(f"Error calling Embedding API ({provider}) at {url}: {e}")
            raise ValueError(f"Failed to generate embedding from provider ({provider})")
