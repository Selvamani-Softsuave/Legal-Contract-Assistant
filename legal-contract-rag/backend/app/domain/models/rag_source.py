import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class RAGSource(Base):
    __tablename__ = "RAGSources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("Messages.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(36), ForeignKey("DocumentChunks.id", ondelete="SET NULL"), nullable=True)
    document_name = Column(String(255), nullable=False)
    page_number = Column(Integer, nullable=True)
    section = Column(String(100), nullable=True)
    clause = Column(String(100), nullable=True)
    relevance_score = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    message = relationship("Message", back_populates="rag_sources")
