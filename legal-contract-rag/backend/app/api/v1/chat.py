from fastapi import APIRouter, Depends, status
from typing import List, Optional

from backend.app.schemas.chat import (
    ConversationCreate, ConversationResponse,
    ChatRequest, ChatResponse, MessageResponse, SourceDTO
)
from backend.app.application.chat.chat_use_cases import ChatUseCases
from backend.app.presentation.dependencies import get_chat_use_cases

router = APIRouter()


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    obj_in: ConversationCreate,
    use_cases: ChatUseCases = Depends(get_chat_use_cases)
):
    conv = use_cases.create_conversation(title=obj_in.title, scoped_contract_ids=obj_in.scoped_contract_ids)
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        scoped_contract_ids=conv.scoped_contract_ids,
        created_at=conv.created_at,
        updated_at=conv.updated_at
    )


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    use_cases: ChatUseCases = Depends(get_chat_use_cases)
):
    convs = use_cases.list_conversations()
    return [
        ConversationResponse(
            id=c.id,
            title=c.title,
            scoped_contract_ids=c.scoped_contract_ids,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in convs
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(
    conversation_id: str,
    use_cases: ChatUseCases = Depends(get_chat_use_cases)
):
    messages = use_cases.get_messages(conversation_id)
    results = []
    for m in messages:
        sources_dto = [
            SourceDTO(
                chunk_id=s.chunk_id,
                document_name=s.document_name,
                page_number=s.page_number,
                section=s.section,
                clause=s.clause,
                similarity_score=s.similarity_score,
                text_content=s.text_content
            )
            for s in m.sources
        ]
        results.append(MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role.value if hasattr(m.role, "value") else str(m.role),
            content=m.content,
            sources=sources_dto,
            created_at=m.created_at
        ))
    return results


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation(
    conversation_id: str,
    use_cases: ChatUseCases = Depends(get_chat_use_cases)
):
    use_cases.delete_conversation(conversation_id)
    return {"message": "Conversation deleted successfully"}


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: str,
    request: ChatRequest,
    use_cases: ChatUseCases = Depends(get_chat_use_cases)
):
    result = await use_cases.answer_question(
        conversation_id=conversation_id,
        question=request.question,
        scoped_contract_ids=request.scoped_contract_ids
    )

    sources_dto = [SourceDTO(**s) for s in result["sources"]]

    # Fetch newly created assistant message
    messages = use_cases.get_messages(conversation_id)
    latest_msg = messages[-1] if messages else None

    return ChatResponse(
        conversation_id=conversation_id,
        message=MessageResponse(
            id=latest_msg.id if latest_msg else "",
            conversation_id=conversation_id,
            role="assistant",
            content=result["answer"],
            sources=sources_dto,
            created_at=latest_msg.created_at if latest_msg else None
        ),
        answer=result["answer"],
        sources=sources_dto
    )


@router.post("/", response_model=ChatResponse)
async def chat_legacy(
    request: ChatRequest,
    use_cases: ChatUseCases = Depends(get_chat_use_cases)
):
    conv = use_cases.create_conversation("Quick Chat", scoped_contract_ids=request.scoped_contract_ids)
    return await send_message(conversation_id=conv.id, request=request, use_cases=use_cases)
