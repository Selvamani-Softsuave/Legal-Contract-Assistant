from backend.app.domain.entities.contract_entity import Contract as DomainContract
from backend.app.domain.enums import ContractStatus
from backend.app.domain.models.contract import Contract as ORMContract


class ContractMapper:
    @staticmethod
    def to_domain(orm_entity: ORMContract) -> DomainContract:
        if not orm_entity:
            return None
        status_val = orm_entity.status
        if isinstance(status_val, str):
            try:
                status_val = ContractStatus(status_val)
            except ValueError:
                status_val = ContractStatus.DRAFT

        return DomainContract(
            id=orm_entity.id,
            name=orm_entity.name,
            contract_number=orm_entity.contract_number,
            contract_type=orm_entity.contract_type,
            status=status_val,
            effective_date=orm_entity.effective_date,
            expiration_date=orm_entity.expiration_date,
            governing_law=orm_entity.governing_law,
            jurisdiction=orm_entity.jurisdiction,
            version=orm_entity.version,
            description=orm_entity.description,
            is_deleted=orm_entity.is_deleted,
            created_at=orm_entity.created_at,
            updated_at=orm_entity.updated_at
        )

    @staticmethod
    def to_orm(domain_entity: DomainContract) -> ORMContract:
        if not domain_entity:
            return None
        return ORMContract(
            id=domain_entity.id,
            name=domain_entity.name,
            contract_number=domain_entity.contract_number,
            contract_type=domain_entity.contract_type,
            status=domain_entity.status.value if hasattr(domain_entity.status, "value") else str(domain_entity.status),
            effective_date=domain_entity.effective_date,
            expiration_date=domain_entity.expiration_date,
            governing_law=domain_entity.governing_law,
            jurisdiction=domain_entity.jurisdiction,
            version=domain_entity.version,
            description=domain_entity.description,
            is_deleted=domain_entity.is_deleted,
            created_at=domain_entity.created_at,
            updated_at=domain_entity.updated_at
        )
