import pytest
from unittest.mock import MagicMock, patch
from backend.app.infrastructure.embeddings.factory import EmbeddingProviderFactory
from backend.app.infrastructure.embeddings.ollama_provider import OllamaEmbeddingProvider
from backend.app.infrastructure.embeddings.gemini_provider import GeminiEmbeddingProvider
from backend.app.infrastructure.embeddings.openai_provider import OpenAIEmbeddingProvider
from backend.app.services.embedding_service import EmbeddingService


def test_embedding_factory_ollama():
    provider = EmbeddingProviderFactory.get_provider("ollama")
    assert isinstance(provider, OllamaEmbeddingProvider)
    assert provider.provider_name == "ollama"


def test_embedding_factory_gemini():
    with patch("backend.app.core.config.settings.API_KEY", "test-key"):
        provider = EmbeddingProviderFactory.get_provider("gemini")
        assert isinstance(provider, GeminiEmbeddingProvider)
        assert provider.provider_name == "gemini"


def test_embedding_factory_openai():
    with patch("backend.app.core.config.settings.API_KEY", "test-key"):
        provider = EmbeddingProviderFactory.get_provider("openai")
        assert isinstance(provider, OpenAIEmbeddingProvider)
        assert provider.provider_name == "openai"


def test_embedding_service_facade_delegation():
    mock_provider = MagicMock()
    mock_provider.get_embedding.return_value = [0.1, 0.2, 0.3]
    mock_provider.get_embeddings.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    mock_provider.provider_name = "mock_provider"
    mock_provider.model_name = "mock-model-v1"

    service = EmbeddingService(provider=mock_provider)
    assert service.provider_name == "mock_provider"
    assert service.model_name == "mock-model-v1"

    res = service.get_embedding("hello")
    assert res == [0.1, 0.2, 0.3]
    mock_provider.get_embedding.assert_called_once_with("hello")

    batch_res = service.get_embeddings(["text1", "text2"])
    assert len(batch_res) == 2
    mock_provider.get_embeddings.assert_called_once_with(["text1", "text2"])
