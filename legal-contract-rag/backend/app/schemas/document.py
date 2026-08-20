from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    documentId: str
    contractId: str
    fileName: str
    fileSize: int
    status: str
    jobId: str
    correlationId: str
    message: str

class DocumentResponse(BaseModel):
    id: str
    contract_id: str
    contract_name: Optional[str] = None
    file_name: str
    file_size: int
    file_type: str
    blob_path: str
    page_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
