from pydantic import BaseModel
from typing import List, Optional

class DocumentInfo(BaseModel):
    id: str
    name: str
    chunks: int

class UploadResponse(BaseModel):
    documentId: str
    fileName: str
    pages: int
    chunksCreated: int
    status: str

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]