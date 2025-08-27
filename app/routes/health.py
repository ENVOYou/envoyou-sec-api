from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
import sys
from datetime import datetime

router = APIRouter()

@router.get("/health", tags=["Health"], summary="Health Check Endpoint")
async def health_check():
    """
    Comprehensive health check for AWS App Runner and monitoring.
    Returns detailed system status information.
    """
    cache_timestamp = os.getenv("CACHE_TIMESTAMP")
    
    health_status = {
        "status": "success",
        "data": {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "environment": os.getenv("FASTAPI_ENV", "development"),
            "python_version": sys.version.split()[0],
            "system": {
                "cache_status": "active" if cache_timestamp else "empty",
                "last_cache_update": datetime.fromtimestamp(float(cache_timestamp)).isoformat() if cache_timestamp else None,
            },
            "services": {
                "api_server": "running",
                "security": "enabled" if os.getenv("API_KEYS") else "disabled",
                "rate_limiting": "active"
            }
        }
    }
    
    if os.getenv("FASTAPI_ENV") != "production":
        health_status["data"]["debug"] = {
            "port": os.getenv("PORT", "8000"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "demo_keys_available": bool(os.getenv("API_KEYS", "").find("demo_key") >= 0)
        }
    
    return JSONResponse(
        status_code=200,
        content=health_status
    )

@router.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Kubernetes/container readiness check.
    Simple endpoint that returns 200 when service is ready to accept traffic.
    """
    return JSONResponse({"status": "ready"})

@router.get("/live", tags=["Health"])
async def liveness_check():
    """
    Kubernetes/container liveness check.
    Simple endpoint that returns 200 when service is alive.
    """
    return JSONResponse({"status": "alive"})
