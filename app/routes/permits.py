from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional, List
from app.models.permit import Permit
from app.data.mock_permits import mock_permits

router = APIRouter()

def check_params(
    nama: Optional[str] = Query(None),
    jenis: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    if not any([nama, jenis, status]):
        raise HTTPException(400, "At least one search parameter required")
    return {"nama": nama, "jenis": jenis, "status": status}

@router.get("/search", response_model=List[Permit])
async def search_permits(params: dict = Depends(check_params)):
    nama = params["nama"]
    jenis = params["jenis"]
    status = params["status"]

    results = []
    for permit in mock_permits:
        if nama and nama.lower() not in permit["company_name"].lower():
            continue
        if jenis and jenis.lower() not in permit["permit_type"].lower():
            continue
        if status and status.lower() not in permit["status"].lower():
            continue
        results.append(permit)
    return results
