import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.domain.entities.contract_entity import Contract as DomainContract
from backend.app.domain.ports.repositories.contract_repository_port import IContractRepository
from backend.app.domain.models.contract import Contract as ORMContract
from backend.app.domain.exceptions.contract_exceptions import (
    ContractNotFoundException,
    DuplicateContractNumberException
)
from backend.app.infrastructure.database.mappers.contract_mapper import ContractMapper

logger = logging.getLogger(__name__)


class SQLAlchemyContractRepository(IContractRepository):
    """
    SQLAlchemy implementation of IContractRepository.
    Raises domain exceptions on constraint violations. Does NOT depend on FastAPI or HTTP.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, contract_id: str) -> Optional[DomainContract]:
        orm_contract = self.db.query(ORMContract).filter(
            ORMContract.id == contract_id,
            ORMContract.is_deleted == False
        ).first()
        return ContractMapper.to_domain(orm_contract) if orm_contract else None

    def get_by_number(self, contract_number: str) -> Optional[DomainContract]:
        orm_contract = self.db.query(ORMContract).filter(
            ORMContract.contract_number == contract_number,
            ORMContract.is_deleted == False
        ).first()
        return ContractMapper.to_domain(orm_contract) if orm_contract else None

    def list(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[DomainContract]:
        query = self.db.query(ORMContract).filter(ORMContract.is_deleted == False)
        if status:
            query = query.filter(ORMContract.status == status)
        orm_contracts = query.order_by(ORMContract.created_at.desc()).offset(skip).limit(limit).all()
        return [ContractMapper.to_domain(c) for c in orm_contracts]

    def save(self, contract: DomainContract) -> DomainContract:
        existing = self.db.query(ORMContract).filter(ORMContract.id == contract.id).first()
        if existing:
            # Update fields
            existing.name = contract.name
            existing.contract_number = contract.contract_number
            existing.contract_type = contract.contract_type
            existing.status = contract.status.value if hasattr(contract.status, "value") else str(contract.status)
            existing.effective_date = contract.effective_date
            existing.expiration_date = contract.expiration_date
            existing.governing_law = contract.governing_law
            existing.jurisdiction = contract.jurisdiction
            existing.version = contract.version
            existing.description = contract.description
            existing.is_deleted = contract.is_deleted
            existing.updated_at = contract.updated_at
            orm_obj = existing
        else:
            orm_obj = ContractMapper.to_orm(contract)
            self.db.add(orm_obj)

        try:
            self.db.commit()
            self.db.refresh(orm_obj)
            return ContractMapper.to_domain(orm_obj)
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"IntegrityError saving contract {contract.contract_number}: {e}")
            raise DuplicateContractNumberException(contract.contract_number or "")

    def delete(self, contract_id: str) -> bool:
        contract = self.db.query(ORMContract).filter(
            ORMContract.id == contract_id,
            ORMContract.is_deleted == False
        ).first()
        if not contract:
            return False
        contract.is_deleted = True
        self.db.commit()
        return True
