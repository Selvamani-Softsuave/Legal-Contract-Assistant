import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from backend.app.domain.enums import DocumentStatus


@dataclass
class Document:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    contract_id: str = ""
    file_name: str = ""
    file_size: int = 0
    file_type: str = ""
    blob_path: str = ""
    status: DocumentStatus = DocumentStatus.QUEUED
    error_message: Optional[str] = None
    extracted_text_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_processing(self) -> None:
        self.status = DocumentStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_completed(self) -> None:
        self.status = DocumentStatus.COMPLETED
        self.error_message = None
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        self.status = DocumentStatus.FAILED
        self.error_message = error
        self.updated_at = datetime.utcnow()
