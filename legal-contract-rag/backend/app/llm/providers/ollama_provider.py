import os
import httpx
import logging
from typing import Dict, Any, Optional
from backend.app.llm.base import LLMProvider
from backend.app.llm.models import LLMRequest, LLMResponse, LLMUsage
from backend.app.llm.exceptions import (
    LLMProviderError,
    LLMTimeoutError,
    LLMUnavailableError,
    LLMInvalidResponseError,
)

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Native Ollama LLM provider.
    Communicates directly with Ollama daemon REST API (/api/generate or /api/chat).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self._base_url = (
            base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ).rstrip("/")
        self._default_model = model or os.getenv("OLLAMA_MODEL", os.getenv("LLM_MODEL", "llama3.2"))
        self._timeout = timeout or float(os.getenv("OLLAMA_TIMEOUT", os.getenv("LLM_TIMEOUT", "120.0")))

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return self._default_model

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self._default_model
        timeout = request.timeout or self._timeout
        url = f"{self._base_url}/api/generate"

        full_prompt = request.user_prompt
        if request.system_prompt:
            payload = {
                "model": model,
                "system": request.system_prompt,
                "prompt": request.user_prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                }
            }
        else:
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                }
            }

        if request.stop_sequences:
            payload["options"]["stop"] = request.stop_sequences

        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code >= 500:
                    raise LLMUnavailableError(
                        f"Ollama server error ({resp.status_code}): {resp.text}",
                        provider=self.provider_name
                    )
                resp.raise_for_status()
                data = resp.json()

                content = data.get("response", "")
                prompt_eval_count = data.get("prompt_eval_count")
                eval_count = data.get("eval_count")
                usage = LLMUsage(
                    prompt_tokens=prompt_eval_count,
                    completion_tokens=eval_count,
                    total_tokens=(prompt_eval_count + eval_count) if (prompt_eval_count is not None and eval_count is not None) else None
                )

                return LLMResponse(
                    content=content,
                    provider=self.provider_name,
                    model=model,
                    finish_reason=data.get("done_reason") or ("stop" if data.get("done") else None),
                    usage=usage,
                    metadata={"total_duration": data.get("total_duration")},
                    raw_response=data
                )
        except httpx.TimeoutException as e:
            logger.error(f"Ollama request timed out after {timeout}s: {e}")
            raise LLMTimeoutError(f"Ollama request timed out: {e}", provider=self.provider_name, raw_error=e)
        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to Ollama at {self._base_url}: {e}")
            raise LLMUnavailableError(f"Cannot connect to Ollama server at {self._base_url}: {e}", provider=self.provider_name, raw_error=e)
        except LLMProviderError:
            raise
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise LLMInvalidResponseError(f"Ollama generation error: {e}", provider=self.provider_name, raw_error=e)

    async def health_check(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                status = "healthy" if resp.status_code == 200 else "unhealthy"
                return {
                    "status": status,
                    "provider": self.provider_name,
                    "model": self._default_model,
                    "base_url": self._base_url
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider_name,
                "model": self._default_model,
                "error": str(e)
            }
