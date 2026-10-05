import uuid
import re
from dataclasses import dataclass
from typing import Optional
from backend.app.domain.exceptions.base import ValidationException


@dataclass(frozen=True)
class ContractNumber:
    value: str

    def __post_init__(self):
        cleaned = self.value.strip().upper() if self.value else ""
        if not cleaned:
            raise ValidationException("Contract number cannot be empty.")
        object.__setattr__(self, "value", cleaned)

    @classmethod
    def generate(cls) -> "ContractNumber":
        return cls(f"CNT-{uuid.uuid4().hex[:8].upper()}")

    @classmethod
    def from_string(cls, raw: Optional[str]) -> "ContractNumber":
        if not raw or not raw.strip():
            return cls.generate()
        return cls(raw.strip().upper())

    def __str__(self) -> str:
        return self.value
