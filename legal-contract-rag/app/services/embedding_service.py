import httpx
import logging
from typing import List
from app.config import config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Embedding service using Ollama's local embedding model.
    Default model: nomic-embed-text  (pull with: ollama pull nomic-embed-text)

    Large documents are embedded in small batches to avoid Ollama timeouts.
    """

    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_EMBEDDING_MODEL
        self.batch_size = getattr(config, "OLLAMA_EMBEDDING_BATCH_SIZE", 10)
        self.timeout = float(getattr(config, "OLLAMA_EMBEDDING_TIMEOUT", 120))

    # ── single text ──────────────────────────────────────────────────────────

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text string."""
        return self._embed_batch([text])[0]

    # ── multiple texts ────────────────────────────────────────────────────────

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts.
        Processes in batches of `self.batch_size` to avoid Ollama timeouts on
        large documents.
        """
        all_embeddings: List[List[float]] = []
        total = len(texts)

        for start in range(0, total, self.batch_size):
            batch = texts[start: start + self.batch_size]
            batch_num = start // self.batch_size + 1
            total_batches = (total + self.batch_size - 1) // self.batch_size
            logger.info(
                f"Embedding batch {batch_num}/{total_batches} "
                f"({len(batch)} chunks)…"
            )
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    # ── internal ──────────────────────────────────────────────────────────────

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Call Ollama /api/embed for a single batch.
        Raises a descriptive Exception on failure.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": texts},
                )
                response.raise_for_status()
                data = response.json()
                # Response shape: {"embeddings": [[float, ...], ...]}
                embeddings = data.get("embeddings")
                if not embeddings:
                    raise ValueError(
                        f"Ollama returned unexpected embed response: {data}"
                    )
                return embeddings

        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}")
            raise Exception(
                "Ollama is not running. Start it with: ollama serve"
            )
        except httpx.TimeoutException:
            logger.error(
                f"Ollama embedding timed out after {self.timeout}s "
                f"for {len(texts)} texts"
            )
            raise Exception(
                f"Embedding timed out after {self.timeout}s. Try reducing CHUNK_SIZE in .env "
                f"(current: {config.CHUNK_SIZE})"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                error_msg = (
                    f"Ollama embedding model '{self.model}' is not pulled yet. "
                    f"Please run: ollama pull {self.model}"
                )
                logger.error(error_msg)
                raise Exception(error_msg) from e
            logger.error(f"HTTP error from Ollama embedding service: {e}")
            raise Exception(f"Ollama HTTP error ({e.response.status_code}): {e.response.text}") from e
        except Exception as e:
            logger.error(f"Error getting embeddings from Ollama: {e}")
            raise
