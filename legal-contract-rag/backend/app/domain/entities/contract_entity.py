import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from backend.app.domain.enums import ContractStatus
from backend.app.domain.value_objects.contract_number import ContractNumber
from backend.app.domain.value_objects.date_range import DateRange
from backend.app.domain.exceptions.contract_exceptions import InvalidContractStatusTransitionException


@dataclass
class Contract:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    contract_number: Optional[str] = None
    contract_type: Optional[str] = None
    status: ContractStatus = ContractStatus.DRAFT
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    version: int = 1
    description: Optional[str] = None
    is_deleted: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.contract_number:
            self.contract_number = str(ContractNumber.generate())
        # Validate date range invariants if dates are provided
        if self.effective_date and self.expiration_date:
            DateRange(self.effective_date, self.expiration_date)

    def activate(self) -> None:
        if self.status == ContractStatus.TERMINATED:
            raise InvalidContractStatusTransitionException(self.status.value, ContractStatus.ACTIVE.value)
        self.status = ContractStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def terminate(self) -> None:
        self.status = ContractStatus.TERMINATED
        self.updated_at = datetime.utcnow()

    def expire(self) -> None:
        self.status = ContractStatus.EXPIRED
        self.updated_at = datetime.utcnow()

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
