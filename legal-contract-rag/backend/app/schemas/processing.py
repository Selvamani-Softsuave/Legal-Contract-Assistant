from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProcessingJobResponse(BaseModel):
    id: str
    document_id: str
    operation: str
    status: str
    correlation_id: str
    requested_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime

    class Config:
        from_attributes = True
