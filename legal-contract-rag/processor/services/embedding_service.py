import httpx
import logging
import os
from typing import List

logger = logging.getLogger(__name__)

class ProcessorEmbeddingService:
    def __init__(self):
        self.batch_size = int(os.getenv("OLLAMA_EMBEDDING_BATCH_SIZE", "10"))
        self.timeout = float(os.getenv("OLLAMA_EMBEDDING_TIMEOUT", "120"))
        self._st_model = None

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

        # 1. Try SentenceTransformers if available locally
        try:
            from sentence_transformers import SentenceTransformer
            if self._st_model is None:
                self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = self._st_model.encode(texts).tolist()
            return embeddings
        except Exception:
            pass

        # 2. Dynamic Provider Resolution
        provider, base_url, model, api_key = self._resolve_config()
        logger.info(f"Processor generating embeddings via provider '{provider}' using model '{model}'")

        if provider == "OLLAMA" and not base_url.endswith("/v1"):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(
                        f"{base_url}/api/embed",
                        json={"model": model, "input": texts}
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    res = data.get("embeddings", [])
                    if res:
                        return res
                    raise ValueError(f"Ollama invalid embedding payload: {data}")
            except Exception as e:
                logger.warning(f"Processor native Ollama failed: {e}. Falling back to mock vectors.")
                return [[0.01 * (i + 1)] * 384 for i in range(len(texts))]

        if provider == "GEMINI":
            candidate_models = []
            if model:
                candidate_models.append(model.replace("models/", ""))
            for fallback in ["gemini-embedding-001", "embedding-001", "text-embedding-004"]:
                if fallback not in candidate_models:
                    candidate_models.append(fallback)

            last_err = None
            for m in candidate_models:
                try:
                    with httpx.Client(timeout=self.timeout) as client:
                        if len(texts) == 1:
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:embedContent?key={api_key}"
                            payload = {"model": f"models/{m}", "content": {"parts": [{"text": texts[0]}]}}
                            resp = client.post(url, json=payload)
                            if resp.status_code == 200:
                                data = resp.json()
                                if "embedding" in data and "values" in data["embedding"]:
                                    return [data["embedding"]["values"]]
                            else:
                                last_err = f"Gemini ({m}) error {resp.status_code}: {resp.text}"
                        else:
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:batchEmbedContents?key={api_key}"
                            requests_payload = [
                                {"model": f"models/{m}", "content": {"parts": [{"text": t}]}}
                                for t in texts
                            ]
                            resp = client.post(url, json={"requests": requests_payload})
                            if resp.status_code == 200:
                                data = resp.json()
                                if "embeddings" in data:
                                    return [item["values"] for item in data["embeddings"]]
                            else:
                                last_err = f"Gemini ({m}) batch error {resp.status_code}: {resp.text}"
                except Exception as e:
                    last_err = str(e)

            logger.warning(f"Processor Gemini embedding failed across {candidate_models}: {last_err}. Falling back to mock vectors.")
            return [[0.01 * (i + 1)] * 384 for i in range(len(texts))]

        # 3. OpenAI-Compatible API (OpenRouter, OpenAI, Custom)
        url = f"{base_url}/embeddings"
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    url,
                    headers=headers,
                    json={"model": model, "input": texts}
                )
                if resp.status_code >= 400:
                    logger.error(f"Processor embedding API error ({resp.status_code}): {resp.text}")
                resp.raise_for_status()
                data = resp.json()
                if "data" in data:
                    return [item["embedding"] for item in data["data"]]
                raise ValueError(f"Unexpected embedding payload: {data}")
        except Exception as e:
            logger.warning(f"Processor embedding API ({provider}) failed: {e}. Falling back to mock vectors.")
            return [[0.01 * (i + 1)] * 384 for i in range(len(texts))]
