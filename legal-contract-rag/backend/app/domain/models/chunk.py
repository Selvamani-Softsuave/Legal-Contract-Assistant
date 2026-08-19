import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class DocumentChunk(Base):
    __tablename__ = "DocumentChunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("Documents.id", ondelete="CASCADE"), nullable=False, index=True)
    contract_id = Column(String(36), ForeignKey("Contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    article = Column(String(100), nullable=True)
    section = Column(String(100), nullable=True)
    subsection = Column(String(100), nullable=True)
    clause = Column(String(100), nullable=True)
    heading = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")
    contract = relationship("Contract", back_populates="chunks")
