from pydantic import BaseModel
from datetime import date
from typing import Optional

class Permit(BaseModel):
    id: int
    company_name: str
    permit_type: str
    status: str
    issued_date: date
    expired_date: Optional[date]  # None jika tidak ada tanggal expired
