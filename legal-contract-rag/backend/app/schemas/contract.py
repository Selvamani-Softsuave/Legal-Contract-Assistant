from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ContractCreate(BaseModel):
    name: str
    contract_number: Optional[str] = None
    contract_type: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    description: Optional[str] = None

class ContractUpdate(BaseModel):
    name: Optional[str] = None
    contract_number: Optional[str] = None
    contract_type: Optional[str] = None
    status: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    description: Optional[str] = None

class ContractResponse(BaseModel):
    id: str
    name: str
    contract_number: Optional[str] = None
    contract_type: Optional[str] = None
    status: str
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    version: int
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
