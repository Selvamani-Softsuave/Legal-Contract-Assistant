import json
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.domain.models.conversation import Conversation
from backend.app.domain.models.message import Message
from backend.app.domain.models.rag_source import RAGSource

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_conversation(self, title: str, scoped_contract_ids: Optional[List[str]] = None) -> Conversation:
        scoped_json = json.dumps(scoped_contract_ids) if scoped_contract_ids else None
        conv = Conversation(title=title, scoped_contract_ids=scoped_json)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False
        ).first()

    def list_conversations(self) -> List[Conversation]:
        return self.db.query(Conversation).filter(
            Conversation.is_deleted == False,
            Conversation.messages.any()
        ).order_by(Conversation.created_at.desc()).all()

    def delete_conversation(self, conversation_id: str) -> bool:
        conv = self.get_conversation(conversation_id)
        if not conv:
            return False
        conv.is_deleted = True
        self.db.commit()
        return True

    def get_messages(self, conversation_id: str) -> List[Message]:
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()

    def add_message(self, conversation_id: str, role: str, content: str) -> Message:
        msg = Message(conversation_id=conversation_id, role=role, content=content)
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def add_rag_sources(self, message_id: str, sources: List[dict]):
        for s in sources:
            src = RAGSource(
                message_id=message_id,
                chunk_id=s.get("chunk_id"),
                document_name=s.get("document_name", "Unknown"),
                page_number=s.get("page_number"),
                section=s.get("section"),
                clause=s.get("clause"),
                relevance_score=s.get("relevance_score")
            )
            self.db.add(src)
        self.db.commit()
