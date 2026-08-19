import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Contract(Base):
    __tablename__ = "Contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    contract_number = Column(String(100), unique=True, nullable=True, index=True)
    contract_type = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="Draft")
    effective_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    governing_law = Column(String(150), nullable=True)
    jurisdiction = Column(String(150), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="contract", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="contract", cascade="all, delete-orphan")
