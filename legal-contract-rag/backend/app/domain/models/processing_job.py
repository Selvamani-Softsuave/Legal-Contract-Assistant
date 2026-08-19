import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class ProcessingJob(Base):
    __tablename__ = "ProcessingJobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("Documents.id", ondelete="CASCADE"), nullable=False, index=True)
    operation = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="Queued")
    correlation_id = Column(String(36), nullable=False)
    requested_by = Column(String(100), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    document = relationship("Document", back_populates="jobs")
