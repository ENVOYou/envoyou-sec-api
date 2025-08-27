"""
Admin routes for API key management and system monitoring (FastAPI version).
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from typing import Any, Dict

from api.utils.security import (
    require_api_key, 
    generate_api_key, 
    list_api_keys,
    validate_api_key,
    VALID_API_KEYS
)

router = APIRouter(prefix="/admin")
logger = logging.getLogger(__name__)

@router.get("/api-keys", dependencies=[Depends(require_api_key)])
async def list_keys(request: Request):
    """List all registered API keys (admin only)."""
    client_info = request.state.client_info
    if client_info.get("tier") != "premium":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    keys = list_api_keys()
    return JSONResponse(content={
        "status": "success",
        "data": {
            "api_keys": keys,
            "total_count": len(keys)
        },
        "timestamp": datetime.now().isoformat()
    })

@router.post("/api-keys", dependencies=[Depends(require_api_key)])
async def create_key(request: Request, data: Dict[str, Any]):
    """Create a new API key."""
    client_info = request.state.client_info
    if client_info.get("tier") != "premium":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    client_name = data.get("client_name")
    tier = data.get("tier", "basic")
    
    if not client_name:
        raise HTTPException(status_code=400, detail="client_name is required")
    if tier not in ["basic", "premium"]:
        raise HTTPException(status_code=400, detail="tier must be 'basic' or 'premium'")
    try:
        new_key = generate_api_key(client_name, tier)
        return JSONResponse(content={
            "status": "success",
            "data": {
                "api_key": new_key,
                "client_name": client_name,
                "tier": tier,
                "created": datetime.now().isoformat(),
                "requests_per_minute": 30 if tier == "basic" else 100
            },
            "message": "API key created successfully"
        })
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")

@router.delete("/api-keys/{key_prefix}", dependencies=[Depends(require_api_key)])
async def delete_key(request: Request, key_prefix: str):
    """Delete an API key (by key prefix)."""
    client_info = request.state.client_info
    if client_info.get("tier") != "premium":
        raise HTTPException(status_code=403, detail="Admin privileges required")

    key_to_delete = next((key for key in VALID_API_KEYS if key.startswith(key_prefix)), None)
    if not key_to_delete:
        raise HTTPException(status_code=404, detail="API key not found")

    if key_to_delete == request.state.api_key:
        raise HTTPException(status_code=400, detail="Cannot delete the key currently being used")
    deleted_info = VALID_API_KEYS.pop(key_to_delete)
    
    return JSONResponse(content={
        "status": "success",
        "message": f"API key for '{deleted_info['name']}' deleted successfully"
    })

@router.get("/stats", dependencies=[Depends(require_api_key)])
async def api_stats(request: Request):
    """Get API usage statistics."""
    client_info = request.state.client_info
    if client_info.get("tier") != "premium":
        raise HTTPException(status_code=403, detail="Admin privileges required")

    return JSONResponse(content={
        "status": "success",
        "data": {
            "total_api_keys": len(VALID_API_KEYS),
            "tiers": {
                "basic": len([k for k, v in VALID_API_KEYS.items() if v.get("tier") == "basic"]),
                "premium": len([k for k, v in VALID_API_KEYS.items() if v.get("tier") == "premium"])
            },
            "system_info": {
                "version": "1.0.0",
                "environment": "development"
            }
        },
        "timestamp": datetime.now().isoformat()
    })

__all__ = ["router"]

