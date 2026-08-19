from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.repositories.contract_repository import ContractRepository
from backend.app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse

router = APIRouter()

@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(obj_in: ContractCreate, db: Session = Depends(get_db)):
    repo = ContractRepository(db)
    return repo.create(obj_in)

@router.get("", response_model=List[ContractResponse])
def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    repo = ContractRepository(db)
    return repo.list(skip=skip, limit=limit, status=status)

@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    repo = ContractRepository(db)
    contract = repo.get_by_id(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract

@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(contract_id: str, obj_in: ContractUpdate, db: Session = Depends(get_db)):
    repo = ContractRepository(db)
    contract = repo.update(contract_id, obj_in)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract

@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(contract_id: str, db: Session = Depends(get_db)):
    repo = ContractRepository(db)
    success = repo.soft_delete(contract_id)
    if not success:
        raise HTTPException(status_code=404, detail="Contract not found")
    return None
