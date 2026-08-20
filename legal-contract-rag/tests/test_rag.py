import os
import sys
import pytest
from unittest.mock import Mock, patch, AsyncMock

from backend.app.services.rag_service import EnterpriseRAGService
from backend.app.llm.base import LLMProvider
from backend.app.llm.models import LLMRequest, LLMResponse, LLMUsage


@pytest.mark.asyncio
async def test_legacy_rag_service_compatibility():
    """Test EnterpriseRAGService with mock dependencies maintaining legacy behavior."""
    mock_llm = Mock(spec=LLMProvider)
    mock_llm.provider_name = "ollama"
    mock_llm.default_model = "llama3.2"
    mock_llm.generate = AsyncMock(return_value=LLMResponse(
        content="The termination notice period is 30 days per Section 5.",
        provider="ollama",
        model="llama3.2",
        usage=LLMUsage(prompt_tokens=20, completion_tokens=10, total_tokens=30)
    ))

    mock_embedding = Mock()
    mock_embedding.get_embedding.return_value = [0.1, 0.2, 0.3]

    mock_vector = Mock()
    mock_vector.search_vectors.return_value = [
        {
            "id": "chunk1",
            "document": "This is a test chunk about termination notice.",
            "metadata": {
                "document_name": "contract.pdf",
                "page": 5,
                "section": "Section 5"
            },
            "distance": 0.1
        }
    ]

    rag_service = EnterpriseRAGService(
        llm_provider=mock_llm,
        embedding_service=mock_embedding,
        vector_client=mock_vector
    )

    result = await rag_service.answer_question(
        question="What is the termination notice period?",
        conversation_id="test-conv-1"
    )

    assert "answer" in result
    assert "sources" in result
    assert result["answer"] == "The termination notice period is 30 days per Section 5."
    assert len(result["sources"]) == 1
    assert result["sources"][0]["document_name"] == "contract.pdf"
    assert result["sources"][0]["page_number"] == 5
