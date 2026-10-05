import json
from typing import List
from backend.app.domain.entities.conversation_entity import (
    Conversation as DomainConversation,
    Message as DomainMessage,
    RAGSource as DomainRAGSource
)
from backend.app.domain.enums import MessageRole
from backend.app.domain.models.conversation import Conversation as ORMConversation
from backend.app.domain.models.message import Message as ORMMessage
from backend.app.domain.models.rag_source import RAGSource as ORMRAGSource


class ChatMapper:
    @staticmethod
    def to_domain_conversation(orm_conv: ORMConversation) -> DomainConversation:
        if not orm_conv:
            return None
        scoped_ids = None
        if orm_conv.scoped_contract_ids:
            try:
                scoped_ids = json.loads(orm_conv.scoped_contract_ids)
            except Exception:
                scoped_ids = []

        return DomainConversation(
            id=orm_conv.id,
            title=orm_conv.title or "New Conversation",
            scoped_contract_ids=scoped_ids,
            created_at=orm_conv.created_at,
            updated_at=orm_conv.updated_at
        )

    @staticmethod
    def to_domain_message(orm_msg: ORMMessage) -> DomainMessage:
        if not orm_msg:
            return None
        role_val = orm_msg.role
        try:
            role_val = MessageRole(role_val)
        except ValueError:
            role_val = MessageRole.USER

        sources = []
        if hasattr(orm_msg, "sources") and orm_msg.sources:
            for s in orm_msg.sources:
                sources.append(DomainRAGSource(
                    id=s.id,
                    message_id=s.message_id,
                    chunk_id=s.chunk_id,
                    document_name=s.document_name,
                    page_number=s.page_number,
                    section=s.section,
                    clause=s.clause,
                    similarity_score=s.similarity_score,
                    text_content=s.text_content,
                    created_at=s.created_at
                ))

        return DomainMessage(
            id=orm_msg.id,
            conversation_id=orm_msg.conversation_id,
            role=role_val,
            content=orm_msg.content,
            sources=sources,
            created_at=orm_msg.created_at
        )
