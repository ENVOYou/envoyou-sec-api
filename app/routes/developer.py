from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone, timedelta
from typing import Optional

from .dependencies import get_current_user
from ..models.user import User
from ..models.database import get_db
from sqlalchemy.orm import Session
from ..models.api_key import APIKey
from ..services.redis_metrics import redis_metrics
from ..utils.security import get_rate_limit_for_key, require_api_key

router = APIRouter()

@router.get("/stats", summary="Developer usage stats")
async def developer_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        api_keys = db.query(APIKey).filter(
            APIKey.user_id == current_user.id,
            APIKey.is_active == True
        ).all()

        total_calls = sum(k.usage_count for k in api_keys)
        active_keys = len(api_keys)

        return JSONResponse({
            "status": "success",
            "data": {
                "total_calls": total_calls,
                "active_keys": active_keys,
                "api_keys": [k.to_dict() for k in api_keys],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch developer stats: {str(e)}")


@router.get("/usage-analytics", summary="Aggregated usage analytics")
async def usage_analytics(hours: int = 24, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if hours < 1 or hours > 720:
            hours = 24
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Placeholder: using APIKey.last_used as proxy for activity in window
        keys = db.query(APIKey).filter(APIKey.user_id == current_user.id, APIKey.is_active == True).all()
        activity = []
        for k in keys:
            if k.last_used and k.last_used.replace(tzinfo=timezone.utc) >= since:
                activity.append({
                    "key_id": str(k.id),
                    "prefix": k.prefix,
                    "last_used": k.last_used.isoformat(),
                    "usage_count": k.usage_count
                })

        return JSONResponse({
            "status": "success",
            "data": {
                "window_hours": hours,
                "activity": activity,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch usage analytics: {str(e)}")


@router.get("/rate-limits", summary="Current rate limit info", dependencies=[Depends(require_api_key)])
async def rate_limits(request):
    try:
        limit_str = get_rate_limit_for_key(request)
        health = await redis_metrics.get_health_status()
        return JSONResponse({
            "status": "success",
            "data": {
                "rate_limit": limit_str,
                "backend": "redis" if health.get("available") else "memory",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch rate limits: {str(e)}")
