from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    scoped_contract_ids: Optional[List[str]] = None

class ConversationResponse(BaseModel):
    id: str
    title: str
    scoped_contract_ids: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SourceDTO(BaseModel):
    chunk_id: Optional[str] = None
    document_name: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    clause: Optional[str] = None
    relevance_score: Optional[float] = None

class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    scoped_contract_ids: Optional[List[str]] = None

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: List[SourceDTO] = []
    created_at: datetime

class ChatResponse(BaseModel):
    conversation_id: str
    message: MessageResponse
    answer: str
    sources: List[SourceDTO]
