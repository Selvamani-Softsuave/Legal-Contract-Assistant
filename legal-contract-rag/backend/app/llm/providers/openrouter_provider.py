import os
import httpx
import logging
from typing import Dict, Any, Optional
from backend.app.llm.base import LLMProvider
from backend.app.llm.models import LLMRequest, LLMResponse, LLMUsage
from backend.app.llm.exceptions import (
    LLMProviderError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUnavailableError,
    LLMInvalidResponseError,
)

logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter API provider (OpenAI-compatible gateway).
    Treats OpenRouter as a gateway/provider and normalizes models like meta-llama/llama-3.1-8b-instruct.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self._api_key = (
            api_key
            or os.getenv("API_KEY")
            or os.getenv("OPENROUTER_API_KEY")
            or os.getenv("AI_API_KEY")
            or os.getenv("LLM_API_KEY")
        )
        self._base_url = (
            base_url
            or os.getenv("LLM_BASE_URL")
            or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        ).rstrip("/")
        self._default_model = (
            model
            or os.getenv("LLM_MODEL")
            or os.getenv("OPENROUTER_MODEL", "openrouter/free")
        )
        self._timeout = timeout or float(os.getenv("LLM_TIMEOUT", os.getenv("OPENROUTER_TIMEOUT", "60.0")))

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def default_model(self) -> str:
        return self._default_model

    async def generate(self, request: LLMRequest) -> LLMResponse:
        if not self._api_key:
            raise LLMAuthenticationError("OPENROUTER_API_KEY is not configured", provider=self.provider_name)

        model = request.model or self._default_model
        timeout = request.timeout or self._timeout
        url = f"{self._base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Legal Contract RAG",
            "Content-Type": "application/json"
        }

        messages = []
        if request.messages:
            messages = [{"role": m.role, "content": m.content} for m in request.messages]
        else:
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.user_prompt})

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        if request.stop_sequences:
            payload["stop"] = request.stop_sequences
        if request.response_format:
            payload["response_format"] = request.response_format

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code in (401, 403):
                    raise LLMAuthenticationError(f"OpenRouter auth failure ({resp.status_code}): {resp.text}", provider=self.provider_name)
                elif resp.status_code == 429:
                    raise LLMRateLimitError(f"OpenRouter rate limit exceeded: {resp.text}", provider=self.provider_name)
                elif resp.status_code >= 500:
                    raise LLMUnavailableError(f"OpenRouter service error ({resp.status_code}): {resp.text}", provider=self.provider_name)
                resp.raise_for_status()

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    raise LLMInvalidResponseError("OpenRouter returned no choices", provider=self.provider_name, raw_error=data)

                choice = choices[0]
                content = choice.get("message", {}).get("content", "")
                finish_reason = choice.get("finish_reason")

                raw_usage = data.get("usage", {})
                usage = None
                if raw_usage:
                    usage = LLMUsage(
                        prompt_tokens=raw_usage.get("prompt_tokens"),
                        completion_tokens=raw_usage.get("completion_tokens"),
                        total_tokens=raw_usage.get("total_tokens")
                    )

                return LLMResponse(
                    content=content or "",
                    provider=self.provider_name,
                    model=data.get("model", model),
                    finish_reason=finish_reason,
                    usage=usage,
                    metadata={"id": data.get("id")},
                    raw_response=data
                )
        except (LLMAuthenticationError, LLMRateLimitError, LLMUnavailableError, LLMInvalidResponseError):
            raise
        except httpx.TimeoutException as e:
            logger.error(f"OpenRouter request timed out after {timeout}s: {e}")
            raise LLMTimeoutError(f"OpenRouter request timed out: {e}", provider=self.provider_name, raw_error=e)
        except Exception as e:
            logger.error(f"OpenRouter generation error: {e}")
            raise LLMInvalidResponseError(f"OpenRouter generation error: {e}", provider=self.provider_name, raw_error=e)

    async def health_check(self) -> Dict[str, Any]:
        if not self._api_key:
            return {"status": "unhealthy", "provider": self.provider_name, "error": "API key missing"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self._base_url}/auth/key",
                    headers={"Authorization": f"Bearer {self._api_key}"}
                )
                status = "healthy" if resp.status_code == 200 else "unhealthy"
                return {"status": status, "provider": self.provider_name, "model": self._default_model}
        except Exception as e:
            return {"status": "unhealthy", "provider": self.provider_name, "error": str(e)}
