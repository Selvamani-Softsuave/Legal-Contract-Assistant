import json
import uuid
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.domain.entities.conversation_entity import (
    Conversation as DomainConversation,
    Message as DomainMessage
)
from backend.app.domain.ports.repositories.chat_repository_port import IChatRepository
from backend.app.domain.models.conversation import Conversation as ORMConversation
from backend.app.domain.models.message import Message as ORMMessage
from backend.app.domain.models.rag_source import RAGSource as ORMRAGSource
from backend.app.infrastructure.database.mappers.chat_mapper import ChatMapper

logger = logging.getLogger(__name__)


class SQLAlchemyChatRepository(IChatRepository):
    """SQLAlchemy implementation of IChatRepository."""

    def __init__(self, db: Session):
        self.db = db

    def get_conversation(self, conversation_id: str) -> Optional[DomainConversation]:
        conv = self.db.query(ORMConversation).filter(ORMConversation.id == conversation_id).first()
        return ChatMapper.to_domain_conversation(conv) if conv else None

    def list_conversations(self) -> List[DomainConversation]:
        convs = self.db.query(ORMConversation).order_by(ORMConversation.created_at.desc()).all()
        return [ChatMapper.to_domain_conversation(c) for c in convs]

    def save_conversation(self, conversation: DomainConversation) -> DomainConversation:
        existing = self.db.query(ORMConversation).filter(ORMConversation.id == conversation.id).first()
        scoped_json = json.dumps(conversation.scoped_contract_ids) if conversation.scoped_contract_ids else None
        if existing:
            existing.title = conversation.title
            existing.scoped_contract_ids = scoped_json
            existing.updated_at = conversation.updated_at
            orm_obj = existing
        else:
            orm_obj = ORMConversation(
                id=conversation.id,
                title=conversation.title,
                scoped_contract_ids=scoped_json,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at
            )
            self.db.add(orm_obj)

        self.db.commit()
        self.db.refresh(orm_obj)
        return ChatMapper.to_domain_conversation(orm_obj)

    def delete_conversation(self, conversation_id: str) -> bool:
        conv = self.db.query(ORMConversation).filter(ORMConversation.id == conversation_id).first()
        if not conv:
            return False
        self.db.delete(conv)
        self.db.commit()
        return True

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None
    ) -> DomainMessage:
        msg = ORMMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        self.db.add(msg)
        self.db.flush()

        if sources:
            for s in sources:
                src = ORMRAGSource(
                    id=str(uuid.uuid4()),
                    message_id=msg.id,
                    chunk_id=s.get("chunk_id", ""),
                    document_name=s.get("document_name", ""),
                    page_number=s.get("page_number"),
                    section=s.get("section"),
                    clause=s.get("clause"),
                    similarity_score=s.get("similarity_score"),
                    text_content=s.get("text_content")
                )
                self.db.add(src)

        self.db.commit()
        self.db.refresh(msg)
        return ChatMapper.to_domain_message(msg)

    def get_messages(self, conversation_id: str) -> List[DomainMessage]:
        messages = self.db.query(ORMMessage).filter(
            ORMMessage.conversation_id == conversation_id
        ).order_by(ORMMessage.created_at.asc()).all()
        return [ChatMapper.to_domain_message(m) for m in messages]
