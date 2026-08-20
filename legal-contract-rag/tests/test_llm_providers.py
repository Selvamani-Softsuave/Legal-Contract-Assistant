import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.llm.models import LLMRequest, LLMResponse, LLMUsage
from backend.app.llm.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from backend.app.llm.providers.ollama_provider import OllamaProvider
from backend.app.llm.providers.gemini_provider import GeminiProvider
from backend.app.llm.providers.openrouter_provider import OpenRouterProvider
from backend.app.llm.factory import LLMProviderFactory


@pytest.mark.asyncio
async def test_ollama_provider_conformance():
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")
    assert provider.provider_name == "ollama"
    assert provider.default_model == "llama3.2"

    mock_resp_data = {
        "response": "The contract terminates in 30 days.",
        "done": True,
        "prompt_eval_count": 25,
        "eval_count": 10
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_resp_data
    mock_response.raise_for_status.return_value = None

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        req = LLMRequest(user_prompt="What is notice period?", system_prompt="Answer briefly.")
        res = await provider.generate(req)

        assert isinstance(res, LLMResponse)
        assert res.content == "The contract terminates in 30 days."
        assert res.provider == "ollama"
        assert res.model == "llama3.2"
        assert res.usage.total_tokens == 35


@pytest.mark.asyncio
async def test_gemini_provider_conformance():
    provider = GeminiProvider(api_key="test_gemini_key", model="gemini-1.5-flash")
    assert provider.provider_name == "gemini"
    assert provider.default_model == "gemini-1.5-flash"

    mock_resp_data = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "The liability limit is $1,000,000."}]
                },
                "finishReason": "STOP"
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 50,
            "candidatesTokenCount": 15,
            "totalTokenCount": 65
        }
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_resp_data

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        req = LLMRequest(user_prompt="What is the liability cap?")
        res = await provider.generate(req)

        assert isinstance(res, LLMResponse)
        assert res.content == "The liability limit is $1,000,000."
        assert res.provider == "gemini"
        assert res.finish_reason == "STOP"
        assert res.usage.total_tokens == 65


@pytest.mark.asyncio
async def test_openrouter_provider_conformance():
    provider = OpenRouterProvider(api_key="test_or_key", model="meta-llama/llama-3.1-8b-instruct")
    assert provider.provider_name == "openrouter"
    assert provider.default_model == "meta-llama/llama-3.1-8b-instruct"

    mock_resp_data = {
        "id": "gen-12345",
        "model": "meta-llama/llama-3.1-8b-instruct",
        "choices": [
            {
                "message": {"role": "assistant", "content": "Governing law is Delaware."},
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 40,
            "completion_tokens": 12,
            "total_tokens": 52
        }
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_resp_data
    mock_response.raise_for_status.return_value = None

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        req = LLMRequest(user_prompt="What is the governing law?")
        res = await provider.generate(req)

        assert isinstance(res, LLMResponse)
        assert res.content == "Governing law is Delaware."
        assert res.provider == "openrouter"
        assert res.usage.total_tokens == 52


def test_factory_switching():
    # Test factory returns Ollama by default
    p1 = LLMProviderFactory.get_provider("ollama", force_new=True)
    assert isinstance(p1, OllamaProvider)

    # Test factory returns Gemini
    p2 = LLMProviderFactory.get_provider("gemini", force_new=True)
    assert isinstance(p2, GeminiProvider)

    # Test factory returns OpenRouter
    p3 = LLMProviderFactory.get_provider("openrouter", force_new=True)
    assert isinstance(p3, OpenRouterProvider)
