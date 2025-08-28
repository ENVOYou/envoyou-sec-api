from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.permit import Permit
from app.models.permit_search import PermitSearchParams
from app.clients.amdalnet_client import AmdalnetClient

router = APIRouter()

@router.get("")
async def get_all_permits():
    """Endpoint to get all permits from the external Amdalnet source."""
    client = AmdalnetClient()
    permits = client.get_sk_final()
    return {"status": "success", "data": permits}

@router.get("/active")
async def get_active_permits():
    client = AmdalnetClient()
    all_permits = client.get_sk_final()
    active = [p for p in all_permits if p.get("status", "").lower() == "aktif"]
    return {"status": "success", "data": active}

@router.get("/stats")
async def get_permits_stats():
    client = AmdalnetClient()
    all_permits = client.get_sk_final()
    total = len(all_permits)
    active_count = len([p for p in all_permits if p.get("status", "").lower() == "aktif"])
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
    
    client = AmdalnetClient()
    all_permits = client.get_sk_final()
    results = []
    for permit in all_permits:
        company_name = permit.get("company_name", "").lower()
        permit_type = permit.get("permit_type", "").lower()
        permit_status = permit.get("status", "").lower()

        if params.nama and params.nama.lower() not in company_name:
            continue
        if params.jenis and params.jenis.lower() not in permit_type:
            continue
        if params.status and params.status.lower() != permit_status:
            continue
        results.append(permit)
    return {"status": "success", "data": results}

@router.get("/company/{company_name}")
async def get_permits_by_company(company_name: str):
    client = AmdalnetClient()
    all_permits = client.get_sk_final()
    results = [p for p in all_permits if company_name.lower() in p.get("company_name", "").lower()]
    if not results:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"status": "success", "data": results}

@router.get("/type/{permit_type}")
async def get_permits_by_type(permit_type: str):
    client = AmdalnetClient()
    all_permits = client.get_sk_final()
    results = [p for p in all_permits if permit_type.lower() in p.get("permit_type", "").lower()]
    if not results:
        raise HTTPException(status_code=404, detail="Permit type not found")
    return {"status": "success", "data": results}

@router.get("/{permit_id}")
async def get_permit_by_id(permit_id: int):
    client = AmdalnetClient()
    all_permits = client.get_sk_final()
    for permit in all_permits:
        if permit.get("id") == permit_id:
            return {"status": "success", "data": permit}
    raise HTTPException(status_code=404, detail="Permit not found")

