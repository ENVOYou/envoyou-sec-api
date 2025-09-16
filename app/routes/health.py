from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
import sys
from datetime import datetime, timezone
from app.utils import cache as cache_util
from app.utils.redis_utils import redis_health_check
from app.services.redis_metrics import redis_metrics

router = APIRouter()

@router.get("", tags=["Health"], summary="Health Check Endpoint")
async def health_check():
    """
    Comprehensive health check for AWS App Runner and monitoring.
    Returns detailed system status information.
    """
    cache_timestamp = cache_util.get_cache_timestamp()
    redis_status = redis_health_check()
    
    health_status = {
        "status": "success",
        "data": {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "environment": os.getenv("FASTAPI_ENV", "development"),
            "python_version": sys.version.split()[0],
            "system": {
                "cache_status": "active" if cache_timestamp else "empty",
                "last_cache_update": datetime.fromtimestamp(float(cache_timestamp)).isoformat() if cache_timestamp else None,
                "redis": redis_status
            },
            "services": {
                "api_server": "running",
                "security": "enabled" if os.getenv("API_KEYS") else "disabled",
                "rate_limiting": "redis" if redis_status.get("available") else "memory",
                "session_storage": "redis" if redis_status.get("available") else "database"
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

@router.get("/test-sentry", tags=["Health"], summary="Test Sentry Error Monitoring")
async def test_sentry():
    """
    Test endpoint to verify Sentry error monitoring is working.
    This will intentionally throw an error to test Sentry integration.
    """
    try:
        # Intentionally cause an error for testing
        result = 1 / 0  # This will raise ZeroDivisionError
        return {"message": f"Result: {result}"}
    except Exception as e:
        # Log the error (Sentry will automatically capture this)
        print(f"Test error occurred: {e}")
        raise e

@router.post("/test-email", tags=["Health"], summary="Test Email Service")
async def test_email(email: str):
    """
    Test endpoint to verify email service is working.
    Send a test email to the specified address.
    """
    from app.utils.email import email_service
    
    try:
        result = email_service.send_verification_email(
            to_email=email,
            verification_token="test-verification-token-123"
        )
        
        if result:
            return {"status": "success", "message": f"Test email sent to {email}"}
        else:
            return {"status": "failed", "message": "Email sending failed"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}  # Re-raise to let Sentry capture it

@router.get("/redis", tags=["Health"], summary="Redis Metrics and Health")
async def redis_metrics_check():
    """
    Comprehensive Redis metrics and health check.
    Returns detailed Redis performance and status information.
    """
    try:
        # Collect current metrics
        metrics = await redis_metrics.collect_metrics()

        # Get health status
        health = await redis_metrics.get_health_status()

        # Get recent alerts
        alerts = await redis_metrics.get_alerts(hours=1)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "health": health,
                    "metrics": metrics,
                    "alerts": alerts,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Redis metrics check failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
