import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from backend.app.domain.enums import MessageRole


@dataclass
class RAGSource:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = ""
    chunk_id: str = ""
    document_name: str = ""
    page_number: Optional[int] = None
    section: Optional[str] = None
    clause: Optional[str] = None
    similarity_score: Optional[float] = None
    text_content: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Message:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ""
    role: MessageRole = MessageRole.USER
    content: str = ""
    sources: List[RAGSource] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Conversation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Conversation"
    scoped_contract_ids: Optional[List[str]] = None
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, role: MessageRole, content: str, sources: Optional[List[RAGSource]] = None) -> Message:
        msg = Message(
            conversation_id=self.id,
            role=role,
            content=content,
            sources=sources or []
        )
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()
        return msg
