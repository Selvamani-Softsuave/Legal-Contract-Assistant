from backend.app.domain.entities.document_entity import Document as DomainDocument
from backend.app.domain.enums import DocumentStatus
from backend.app.domain.models.document import Document as ORMDocument


class DocumentMapper:
    @staticmethod
    def to_domain(orm_entity: ORMDocument) -> DomainDocument:
        if not orm_entity:
            return None
        status_val = orm_entity.status
        if isinstance(status_val, str):
            try:
                status_val = DocumentStatus(status_val)
            except ValueError:
                status_val = DocumentStatus.QUEUED

        return DomainDocument(
            id=orm_entity.id,
            contract_id=orm_entity.contract_id,
            file_name=orm_entity.file_name,
            file_size=orm_entity.file_size,
            file_type=orm_entity.file_type,
            blob_path=orm_entity.blob_path,
            status=status_val,
            error_message=orm_entity.error_message,
            extracted_text_path=orm_entity.extracted_text_path,
            created_at=orm_entity.created_at,
            updated_at=orm_entity.updated_at
        )

    @staticmethod
    def to_orm(domain_entity: DomainDocument) -> ORMDocument:
        if not domain_entity:
            return None
        return ORMDocument(
            id=domain_entity.id,
            contract_id=domain_entity.contract_id,
            file_name=domain_entity.file_name,
            file_size=domain_entity.file_size,
            file_type=domain_entity.file_type,
            blob_path=domain_entity.blob_path,
            status=domain_entity.status.value if hasattr(domain_entity.status, "value") else str(domain_entity.status),
            error_message=domain_entity.error_message,
            extracted_text_path=domain_entity.extracted_text_path,
            created_at=domain_entity.created_at,
            updated_at=domain_entity.updated_at
        )
