from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.domain.models.contract import Contract
from backend.app.schemas.contract import ContractCreate, ContractUpdate

class ContractRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, contract_id: str) -> Optional[Contract]:
        return self.db.query(Contract).filter(Contract.id == contract_id, Contract.is_deleted == False).first()

    def list(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Contract]:
        query = self.db.query(Contract).filter(Contract.is_deleted == False)
        if status:
            query = query.filter(Contract.status == status)
        return query.order_by(Contract.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, obj_in: ContractCreate) -> Contract:
        contract = Contract(**obj_in.dict(exclude_unset=True))
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def update(self, contract_id: str, obj_in: ContractUpdate) -> Optional[Contract]:
        contract = self.get_by_id(contract_id)
        if not contract:
            return None
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def soft_delete(self, contract_id: str) -> bool:
        contract = self.get_by_id(contract_id)
        if not contract:
            return False
        contract.is_deleted = True
        self.db.commit()
        return True
