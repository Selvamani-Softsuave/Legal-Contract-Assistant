from typing import List, Optional
from backend.app.domain.entities.contract_entity import Contract
from backend.app.domain.value_objects.contract_number import ContractNumber
from backend.app.domain.ports.repositories.contract_repository_port import IContractRepository
from backend.app.domain.exceptions.contract_exceptions import (
    ContractNotFoundException,
    DuplicateContractNumberException
)
from backend.app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse


class ContractUseCases:
    """Application services orchestrating Contract business workflows."""

    def __init__(self, repository: IContractRepository):
        self.repository = repository

    def create_contract(self, dto: ContractCreate) -> Contract:
        contract_num = ContractNumber.from_string(dto.contract_number).value
        # Check uniqueness prior to persistence
        existing = self.repository.get_by_number(contract_num)
        if existing:
            raise DuplicateContractNumberException(contract_num)

        contract = Contract(
            name=dto.name,
            contract_number=contract_num,
            contract_type=dto.contract_type,
            effective_date=dto.effective_date,
            expiration_date=dto.expiration_date,
            governing_law=dto.governing_law,
            jurisdiction=dto.jurisdiction,
            description=dto.description
        )
        return self.repository.save(contract)

    def get_contract(self, contract_id: str) -> Contract:
        contract = self.repository.get_by_id(contract_id)
        if not contract:
            raise ContractNotFoundException(contract_id)
        return contract

    def list_contracts(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Contract]:
        return self.repository.list(skip=skip, limit=limit, status=status)

    def update_contract(self, contract_id: str, dto: ContractUpdate) -> Contract:
        contract = self.get_contract(contract_id)
        update_data = dto.dict(exclude_unset=True) if hasattr(dto, "dict") else dict(dto)

        if "name" in update_data and update_data["name"]:
            contract.name = update_data["name"]
        if "contract_number" in update_data and update_data["contract_number"]:
            new_num = ContractNumber.from_string(update_data["contract_number"]).value
            if new_num != contract.contract_number:
                existing = self.repository.get_by_number(new_num)
                if existing and existing.id != contract_id:
                    raise DuplicateContractNumberException(new_num)
                contract.contract_number = new_num
        if "contract_type" in update_data:
            contract.contract_type = update_data["contract_type"]
        if "effective_date" in update_data:
            contract.effective_date = update_data["effective_date"]
        if "expiration_date" in update_data:
            contract.expiration_date = update_data["expiration_date"]
        if "governing_law" in update_data:
            contract.governing_law = update_data["governing_law"]
        if "jurisdiction" in update_data:
            contract.jurisdiction = update_data["jurisdiction"]
        if "description" in update_data:
            contract.description = update_data["description"]

        return self.repository.save(contract)

    def delete_contract(self, contract_id: str) -> bool:
        contract = self.get_contract(contract_id)
        return self.repository.delete(contract.id)
