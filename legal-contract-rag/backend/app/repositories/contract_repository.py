import uuid
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from backend.app.domain.models.contract import Contract
from backend.app.schemas.contract import ContractCreate, ContractUpdate
from backend.app.domain.exceptions.contract_exceptions import DuplicateContractNumberException

logger = logging.getLogger(__name__)


def _generate_contract_number() -> str:
    return f"CNT-{uuid.uuid4().hex[:8].upper()}"


class ContractRepository:
    """
    Relational Contract Repository.
    Maintains clean domain exception boundary without coupling to FastAPI or HTTP status codes.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, contract_id: str) -> Optional[Contract]:
        return self.db.query(Contract).filter(Contract.id == contract_id, Contract.is_deleted == False).first()

    def get_by_number(self, contract_number: str) -> Optional[Contract]:
        return self.db.query(Contract).filter(Contract.contract_number == contract_number, Contract.is_deleted == False).first()

    def list(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Contract]:
        query = self.db.query(Contract).filter(Contract.is_deleted == False)
        if status:
            query = query.filter(Contract.status == status)
        return query.order_by(Contract.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, obj_in: ContractCreate) -> Contract:
        data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, "dict") else dict(obj_in)
        num = data.get("contract_number")
        if not num or not str(num).strip():
            data["contract_number"] = _generate_contract_number()
        else:
            data["contract_number"] = str(num).strip()

        contract = Contract(**data)
        self.db.add(contract)
        try:
            self.db.commit()
            self.db.refresh(contract)
            return contract
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"IntegrityError creating contract: {e}")
            raise DuplicateContractNumberException(data.get("contract_number") or "")

    def update(self, contract_id: str, obj_in: ContractUpdate) -> Optional[Contract]:
        contract = self.get_by_id(contract_id)
        if not contract:
            return None
        update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, "dict") else dict(obj_in)
        if "contract_number" in update_data:
            num = update_data["contract_number"]
            if not num or not str(num).strip():
                update_data["contract_number"] = _generate_contract_number()
            else:
                update_data["contract_number"] = str(num).strip()

        for field, value in update_data.items():
            setattr(contract, field, value)
        try:
            self.db.commit()
            self.db.refresh(contract)
            return contract
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"IntegrityError updating contract {contract_id}: {e}")
            raise DuplicateContractNumberException(update_data.get("contract_number") or "")

    def soft_delete(self, contract_id: str) -> bool:
        contract = self.get_by_id(contract_id)
        if not contract:
            return False
        contract.is_deleted = True
        self.db.commit()
        return True
