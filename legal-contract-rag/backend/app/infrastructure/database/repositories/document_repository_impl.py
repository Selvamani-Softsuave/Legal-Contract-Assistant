import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.domain.entities.document_entity import Document as DomainDocument
from backend.app.domain.ports.repositories.document_repository_port import IDocumentRepository
from backend.app.domain.models.document import Document as ORMDocument
from backend.app.infrastructure.database.mappers.document_mapper import DocumentMapper

logger = logging.getLogger(__name__)


class SQLAlchemyDocumentRepository(IDocumentRepository):
    """SQLAlchemy implementation of IDocumentRepository."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, document_id: str) -> Optional[DomainDocument]:
        orm_doc = self.db.query(ORMDocument).filter(ORMDocument.id == document_id).first()
        return DocumentMapper.to_domain(orm_doc) if orm_doc else None

    def list_by_contract(self, contract_id: str) -> List[DomainDocument]:
        orm_docs = self.db.query(ORMDocument).filter(
            ORMDocument.contract_id == contract_id
        ).order_by(ORMDocument.created_at.desc()).all()
        return [DocumentMapper.to_domain(d) for d in orm_docs]

    def save(self, document: DomainDocument) -> DomainDocument:
        existing = self.db.query(ORMDocument).filter(ORMDocument.id == document.id).first()
        if existing:
            existing.status = document.status.value if hasattr(document.status, "value") else str(document.status)
            existing.error_message = document.error_message
            existing.extracted_text_path = document.extracted_text_path
            existing.updated_at = document.updated_at
            orm_obj = existing
        else:
            orm_obj = DocumentMapper.to_orm(document)
            self.db.add(orm_obj)

        self.db.commit()
        self.db.refresh(orm_obj)
        return DocumentMapper.to_domain(orm_obj)

    def update_status(self, document_id: str, status: str, error_message: Optional[str] = None) -> Optional[DomainDocument]:
        orm_doc = self.db.query(ORMDocument).filter(ORMDocument.id == document_id).first()
        if not orm_doc:
            return None
        orm_doc.status = status
        if error_message is not None:
            orm_doc.error_message = error_message
        self.db.commit()
        self.db.refresh(orm_doc)
        return DocumentMapper.to_domain(orm_doc)

    def delete(self, document_id: str) -> bool:
        orm_doc = self.db.query(ORMDocument).filter(ORMDocument.id == document_id).first()
        if not orm_doc:
            return False
        self.db.delete(orm_doc)
        self.db.commit()
        return True
