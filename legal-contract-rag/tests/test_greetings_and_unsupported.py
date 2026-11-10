"""
Pytest Test Suite for Greeting Handling, Dynamic Unsupported Query Response Generation, and Error Handling.
Fulfills Task 1, Task 2, and Task 6 specifications.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from backend.app.services.rag_service import EnterpriseRAGService
from backend.app.llm.base import LLMProvider
from backend.app.llm.models import LLMRequest, LLMResponse
from backend.app.llm.exceptions import LLMProviderError, LLMTimeoutError
from backend.app.rag.response_validator import ResponseValidator


class MockTestLLMProvider(LLMProvider):
    def __init__(self, response_generator=None):
        self.response_generator = response_generator
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return "mock_test_provider"

    @property
    def default_model(self) -> str:
        return "mock-model"

    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "provider": self.provider_name}

    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.call_count += 1
        if callable(self.response_generator):
            content = self.response_generator(request, self.call_count)
        else:
            content = "Mock LLM output response."
        return LLMResponse(content=content, provider=self.provider_name, model=self.default_model)


# ─── 1. Task 1: Greeting Detection Unit Tests ─────────────────────────────

@pytest.mark.parametrize("greeting", [
    "Hello",
    "hello",
    "Hi",
    "hi",
    "hii",
    "hiii",
    "Hey",
    "heyy",
    "Good Morning",
    "good morning!",
    "Good Afternoon",
    "good evening",
    "good day",
    "howdy",
    "welcome",
    "nice to meet you"
])
def test_greeting_detection(greeting: str):
    """Verifies that common greetings in various forms are accurately recognized."""
    assert EnterpriseRAGService.is_conversational_or_general_query(greeting) is True


@pytest.mark.parametrize("general_query", [
    "who are you",
    "what is your name",
    "what is the name of this application",
    "what can you do for me",
    "tell me about yourself",
    "how does this work",
    "what are your capabilities",
    "how are you",
    "thank you",
    "whats up"
])
def test_general_identity_query_detection(general_query: str):
    """Verifies that persona, identity, and application capability questions are detected."""
    assert EnterpriseRAGService.is_conversational_or_general_query(general_query) is True


@pytest.mark.parametrize("contract_query", [
    "What is the late payment interest rate under the Northwind Master Services Agreement?",
    "Does Section 12 require indemnification for third-party IP claims?",
    "What is the governing law of the Vertex Retail Agreement?",
    "When does Amendment No. 2 take effect?"
])
def test_contractual_queries_not_misidentified_as_greetings(contract_query: str):
    """Verifies that substantive legal contract queries are NOT identified as greetings."""
    assert EnterpriseRAGService.is_conversational_or_general_query(contract_query) is False


# ─── 2. Task 1: Greeting Response Generation Unit Tests ───────────────────

@pytest.mark.asyncio
async def test_greeting_response_generation():
    """Tests that greetings generate warm, conversational responses identifying as the assistant."""
    mock_responses = [
        "Hello! I am your Enterprise Legal Contract Assistant. How can I assist you with your legal documents today?",
        "Good morning! I am the Enterprise Legal Contract Assistant, ready to help you analyze contracts and amendments."
    ]

    def gen(request, count):
        return mock_responses[(count - 1) % len(mock_responses)]

    llm = MockTestLLMProvider(response_generator=gen)
    service = EnterpriseRAGService(llm_provider=llm)

    res1 = await service._handle_general_query("Hello", conversation_id="conv-1")
    assert "Legal Contract Assistant" in res1["answer"]
    assert res1["sources"] == []

    res2 = await service._handle_general_query("Good Morning", conversation_id="conv-1")
    assert "Legal Contract Assistant" in res2["answer"]
    assert res2["sources"] == []
    assert res1["answer"] != res2["answer"]


# ─── 3. Task 2: Unique Response Generation for Unsupported Questions ─────

@pytest.mark.asyncio
async def test_unsupported_question_generates_dynamic_response():
    """
    Tests that unsupported questions (e.g. weather, sports) generate dynamic
    LLM responses explaining the information is not in the contracts.
    """
    mock_responses = {
        1: "I'm sorry, but I do not have access to weather data as my focus is on analyzing your legal contracts. Please ask about terms or clauses in your agreements.",
        2: "Weather information is not available in the uploaded legal documents. Feel free to ask about obligations, liabilities, or governing laws in your contracts."
    }

    def gen(request, count):
        return mock_responses.get(count, "The requested information is outside the scope of available agreements.")

    llm = MockTestLLMProvider(response_generator=gen)
    service = EnterpriseRAGService(llm_provider=llm)

    unsupported_query = "What is the weather today in Tokyo?"

    # First call
    result_1 = await service._handle_unsupported_query(unsupported_query, conversation_id="conv-unsupported")
    assert "weather" in result_1["answer"].lower() or "contracts" in result_1["answer"].lower()
    assert result_1["sources"] == []

    # Second call (repeated same question)
    result_2 = await service._handle_unsupported_query(unsupported_query, conversation_id="conv-unsupported")
    assert "weather" in result_2["answer"].lower() or "contracts" in result_2["answer"].lower()

    # Verify responses are dynamic and distinct even on identical questions
    assert result_1["answer"] != result_2["answer"]


@pytest.mark.asyncio
async def test_empty_retrieval_triggers_unsupported_handler():
    """
    Integration test: When vector search returns 0 results for a contract query,
    the pipeline automatically routes to dynamic unsupported question generation.
    """
    mock_llm = MockTestLLMProvider(
        response_generator=lambda req, cnt: "That topic is not mentioned in the active contracts. Please check your uploaded agreements."
    )
    mock_vector = MagicMock()
    mock_vector.search_vectors.return_value = []  # 0 chunks found

    mock_embedding = MagicMock()
    mock_embedding.get_embedding.return_value = [0.1] * 3072

    service = EnterpriseRAGService(
        llm_provider=mock_llm,
        vector_client=mock_vector,
        embedding_service=mock_embedding
    )

    result = await service.answer_question(
        question="What is the policy on company bicycles in 2045?",
        conversation_id="conv-empty"
    )

    assert "contracts" in result["answer"].lower() or "not mentioned" in result["answer"].lower()
    assert result["sources"] == []


# ─── 4. Error Handling Unit Tests ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_error_handling_when_llm_times_out():
    """
    Verifies that when the LLM provider fails or times out during greeting or
    unsupported question generation, the service gracefully returns a diversified fallback.
    """
    failing_llm = MagicMock()
    failing_llm.generate = AsyncMock(side_effect=LLMTimeoutError("Request to LLM timed out after 30s"))

    service = EnterpriseRAGService(llm_provider=failing_llm)

    # Greeting fallback check
    greeting_res = await service._handle_general_query("Hi", conversation_id="conv-err")
    assert "Legal Contract Assistant" in greeting_res["answer"]
    assert greeting_res["sources"] == []

    # Unsupported question fallback check
    unsupported_res = await service._handle_unsupported_query("Who won the 1994 World Cup?", conversation_id="conv-err")
    assert len(unsupported_res["answer"]) > 20
    assert "contracts" in unsupported_res["answer"].lower() or "documents" in unsupported_res["answer"].lower()


@pytest.mark.asyncio
async def test_error_handling_in_main_rag_answer_question():
    """
    Verifies that provider errors during RAG generation return meaningful error messages
    rather than crashing the application or returning unhandled 500 exceptions.
    """
    failing_llm = MagicMock()
    failing_llm.generate = AsyncMock(side_effect=LLMProviderError("gemini", "Internal service error 500"))

    mock_vector = MagicMock()
    mock_vector.search_vectors.return_value = [{
        "id": "c1",
        "document": "Section 1.1 Terms",
        "metadata": {"document_name": "Agreement.pdf", "page": 1}
    }]

    mock_embedding = MagicMock()
    mock_embedding.get_embedding.return_value = [0.1] * 3072

    service = EnterpriseRAGService(
        llm_provider=failing_llm,
        vector_client=mock_vector,
        embedding_service=mock_embedding
    )

    result = await service.answer_question(
        question="What are the payment terms?",
        conversation_id="conv-err-rag"
    )

    assert "Error generating answer from LLM provider" in result["answer"]
    assert len(result["sources"]) == 1
