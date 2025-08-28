from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.permit import Permit
from app.models.permit_search import PermitSearchParams
from app.data.mock_permits import mock_permits

router = APIRouter()

@router.get("")
async def get_all_permits():
    """Endpoint untuk mendapatkan semua permits dengan response format standar"""
    return {"status": "success", "data": mock_permits}

@router.get("/active")
async def get_active_permits():
    active = [p for p in mock_permits if p["status"].lower() == "aktif"]
    return {"status": "success", "data": active}

@router.get("/stats")
async def get_permits_stats():
    total = len(mock_permits)
    active_count = len([p for p in mock_permits if p["status"].lower() == "aktif"])
    inactive_count = total - active_count
    stats = {
        "total_permits": total,
        "active_permits": active_count,
        "inactive_permits": inactive_count
    }
    return {"status": "success", "data": stats}

@router.get("/search")
async def search_permits(params: PermitSearchParams = Depends()):
    if not (params.nama or params.jenis or params.status):
        raise HTTPException(status_code=400, detail="At least one search parameter required (nama, jenis, or status)")
    results = []
    for permit in mock_permits:
        if params.nama and params.nama.lower() not in permit["company_name"].lower():
            continue
        if params.jenis and params.jenis.lower() not in permit["permit_type"].lower():
            continue
        if params.status and params.status.lower() != permit["status"].lower():
            continue
        results.append(permit)
    return {"status": "success", "data": results}

@router.get("/company/{company_name}")
async def get_permits_by_company(company_name: str):
    results = [p for p in mock_permits if company_name.lower() in p["company_name"].lower()]
    if not results:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"status": "success", "data": results}

@router.get("/type/{permit_type}")
async def get_permits_by_type(permit_type: str):
    results = [p for p in mock_permits if permit_type.lower() in p["permit_type"].lower()]
    if not results:
        raise HTTPException(status_code=404, detail="Permit type not found")
    return {"status": "success", "data": results}

@router.get("/{permit_id}")
async def get_permit_by_id(permit_id: int):
    for permit in mock_permits:
        if permit["id"] == permit_id:
            return {"status": "success", "data": permit}
    raise HTTPException(status_code=404, detail="Permit not found")

