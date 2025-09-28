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


def _assess_calculation_confidence(payload_dict: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """Quick confidence assessment for emissions calculation."""
    score = 85  # Base score for calculation
    
    # Check data completeness
    scope1 = payload_dict.get("scope1")
    scope2 = payload_dict.get("scope2")
    
    if not scope1 and not scope2:
        score -= 50
        level = "low"
        recommendation = "No emission data provided"
    elif scope1 and scope2:
        score += 10  # Bonus for complete data
        level = "high"
        recommendation = "Complete Scope 1 & 2 data - ready for SEC filing"
    else:
        level = "medium"
        recommendation = "Partial data - consider EPA validation"
    
    # Check for reasonable values
    total_co2e = result.get("totals", {}).get("emissions_kg", 0) / 1000  # Convert to tonnes
    if total_co2e > 100000:  # Very large emissions
        score -= 10
        recommendation += " - Verify large emission values"
    elif total_co2e < 1:  # Very small emissions
        score -= 5
        recommendation += " - Verify small emission values"
    
    return {
        "score": max(0, min(100, score)),
        "level": level,
        "recommendation": recommendation
    }


@router.post("/calculate")
async def calculate(payload: CalcPayload, api_key: Any = Depends(require_api_key), db: Session = Depends(get_db)):
    try:
        payload_dict = payload.model_dump()
        result = calculate_emissions(payload_dict)
        
        # Add confidence assessment
        confidence = _assess_calculation_confidence(payload_dict, result)
        result["confidence_analysis"] = confidence
        
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
            "confidence": confidence
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
