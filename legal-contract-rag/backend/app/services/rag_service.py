import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.infrastructure.vector.vector_client import VectorClient
from backend.app.services.embedding_service import EmbeddingService
from backend.app.repositories.chat_repository import ChatRepository
from backend.app.core.config import settings

from backend.app.llm.base import LLMProvider
from backend.app.llm.factory import LLMProviderFactory
from backend.app.llm.models import LLMRequest
from backend.app.llm.exceptions import LLMProviderError

from backend.app.rag.context_builder import ContextBuilder
from backend.app.rag.citation_handler import CitationHandler
from backend.app.rag.prompt_builder import LegalRAGPromptBuilder
from backend.app.rag.response_validator import ResponseValidator

logger = logging.getLogger(__name__)


class EnterpriseRAGService:
    """
    Provider-independent Enterprise Legal Contract RAG Service.
    Orchestrates embedding, vector similarity retrieval, standardized prompt construction,
    LLM generation via generic LLMProvider, output validation, and database persistence.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        embedding_service: Optional[EmbeddingService] = None,
        vector_client: Optional[VectorClient] = None
    ):
        # Single active LLM Provider injected or resolved via factory
        self.llm_provider = llm_provider or LLMProviderFactory.get_provider()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_client = vector_client or VectorClient()

    async def answer_question(
        self,
        question: str,
        conversation_id: str,
        scoped_contract_ids: Optional[List[str]] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        if not question or not question.strip():
            return {"answer": "Please provide a question.", "sources": []}

        # 1. Generate query embedding
        try:
            query_embedding = self.embedding_service.get_embedding(question)
        except Exception as e:
            logger.error(f"Error embedding question: {e}")
            return {"answer": "Error generating question embedding.", "sources": []}

        # 2. Hybrid Retrieval (Semantic Search + BM25 + RRF Fusion)
        from backend.app.rag.hybrid_retriever import HybridRetriever
        try:
            retriever = HybridRetriever(db=db)
            retrieval_res = retriever.search(
                query=question,
                contract_ids=scoped_contract_ids,
                top_k=settings.TOP_K
            )
            search_results = retrieval_res["results"]
        except Exception as err:
            logger.error(f"Error executing hybrid retrieval: {err}. Falling back to standard vector search.")
            search_results = self.vector_client.search_vectors(
                query_embedding=query_embedding,
                top_k=settings.TOP_K,
                contract_ids=scoped_contract_ids
            )

        # 3. Handle empty retrieval
        if not search_results:
            answer_text = ResponseValidator.DEFAULT_FALLBACK
            sources: List[Dict[str, Any]] = []
            if db and conversation_id:
                chat_repo = ChatRepository(db)
                chat_repo.add_message(conversation_id, "assistant", answer_text)
            return {"answer": answer_text, "sources": sources}

        # 4. Build context string & citation DTOs
        context_str = ContextBuilder.build_context(search_results)
        sources = CitationHandler.build_sources(search_results)

        # 5. Build standardized, provider-independent RAG prompt
        system_prompt = LegalRAGPromptBuilder.build_system_prompt()
        user_prompt = LegalRAGPromptBuilder.build_user_prompt(question, context_str)

        # 6. Dispatch to single active LLM Provider
        start_time = time.time()
        try:
            llm_request = LLMRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.0,
                metadata={
                    "conversation_id": conversation_id,
                    "chunk_count": len(search_results)
                }
            )
            llm_response = await self.llm_provider.generate(llm_request)
            raw_answer = llm_response.content
            duration = time.time() - start_time
            logger.info(
                f"LLM generation finished | Provider: {llm_response.provider} | "
                f"Model: {llm_response.model} | Duration: {duration:.2f}s"
            )

            # 7. Normalize & validate LLM response
            answer_text = ResponseValidator.validate_and_normalize(raw_answer)

        except LLMProviderError as e:
            logger.error(f"LLM Provider Error ({e.provider}): {e.message}")
            answer_text = f"Error generating answer from LLM provider ({e.provider}): {e.message}"
        except Exception as e:
            logger.error(f"Unexpected error in LLM generation: {e}")
            answer_text = f"Error generating answer: {str(e)}"

        # 8. Persist assistant message & RAG sources to database
        if db and conversation_id:
            try:
                chat_repo = ChatRepository(db)
                assistant_msg = chat_repo.add_message(conversation_id, "assistant", answer_text)
                chat_repo.add_rag_sources(assistant_msg.id, sources)
            except Exception as db_err:
                logger.error(f"Failed to persist chat message/sources: {db_err}")

        return {
            "answer": answer_text,
            "sources": sources
        }
