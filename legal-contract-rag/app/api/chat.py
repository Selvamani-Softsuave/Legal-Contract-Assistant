
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import RAGService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize RAG service (singleton)
rag_service = RAGService()

@router.post('/', response_model=ChatResponse)
async def chat(request: ChatRequest):
    '''
    Answer a question based on the uploaded documents.
    '''
    try:
        result = await rag_service.answer_question(request.question)
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f'Error in chat endpoint: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')

