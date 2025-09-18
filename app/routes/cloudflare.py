"""
Cloudflare API Routes
Provides endpoints for Cloudflare management and monitoring
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime

from ..utils.security import require_api_key
from ..services.cloudflare_service import cloudflare_service

router = APIRouter(tags=["cloudflare"])

@router.get("/health", summary="Cloudflare API Health Check")
async def cloudflare_health():
    """
    Check Cloudflare API connectivity and account status
    """
    try:
        health = await cloudflare_service.get_health_check()
        return JSONResponse(content=health)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/analytics", summary="Zone Analytics", dependencies=[Depends(require_api_key)])
async def get_analytics(domain: str = "envoyou.com", hours: int = 24):
    """
    Get Cloudflare zone analytics data
    """
    try:
        since_seconds = -hours * 3600  # Convert hours to seconds ago
        analytics = await cloudflare_service.get_zone_analytics(domain, since_seconds)

        if "error" in analytics:
            raise HTTPException(status_code=400, detail=analytics["error"])

        return JSONResponse(content=analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics request failed: {str(e)}")

@router.get("/dns", summary="DNS Records", dependencies=[Depends(require_api_key)])
async def get_dns_records(domain: str = "envoyou.com"):
    """
    Get all DNS records for the zone
    """
    try:
        records = await cloudflare_service.get_dns_records(domain)
        return JSONResponse(content={
            "domain": domain,
            "records": records,
            "count": len(records),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DNS records request failed: {str(e)}")

@router.post("/dns", summary="Create DNS Record", dependencies=[Depends(require_api_key)])
async def create_dns_record(
    domain: str = "envoyou.com",
    record_type: str = "A",
    name: str = "",
    content: str = "",
    ttl: int = 1,
    proxied: bool = True
):
    """
    Create a new DNS record
    """
    try:
        if not name or not content:
            raise HTTPException(status_code=400, detail="Name and content are required")

        result = await cloudflare_service.create_dns_record(
            domain, record_type, name, content, ttl, proxied
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse(content={
            "success": True,
            "record": result,
            "message": f"DNS record created: {name}"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DNS record creation failed: {str(e)}")

@router.put("/dns/{record_id}", summary="Update DNS Record", dependencies=[Depends(require_api_key)])
async def update_dns_record(
    record_id: str,
    domain: str = "envoyou.com",
    record_type: str = "A",
    name: str = "",
    content: str = "",
    ttl: int = 1,
    proxied: bool = True
):
    """
    Update an existing DNS record
    """
    try:
        if not name or not content:
            raise HTTPException(status_code=400, detail="Name and content are required")

        result = await cloudflare_service.update_dns_record(
            domain, record_id, record_type, name, content, ttl, proxied
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse(content={
            "success": True,
            "record": result,
            "message": f"DNS record updated: {name}"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DNS record update failed: {str(e)}")

@router.delete("/dns/{record_id}", summary="Delete DNS Record", dependencies=[Depends(require_api_key)])
async def delete_dns_record(record_id: str, domain: str = "envoyou.com"):
    """
    Delete a DNS record
    """
    try:
        success = await cloudflare_service.delete_dns_record(domain, record_id)

        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"DNS record deleted: {record_id}"
            })
        else:
            raise HTTPException(status_code=400, detail="Failed to delete DNS record")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DNS record deletion failed: {str(e)}")

@router.get("/firewall", summary="Firewall Rules", dependencies=[Depends(require_api_key)])
async def get_firewall_rules(domain: str = "envoyou.com"):
    """
    Get firewall rules for the zone
    """
    try:
        rules = await cloudflare_service.get_firewall_rules(domain)
        return JSONResponse(content={
            "domain": domain,
            "rules": rules,
            "count": len(rules),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firewall rules request failed: {str(e)}")

@router.post("/firewall", summary="Create Firewall Rule", dependencies=[Depends(require_api_key)])
async def create_firewall_rule(
    description: str,
    expression: str,
    action: str = "block",
    domain: str = "envoyou.com"
):
    """
    Create a new firewall rule
    """
    try:
        result = await cloudflare_service.create_firewall_rule(
            domain, description, expression, action
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse(content={
            "success": True,
            "rule": result,
            "message": f"Firewall rule created: {description}"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firewall rule creation failed: {str(e)}")

@router.get("/rate-limits", summary="Rate Limiting Rules", dependencies=[Depends(require_api_key)])
async def get_rate_limits(domain: str = "envoyou.com"):
    """
    Get rate limiting rules for the zone
    """
    try:
        limits = await cloudflare_service.get_rate_limits(domain)
        return JSONResponse(content={
            "domain": domain,
            "rate_limits": limits,
            "count": len(limits),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rate limits request failed: {str(e)}")

@router.post("/rate-limits", summary="Create Rate Limit", dependencies=[Depends(require_api_key)])
async def create_rate_limit(
    url_pattern: str,
    requests_per_period: int = 100,
    period: int = 60,
    action: str = "block",
    domain: str = "envoyou.com"
):
    """
    Create a new rate limiting rule
    """
    try:
        result = await cloudflare_service.create_rate_limit(
            domain, url_pattern, requests_per_period, period, action
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse(content={
            "success": True,
            "rate_limit": result,
            "message": f"Rate limit created for: {url_pattern}"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rate limit creation failed: {str(e)}")

@router.post("/cache/purge", summary="Purge Cache", dependencies=[Depends(require_api_key)])
async def purge_cache(
    urls: Optional[List[str]] = None,
    domain: str = "envoyou.com"
):
    """
    Purge Cloudflare cache
    """
    try:
        result = await cloudflare_service.purge_cache(domain, urls)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse(content={
            "success": True,
            "message": result["message"],
            "purged_urls": urls if urls else "all"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache purge failed: {str(e)}")

@router.get("/ssl", summary="SSL/TLS Status", dependencies=[Depends(require_api_key)])
async def get_ssl_status(domain: str = "envoyou.com"):
    """
    Get SSL/TLS status for the zone
    """
    try:
        ssl_status = await cloudflare_service.get_ssl_status(domain)

        if "error" in ssl_status:
            raise HTTPException(status_code=400, detail=ssl_status["error"])

        return JSONResponse(content=ssl_status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SSL status request failed: {str(e)}")

@router.get("/page-rules", summary="Page Rules", dependencies=[Depends(require_api_key)])
async def get_page_rules(domain: str = "envoyou.com"):
    """
    Get page rules for the zone
    """
    try:
        rules = await cloudflare_service.get_page_rules(domain)
        return JSONResponse(content={
            "domain": domain,
            "page_rules": rules,
            "count": len(rules),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Page rules request failed: {str(e)}")

@router.post("/page-rules", summary="Create Page Rule", dependencies=[Depends(require_api_key)])
async def create_page_rule(
    url_pattern: str,
    actions: List[dict],
    priority: int = 1,
    domain: str = "envoyou.com"
):
    """
    Create a new page rule
    """
    try:
        result = await cloudflare_service.create_page_rule(
            domain, url_pattern, actions, priority
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return JSONResponse(content={
            "success": True,
            "page_rule": result,
            "message": f"Page rule created for: {url_pattern}"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Page rule creation failed: {str(e)}")