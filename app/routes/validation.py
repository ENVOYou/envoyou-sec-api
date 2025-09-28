from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Any
from sqlalchemy.orm import Session

from app.utils.security import require_api_key
from app.services.validation_service import cross_validate_epa
from app.models.database import get_db

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
async def validate_epa(payload: ValidatePayload, state: Optional[str] = Query(None), year: Optional[int] = Query(None), db: Session = Depends(get_db), api_key: Any = Depends(require_api_key)):
    try:
        result = cross_validate_epa(payload.model_dump(), db=db, state=state, year=year)
        
        # Extract confidence for top-level response
        confidence = result.get("confidence_analysis", {})
        
        return {
            "status": "success",
            "validation": {
                "confidence_score": confidence.get("score", 0),
                "confidence_level": confidence.get("level", "unknown"),
                "recommendation": confidence.get("recommendation", "Manual review required"),
                "matches_found": result.get("epa", {}).get("matches_count", 0),
                "flags_count": len(result.get("flags", []))
            },
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
