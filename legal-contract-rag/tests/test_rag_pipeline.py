import pytest
from unittest.mock import Mock, AsyncMock
from backend.app.services.rag_service import EnterpriseRAGService
from backend.app.llm.base import LLMProvider
from backend.app.llm.models import LLMRequest, LLMResponse, LLMUsage
from backend.app.llm.exceptions import LLMTimeoutError, LLMAuthenticationError
from backend.app.rag.context_builder import ContextBuilder
from backend.app.rag.citation_handler import CitationHandler
from backend.app.rag.prompt_builder import LegalRAGPromptBuilder
from backend.app.rag.response_validator import ResponseValidator


class MockLLMProvider(LLMProvider):
    def __init__(self, response_content="This is a test answer.", provider="mock_llm", model="mock_model"):
        self._content = response_content
        self._provider = provider
        self._model = model
        self.last_request = None

    @property
    def provider_name(self) -> str:
        return self._provider

    @property
    def default_model(self) -> str:
        return self._model

    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.last_request = request
        return LLMResponse(
            content=self._content,
            provider=self._provider,
            model=self._model,
            usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        )

    async def health_check(self):
        return {"status": "healthy", "provider": self._provider}


@pytest.mark.asyncio
async def test_rag_service_with_retrieved_context():
    mock_llm = MockLLMProvider("The term of the agreement is 2 years per Section 1.2.")
    mock_embedding = Mock()
    mock_embedding.get_embedding.return_value = [0.1, 0.2, 0.3]

    mock_vector = Mock()
    mock_vector.search_vectors.return_value = [
        {
            "id": "chunk-101",
            "document": "This Agreement shall remain in effect for two (2) years.",
            "metadata": {
                "document_name": "Master_Services_Agreement.pdf",
                "page": 2,
                "section": "1.2 Term",
                "clause": "Duration"
            },
            "distance": 0.15
        }
    ]

    service = EnterpriseRAGService(
        llm_provider=mock_llm,
        embedding_service=mock_embedding,
        vector_client=mock_vector
    )

    res = await service.answer_question("What is the agreement duration?", conversation_id="conv-1")

    assert res["answer"] == "The term of the agreement is 2 years per Section 1.2."
    assert len(res["sources"]) == 1
    assert res["sources"][0]["document_name"] == "Master_Services_Agreement.pdf"
    assert res["sources"][0]["section"] == "1.2 Term"
    assert res["sources"][0]["page_number"] == 2
    assert mock_llm.last_request is not None
    assert "Master_Services_Agreement.pdf" in mock_llm.last_request.user_prompt


@pytest.mark.asyncio
async def test_rag_service_empty_retrieval():
    mock_llm = MockLLMProvider("Should not be called")
    mock_embedding = Mock()
    mock_embedding.get_embedding.return_value = [0.1, 0.2, 0.3]
    mock_vector = Mock()
    mock_vector.search_vectors.return_value = []

    service = EnterpriseRAGService(
        llm_provider=mock_llm,
        embedding_service=mock_embedding,
        vector_client=mock_vector
    )

    res = await service.answer_question("What is the penalty fee?", conversation_id="conv-2")
    assert res["answer"] == "I don't know based on the provided documents."
    assert res["sources"] == []
    assert mock_llm.last_request is None  # LLM must not be called on empty retrieval


@pytest.mark.asyncio
async def test_rag_service_provider_timeout():
    failing_llm = Mock()
    failing_llm.generate = AsyncMock(side_effect=LLMTimeoutError("Request timed out", provider="gemini"))

    mock_embedding = Mock()
    mock_embedding.get_embedding.return_value = [0.1, 0.2]
    mock_vector = Mock()
    mock_vector.search_vectors.return_value = [
        {"id": "c1", "document": "Sample context", "metadata": {"document_name": "doc.pdf", "page": 1}, "distance": 0.1}
    ]

    service = EnterpriseRAGService(
        llm_provider=failing_llm,
        embedding_service=mock_embedding,
        vector_client=mock_vector
    )

    res = await service.answer_question("Query", conversation_id="conv-3")
    assert "Error generating answer from LLM provider (gemini)" in res["answer"]


def test_response_validator():
    # Normal response
    assert ResponseValidator.validate_and_normalize("Governing law is NY.") == "Governing law is NY."
    # Response wrapped with Answer: prefix
    assert ResponseValidator.validate_and_normalize("Internal thoughts\nAnswer: Payment is due in 30 days.") == "Payment is due in 30 days."
    # Refusal normalization
    assert ResponseValidator.validate_and_normalize("The provided context does not contain this info.") == "I don't know based on the provided documents."
    # Empty string
    assert ResponseValidator.validate_and_normalize("") == "I don't know based on the provided documents."
