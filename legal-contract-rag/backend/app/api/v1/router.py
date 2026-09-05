from fastapi import APIRouter
from backend.app.api.v1 import contracts, documents, processing, chat, ws, agent

api_router = APIRouter()
api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(processing.router, prefix="/processing", tags=["processing"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])

