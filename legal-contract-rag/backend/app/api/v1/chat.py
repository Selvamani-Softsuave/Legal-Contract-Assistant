from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from backend.app.core.database import get_db
from backend.app.repositories.chat_repository import ChatRepository
from backend.app.services.rag_service import EnterpriseRAGService
from backend.app.schemas.chat import (
    ConversationCreate, ConversationResponse,
    ChatRequest, ChatResponse, MessageResponse, SourceDTO
)

router = APIRouter()
rag_service = EnterpriseRAGService()

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(obj_in: ConversationCreate, db: Session = Depends(get_db)):
    repo = ChatRepository(db)
    conv = repo.create_conversation(title=obj_in.title, scoped_contract_ids=obj_in.scoped_contract_ids)
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        scoped_contract_ids=json.loads(conv.scoped_contract_ids) if conv.scoped_contract_ids else None,
        created_at=conv.created_at,
        updated_at=conv.updated_at
    )

@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    repo = ChatRepository(db)
    convs = repo.list_conversations()
    results = []
    for c in convs:
        results.append(ConversationResponse(
            id=c.id,
            title=c.title,
            scoped_contract_ids=json.loads(c.scoped_contract_ids) if c.scoped_contract_ids else None,
            created_at=c.created_at,
            updated_at=c.updated_at
        ))
    return results

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(conversation_id: str, db: Session = Depends(get_db)):
    repo = ChatRepository(db)
    conv = repo.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = repo.get_messages(conversation_id)
    results = []
    for m in messages:
        sources_dto = [
            SourceDTO(
                chunk_id=s.chunk_id,
                document_name=s.document_name,
                page_number=s.page_number,
                section=s.section,
                clause=s.clause,
                relevance_score=s.relevance_score
            )
            for s in (m.rag_sources or [])
        ]
        results.append(MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            sources=sources_dto,
            created_at=m.created_at
        ))
    return results

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    repo = ChatRepository(db)
    success = repo.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted successfully"}

@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(conversation_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    repo = ChatRepository(db)
    conv = repo.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 1. Add user message
    user_msg = repo.add_message(conversation_id, "user", request.question)

    # 2. Determine scoping
    scoped_ids = request.scoped_contract_ids
    if not scoped_ids and conv.scoped_contract_ids:
        scoped_ids = json.loads(conv.scoped_contract_ids)

    # 3. Answer question via RAG service
    rag_result = await rag_service.answer_question(
        question=request.question,
        conversation_id=conversation_id,
        scoped_contract_ids=scoped_ids,
        db=db
    )

    sources_dto = [SourceDTO(**s) for s in rag_result["sources"]]

    # Fetch newly persisted assistant message
    messages = repo.get_messages(conversation_id)
    latest_msg = messages[-1] if messages else user_msg

    return ChatResponse(
        conversation_id=conversation_id,
        message=MessageResponse(
            id=latest_msg.id,
            conversation_id=conversation_id,
            role="assistant",
            content=rag_result["answer"],
            sources=sources_dto,
            created_at=latest_msg.created_at
        ),
        answer=rag_result["answer"],
        sources=sources_dto
    )

@router.post("/", response_model=ChatResponse)
async def chat_legacy(request: ChatRequest, db: Session = Depends(get_db)):
    repo = ChatRepository(db)
    conv = repo.create_conversation("Quick Chat", scoped_contract_ids=request.scoped_contract_ids)
    repo.add_message(conv.id, "user", request.question)

    rag_result = await rag_service.answer_question(
        question=request.question,
        conversation_id=conv.id,
        scoped_contract_ids=request.scoped_contract_ids,
        db=db
    )

    sources_dto = [SourceDTO(**s) for s in rag_result["sources"]]
    messages = repo.get_messages(conv.id)
    latest_msg = messages[-1] if messages else conv

    return ChatResponse(
        conversation_id=conv.id,
        message=MessageResponse(
            id=getattr(latest_msg, "id", conv.id),
            conversation_id=conv.id,
            role="assistant",
            content=rag_result["answer"],
            sources=sources_dto,
            created_at=conv.created_at
        ),
        answer=rag_result["answer"],
        sources=sources_dto
    )
