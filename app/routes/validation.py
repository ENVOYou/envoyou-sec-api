from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Any

from app.utils.security import require_api_key
from app.services.validation_service import cross_validate_epa

router = APIRouter()

class Scope1Schema(BaseModel):
    fuel_type: str
    amount: float
    unit: str

class Scope2Schema(BaseModel):
    kwh: float
    grid_region: Optional[str] = None

class ValidatePayload(BaseModel):
    company: str
    scope1: Optional[Scope1Schema] = None
    scope2: Optional[Scope2Schema] = None


@router.post("/epa")
async def validate_epa(payload: ValidatePayload, state: Optional[str] = Query(None), year: Optional[int] = Query(None), api_key: Any = Depends(require_api_key)):
    try:
        result = cross_validate_epa(payload.model_dump(), state=state, year=year)
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
