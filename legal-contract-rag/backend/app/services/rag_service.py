import re
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

        # 0. Check for greetings, identity, and general application inquiries
        if self.is_conversational_or_general_query(question):
            return await self._handle_general_query(question, conversation_id, db)

        # 1. Generate query embedding
        try:
            query_embedding = self.embedding_service.get_embedding(question)
        except Exception as e:
            logger.error(f"Error embedding question: {e}")
            return {"answer": "Error generating question embedding.", "sources": []}

        # 2. Hybrid Retrieval (Semantic Search + BM25 + RRF Fusion)
        from backend.app.rag.hybrid_retriever import HybridRetriever
        try:
            retriever = HybridRetriever(
                db=db,
                vector_client=self.vector_client,
                embedding_service=self.embedding_service
            )
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

        # 3. Handle empty retrieval (unsupported questions / out of scope)
        if not search_results:
            return await self._handle_unsupported_query(question, conversation_id, db)

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

            # If the model indicates context does not contain sufficient info, generate dynamic unique explanation
            if answer_text == ResponseValidator.DEFAULT_FALLBACK:
                return await self._handle_unsupported_query(question, conversation_id, db, search_results=search_results)

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

    @staticmethod
    def is_conversational_or_general_query(q: str) -> bool:
        """Determines if a query is a greeting, persona/identity, or general application question."""
        cleaned = re.sub(r"[^\w\s]", "", q.lower().strip())
        words = cleaned.split()
        if not words:
            return False

        first_word = words[0]
        # Match repeated letter variants like hi, hii, hiii, hey, heyy, hello, helloo, yo, etc.
        if re.match(r"^(h+i+|h+e+y+|h+e+l+o+|h+o+l+a+|y+o+)\b", first_word) and len(words) <= 5:
            return True

        # Multi-word greetings
        full_greetings = {
            "good morning", "good afternoon", "good evening", "good day",
            "howdy", "welcome", "nice to meet you"
        }
        if cleaned in full_greetings or any(cleaned.startswith(g) for g in ["good morning", "good afternoon", "good evening"]):
            return True

        # Identity & Application inquiry patterns
        general_patterns = [
            r"^(who|what)s? (are you|is your name|your name|do you do|can you do)\b",
            r"^(tell me about|explain) (yourself|this (app|application|platform|system|assistant|service|project))\b",
            r"^(what is|what is the name of) this (app|application|platform|system|assistant|service|project)\b",
            r"^how (can|do) you help\b",
            r"^how (does|do) (this|it) work\b",
            r"^(help|help me|what are your capabilities|features)\b",
            r"^how are you\b",
            r"^(thank you|thanks|thx)\b",
            r"^whats? up\b",
            r"^who made you\b",
        ]
        for pattern in general_patterns:
            if re.search(pattern, cleaned):
                return True

        return False

    async def _handle_general_query(
        self,
        question: str,
        conversation_id: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Handles greetings and general application questions dynamically via LLM without requiring contract retrieval."""
        general_sys_prompt = (
            "You are the Enterprise Legal Contract Assistant, an intelligent, conversational legal AI application.\n"
            "Your role is to help legal, procurement, and contract management teams review, analyze, and query contracts, "
            "agreements (like MSAs, NDAs, Vendor Agreements), amendments, and schedules.\n\n"
            "Key Capabilities:\n"
            "1. Grounded contract Q&A using hybrid retrieval (BM25 + Semantic vector search).\n"
            "2. Amendment hierarchy and precedence resolution (determining operative terms when amendments supersede agreements).\n"
            "3. Defined terms cross-referencing and verification.\n"
            "4. Precise clause and document citations.\n\n"
            "Guidelines:\n"
            "- Tailor your response directly to the user's specific greeting or general question.\n"
            "- Answer warmly, naturally, and concisely (2-4 sentences).\n"
            "- Vary your wording so repeated greetings feel fresh, conversational, and engaging.\n"
            "- State that you are the Legal Contract Assistant and invite the user to upload contracts or ask specific questions.\n"
            "- IMPORTANT: Output ONLY the direct final message to the user. Do not include internal drafts, options, reasoning bullets, or thought process."
        )

        try:
            prompt_text = (
                f"User message: {question}\n\n"
                "Respond directly and warmly to the user as the Enterprise Legal Contract Assistant in 2-3 sentences. "
                "DIRECT ANSWER:"
            )
            llm_request = LLMRequest(
                system_prompt=general_sys_prompt,
                user_prompt=prompt_text,
                temperature=0.7,
                max_tokens=600
            )
            llm_response = await self.llm_provider.generate(llm_request)
            answer_text = ResponseValidator.validate_and_normalize(llm_response.content)
            if answer_text == ResponseValidator.DEFAULT_FALLBACK or not answer_text.endswith(('.', '!', '?')):
                import random
                answer_text = random.choice([
                    "Hello! I am the Enterprise Legal Contract Assistant. I am here to help you query, review, and analyze your legal contracts, amendments, and agreements. How can I assist you today?",
                    "Greetings! As your Enterprise Legal Contract Assistant, I can help you examine agreement clauses, check amendment hierarchies, and verify contractual terms. How can I assist you today?",
                    "Hi there! I am your Enterprise Legal Contract Assistant, designed to assist with reviewing and querying your legal contracts and amendments. Feel free to upload documents or ask specific questions!"
                ])
        except Exception as e:
            logger.warning(f"Error generating general assistant response: {e}. Using standard greeting.")
            answer_text = (
                "Hello! I am the **Enterprise Legal Contract Assistant**. "
                "I am designed to assist you with analyzing and querying legal agreements, "
                "resolving amendment precedence, and finding specific clauses across your contracts. "
                "How can I assist you with your contracts today?"
            )

        if db and conversation_id:
            try:
                chat_repo = ChatRepository(db)
                chat_repo.add_message(conversation_id, "assistant", answer_text)
            except Exception as db_err:
                logger.error(f"Failed to persist chat message: {db_err}")

        return {
            "answer": answer_text,
            "sources": []
        }

    async def _handle_unsupported_query(
        self,
        question: str,
        conversation_id: str,
        db: Optional[Session] = None,
        search_results: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Dynamically generates unique, natural responses for unsupported questions (out-of-scope,
        missing context, or absent from contract documents) using the LLM with temperature=0.7.
        Ensures each response is unique and natural, even when users repeat the same question.
        """
        import random
        unsupported_sys_prompt = (
            "You are the Enterprise Legal Contract Assistant.\n"
            "The user asked a question that is NOT supported or found in the provided legal contracts and documents.\n\n"
            "Guidelines:\n"
            "1. Explain concisely, professionally, and naturally that the requested information is not found in the loaded contract documents or falls outside the scope of the available agreements.\n"
            "2. Invite the user to check their uploaded contracts or ask about specific terms, obligations, payment schedules, or liabilities within their documents.\n"
            "3. Keep the response to 1-3 sentences.\n"
            "4. Vary your wording and tone so repeated inquiries receive fresh, engaging, and unique responses.\n"
            "5. IMPORTANT: Output ONLY the direct final response to the user. Do not include internal drafts, options, reasoning bullets, or thought process."
        )

        fallback_templates = [
            "I was unable to find provisions regarding that topic in the currently loaded contract documents. Please feel free to ask about specific terms, liabilities, or obligations within your agreements.",
            "That information doesn't appear in the available contracts. You can upload relevant documents or ask about existing contractual clauses and policies.",
            "I've searched through the provided documents, but could not locate details addressing this question. Let me know if you would like to explore other terms or agreements in your contract suite.",
            "The active contracts do not contain information related to this inquiry. Please ask about clauses, termination policies, payment terms, or liabilities within your uploaded agreements.",
            "I couldn't locate any provisions related to your question in the active contracts. How else can I assist you with your agreements today?"
        ]

        try:
            prompt_text = (
                f"User Question: {question}\n\n"
                "Respond directly and professionally as the Enterprise Legal Contract Assistant, explaining that this information is not found in the provided contracts. "
                "DIRECT ANSWER:"
            )
            llm_request = LLMRequest(
                system_prompt=unsupported_sys_prompt,
                user_prompt=prompt_text,
                temperature=0.7,
                max_tokens=600
            )
            llm_response = await self.llm_provider.generate(llm_request)
            answer_text = ResponseValidator.validate_and_normalize(llm_response.content)
            if not answer_text or answer_text == ResponseValidator.DEFAULT_FALLBACK or not answer_text.endswith(('.', '!', '?')):
                answer_text = random.choice(fallback_templates)
        except Exception as e:
            logger.warning(f"Error generating dynamic unsupported response: {e}. Using diversified fallback.")
            answer_text = random.choice(fallback_templates)

        if db and conversation_id:
            try:
                chat_repo = ChatRepository(db)
                assistant_msg = chat_repo.add_message(conversation_id, "assistant", answer_text)
                if search_results:
                    sources = CitationHandler.build_sources(search_results)
                    chat_repo.add_rag_sources(assistant_msg.id, sources)
            except Exception as db_err:
                logger.error(f"Failed to persist unsupported chat message: {db_err}")

        return {
            "answer": answer_text,
            "sources": []
        }
