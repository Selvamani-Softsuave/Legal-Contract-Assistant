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


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM provider.
    Direct integration with Google Generative Language REST API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self._api_key = (
            api_key
            or os.getenv("API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("AI_API_KEY")
            or os.getenv("LLM_API_KEY")
        )
        self._default_model = model or os.getenv("LLM_MODEL", os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        self._timeout = timeout or float(os.getenv("LLM_TIMEOUT", os.getenv("GEMINI_TIMEOUT", "60.0")))
        self._cached_working_model: Optional[tuple[str, str]] = None

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return self._default_model

    def _build_payload(self, request: LLMRequest, model_name: str) -> dict:
        temperature = max(0.0, min(request.temperature, 1.0))
        generation_config: Dict[str, Any] = {"temperature": temperature}
        if request.max_tokens:
            generation_config["maxOutputTokens"] = request.max_tokens
        if request.stop_sequences:
            generation_config["stopSequences"] = request.stop_sequences

        if "gemma" in model_name.lower():
            combined_text = f"{request.system_prompt}\n\n{request.user_prompt}" if request.system_prompt else request.user_prompt
            return {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": combined_text}]
                    }
                ],
                "generationConfig": generation_config
            }

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": request.user_prompt}]
                }
            ],
            "generationConfig": generation_config
        }

        if request.system_prompt:
            payload["system_instruction"] = {
                "parts": [{"text": request.system_prompt}]
            }

        return payload

    def _extract_text_and_usage(self, resp_data: dict) -> tuple[str, Optional[LLMUsage], Optional[str]]:
        candidates = resp_data.get("candidates", [])
        if not candidates:
            return "", None, None

        candidate = candidates[0]
        finish_reason = candidate.get("finishReason")
        parts = candidate.get("content", {}).get("parts", [])
        content = "".join(p.get("text", "") for p in parts if "text" in p).strip()

        usage_metadata = resp_data.get("usageMetadata", {})
        usage = None
        if usage_metadata:
            usage = LLMUsage(
                prompt_tokens=usage_metadata.get("promptTokenCount"),
                completion_tokens=usage_metadata.get("candidatesTokenCount"),
                total_tokens=usage_metadata.get("totalTokenCount")
            )

        return content, usage, finish_reason

    async def generate(self, request: LLMRequest) -> LLMResponse:
        if not self._api_key:
            raise LLMAuthenticationError("GEMINI_API_KEY is not configured", provider=self.provider_name)

        requested_model = (request.model or self._default_model).replace("models/", "")
        timeout = request.timeout or self._timeout

        # 1. Try cached working model if matches
        if self._cached_working_model:
            version, m = self._cached_working_model
            url = f"https://generativelanguage.googleapis.com/{version}/models/{m}:generateContent?key={self._api_key}"
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, json=self._build_payload(request, m))
                    if resp.status_code == 200:
                        content, usage, finish_reason = self._extract_text_and_usage(resp.json())
                        if content:
                            return LLMResponse(
                                content=content,
                                provider=self.provider_name,
                                model=m,
                                finish_reason=finish_reason,
                                usage=usage,
                                raw_response=resp.json()
                            )
            except Exception:
                self._cached_working_model = None

        # 2. Try candidate list
        candidate_models = [requested_model]
        for fallback in ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro", "gemma-4-26b-a4b-it"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error = None
        for m in candidate_models:
            for version in ["v1beta", "v1"]:
                url = f"https://generativelanguage.googleapis.com/{version}/models/{m}:generateContent?key={self._api_key}"
                try:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        resp = await client.post(url, json=self._build_payload(request, m))
                        if resp.status_code == 200:
                            content, usage, finish_reason = self._extract_text_and_usage(resp.json())
                            if content:
                                self._cached_working_model = (version, m)
                                return LLMResponse(
                                    content=content,
                                    provider=self.provider_name,
                                    model=m,
                                    finish_reason=finish_reason,
                                    usage=usage,
                                    raw_response=resp.json()
                                )
                        elif resp.status_code in (401, 403):
                            raise LLMAuthenticationError(f"Gemini authentication failed ({resp.status_code}): {resp.text}", provider=self.provider_name)
                        elif resp.status_code == 429:
                            raise LLMRateLimitError(f"Gemini rate limit exceeded: {resp.text}", provider=self.provider_name)
                        else:
                            last_error = f"Gemini ({version}/{m}) error {resp.status_code}: {resp.text}"
                except (LLMAuthenticationError, LLMRateLimitError):
                    raise
                except httpx.TimeoutException as e:
                    last_error = f"Gemini timeout: {e}"
                except Exception as e:
                    last_error = str(e)

        raise LLMUnavailableError(f"Gemini generation failed: {last_error}", provider=self.provider_name)

    async def health_check(self) -> Dict[str, Any]:
        if not self._api_key:
            return {"status": "unhealthy", "provider": self.provider_name, "error": "API key missing"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={self._api_key}")
                status = "healthy" if resp.status_code == 200 else "unhealthy"
                return {"status": status, "provider": self.provider_name, "model": self._default_model}
        except Exception as e:
            return {"status": "unhealthy", "provider": self.provider_name, "error": str(e)}
