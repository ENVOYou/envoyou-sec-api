from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session

from app.utils.security import require_api_key
from app.models.database import get_db, create_tables
from app.services.emissions_calculator import calculate_emissions, FACTORS_VERSION
from app.services.audit_service import record_audit

router = APIRouter()

class Scope1Schema(BaseModel):
    fuel_type: str
    amount: float
    unit: str

class Scope2Schema(BaseModel):
    kwh: float
    grid_region: Optional[str] = None

class CalcPayload(BaseModel):
    company: str
    scope1: Optional[Scope1Schema] = None
    scope2: Optional[Scope2Schema] = None

    @field_validator('company')
    @classmethod
    def company_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('company is required')
        return v


@router.post("/calculate")
async def calculate(payload: CalcPayload, api_key: Any = Depends(require_api_key), db: Session = Depends(get_db)):
    try:
        result = calculate_emissions(payload.model_dump())
        # Ensure schema exists before audit write (CI-safe)
        try:
            create_tables()
        except Exception:
            pass
        # Record minimal audit trail with inputs and factors version
        notes: Dict[str, Any] = {
            "action": "emissions_calculate",
            "version": FACTORS_VERSION,
            "components": result.get("components", {}),
            "totals": result.get("totals", {}),
        }
        record_audit(
            db,
            source_file="emissions_calculator",
            calculation_version=FACTORS_VERSION,
            company_cik=payload.company,
            notes=str(notes),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
