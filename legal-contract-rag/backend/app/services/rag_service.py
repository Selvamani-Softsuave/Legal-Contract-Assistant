import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.infrastructure.vector.vector_client import VectorClient
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.ollama_service import OllamaService
from backend.app.repositories.chat_repository import ChatRepository
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

def _clean_llm_response(text: str) -> str:
    if not text:
        return text
    cleaned = text.strip()
    
    # 1. If model outputs thought checklist and ends with "Answer: ..."
    if "Answer:" in cleaned:
        parts = cleaned.split("Answer:")
        candidate = parts[-1].strip()
        if candidate:
            cleaned = candidate

    # 2. Filter out internal thinking bullets if still present
    lines = [l for l in cleaned.split("\n")]
    filtered = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("* Role:", "* Task:", "* Constraint", "* Document:", "* Content:", "* Question:", "* Section", "* Total", "* Direct answer", "* Professional", "* No internal", "* Citations", "* Only using", "*Self-Correction")):
            continue
        filtered.append(line)
    
    result = "\n".join(filtered).strip()
    return result if result else cleaned

class EnterpriseRAGService:
    def __init__(self):
        self.vector_client = VectorClient()
        self.embedding_service = EmbeddingService()
        self.ollama_service = OllamaService()

    async def answer_question(
        self,
        question: str,
        conversation_id: str,
        scoped_contract_ids: Optional[List[str]] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        if not question.strip():
            return {"answer": "Please provide a question.", "sources": []}

        # 1. Generate query embedding
        try:
            query_embedding = self.embedding_service.get_embedding(question)
        except Exception as e:
            logger.error(f"Error embedding question: {e}")
            return {"answer": "Error generating question embedding.", "sources": []}

        # 2. Decoupled similarity search via Document Processor internal Vector API
        search_results = self.vector_client.search_vectors(
            query_embedding=query_embedding,
            top_k=settings.TOP_K,
            contract_ids=scoped_contract_ids
        )

        if not search_results:
            answer_text = "I don't know based on the provided documents."
            sources = []
            if db and conversation_id:
                chat_repo = ChatRepository(db)
                msg = chat_repo.add_message(conversation_id, "assistant", answer_text)
            return {"answer": answer_text, "sources": sources}

        # 3. Build context & citation DTOs
        context_parts = []
        sources = []
        for res in search_results:
            meta = res.get("metadata", {})
            doc_text = res.get("document", "")
            context_parts.append(f"[Document: {meta.get('document_name', 'Unknown')}, Page {meta.get('page', 1)}]\n{doc_text}")

            sources.append({
                "chunk_id": res.get("id"),
                "document_name": meta.get("document_name", "Unknown"),
                "page_number": meta.get("page"),
                "section": meta.get("section") or meta.get("article"),
                "clause": meta.get("clause"),
                "relevance_score": float(res.get("distance", 0.0))
            })

        context_str = "\n\n---\n\n".join(context_parts)

        # 4. Construct clean legal RAG prompt
        system_prompt = (
            "You are a professional legal contract assistant. "
            "Answer the question directly and concisely based strictly on the provided contract context. "
            "Cite relevant sections, clauses, or page numbers where applicable. "
            "If the context does not contain the answer, say 'I don't know based on the provided documents.' "
            "Do not output internal thinking, notes, or bullet-point rule evaluations."
        )

        user_prompt = f"Contract Context:\n{context_str}\n\nQuestion: {question}\n\nDirect Answer:"

        # 5. Generate LLM response
        try:
            raw_answer = await self.ollama_service.generate(system_prompt, user_prompt)
            answer_text = _clean_llm_response(raw_answer)
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            answer_text = f"Error generating answer: {str(e)}"

        # 6. Persist to relational database (Messages & RAGSources)
        if db and conversation_id:
            chat_repo = ChatRepository(db)
            assistant_msg = chat_repo.add_message(conversation_id, "assistant", answer_text)
            chat_repo.add_rag_sources(assistant_msg.id, sources)

        return {
            "answer": answer_text,
            "sources": sources
        }
