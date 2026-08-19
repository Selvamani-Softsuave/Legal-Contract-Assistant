from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.domain.models.document import Document

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, document_id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()

    def list_by_contract(self, contract_id: str) -> List[Document]:
        return self.db.query(Document).filter(
            Document.contract_id == contract_id,
            Document.is_deleted == False
        ).order_by(Document.created_at.desc()).all()

    def create(self, document_data: dict) -> Document:
        doc = Document(**document_data)
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def update_status(self, document_id: str, status: str) -> Optional[Document]:
        doc = self.get_by_id(document_id)
        if not doc:
            return None
        doc.status = status
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def soft_delete(self, document_id: str) -> bool:
        doc = self.get_by_id(document_id)
        if not doc:
            return False
        doc.is_deleted = True
        self.db.commit()
        return True
