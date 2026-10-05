from typing import List, Optional, Dict, Any
from backend.app.domain.entities.conversation_entity import Conversation, Message
from backend.app.domain.ports.repositories.chat_repository_port import IChatRepository
from backend.app.domain.exceptions.chat_exceptions import (
    ConversationNotFoundException,
    EmptyQuestionException
)


class ChatUseCases:
    """Application use cases for conversations and grounded chat."""

    def __init__(self, repository: IChatRepository, rag_service=None):
        self.repository = repository
        self.rag_service = rag_service

    def create_conversation(self, title: str = "New Conversation", scoped_contract_ids: Optional[List[str]] = None) -> Conversation:
        conv = Conversation(
            title=title,
            scoped_contract_ids=scoped_contract_ids
        )
        return self.repository.save_conversation(conv)

    def list_conversations(self) -> List[Conversation]:
        return self.repository.list_conversations()

    def get_conversation(self, conversation_id: str) -> Conversation:
        conv = self.repository.get_conversation(conversation_id)
        if not conv:
            raise ConversationNotFoundException(conversation_id)
        return conv

    def get_messages(self, conversation_id: str) -> List[Message]:
        self.get_conversation(conversation_id)
        return self.repository.get_messages(conversation_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        self.get_conversation(conversation_id)
        return self.repository.delete_conversation(conversation_id)

    async def answer_question(
        self,
        conversation_id: str,
        question: str,
        scoped_contract_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if not question or not question.strip():
            raise EmptyQuestionException()

        conv = self.get_conversation(conversation_id)

        # 1. Persist user message
        self.repository.add_message(conversation_id, "user", question)

        # 2. Determine contract scoping
        active_scope = scoped_contract_ids or conv.scoped_contract_ids

        # 3. Generate grounded answer via RAG service
        if not self.rag_service:
            from backend.app.services.rag_service import EnterpriseRAGService
            self.rag_service = EnterpriseRAGService()

        rag_result = await self.rag_service.answer_question(
            question=question,
            conversation_id=conversation_id,
            scoped_contract_ids=active_scope
        )

        return {
            "conversation_id": conversation_id,
            "answer": rag_result.get("answer", ""),
            "sources": rag_result.get("sources", []),
            "scope": active_scope
        }
