from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional

from backend.app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse
from backend.app.application.contracts.contract_use_cases import ContractUseCases
from backend.app.presentation.dependencies import get_contract_use_cases

router = APIRouter()


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    obj_in: ContractCreate,
    use_cases: ContractUseCases = Depends(get_contract_use_cases)
):
    return use_cases.create_contract(obj_in)


@router.get("", response_model=List[ContractResponse])
def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    use_cases: ContractUseCases = Depends(get_contract_use_cases)
):
    return use_cases.list_contracts(skip=skip, limit=limit, status=status)


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: str,
    use_cases: ContractUseCases = Depends(get_contract_use_cases)
):
    return use_cases.get_contract(contract_id)


@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: str,
    obj_in: ContractUpdate,
    use_cases: ContractUseCases = Depends(get_contract_use_cases)
):
    return use_cases.update_contract(contract_id, obj_in)


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: str,
    use_cases: ContractUseCases = Depends(get_contract_use_cases)
):
    use_cases.delete_contract(contract_id)
    return None
