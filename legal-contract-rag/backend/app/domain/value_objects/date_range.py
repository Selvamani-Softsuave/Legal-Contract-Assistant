from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from backend.app.domain.exceptions.contract_exceptions import InvalidContractDateRangeException


@dataclass(frozen=True)
class DateRange:
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None

    def __post_init__(self):
        if self.effective_date and self.expiration_date:
            if self.expiration_date < self.effective_date:
                raise InvalidContractDateRangeException(self.effective_date, self.expiration_date)

    @property
    def is_active_now(self) -> bool:
        now = datetime.utcnow()
        if self.effective_date and now < self.effective_date:
            return False
        if self.expiration_date and now > self.expiration_date:
            return False
        return True
