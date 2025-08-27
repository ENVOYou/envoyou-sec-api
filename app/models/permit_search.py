from pydantic import BaseModel
from typing import Optional

class PermitSearchParams(BaseModel):
    nama: Optional[str] = None
    jenis: Optional[str] = None
    status: Optional[str] = None

    def is_empty(self):
        return not (self.nama or self.jenis or self.status)