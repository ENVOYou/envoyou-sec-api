"""
Cloudflare Integration Service
Provides comprehensive Cloudflare API integration for DNS, security, and analytics
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from ..config import settings

logger = logging.getLogger(__name__)

class CloudflareService:
    """Cloudflare API service for domain management and analytics"""

    def __init__(self):
        self.api_token = settings.CLOUDFLARE_API_TOKEN
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.session = None
        # Prefer explicit zone configuration when available
        self.zone_id = settings.CLOUDFLARE_ZONE_ID or None  # Will be discovered if not set

        # Common headers for all requests
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=30.0
            )
        return self.session

    async def _get_zone_id(self, domain: str = "envoyou.com") -> Optional[str]:
        """Get zone ID for a domain. If `CLOUDFLARE_ZONE_ID` is configured, reuse it."""
        if self.zone_id:
            return self.zone_id

        try:
            session = await self._get_session()
            response = await session.get("/zones", params={"name": domain})

            if response.status_code == 200:
                data = response.json()
                if data["success"] and data["result"]:
                    self.zone_id = data["result"][0]["id"]
                    return self.zone_id

            logger.error(f"Failed to get zone ID for {domain}: {response.text}")
            return None

        except Exception as e:
            logger.error(f"Error getting zone ID: {str(e)}")
            return None

    async def get_zone_analytics(self, domain: str = "envoyou.com", since: int = -86400) -> Dict[str, Any]:
        """
        Get zone analytics data
        since: seconds ago (default: -86400 = 24 hours ago)
        """
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return {"error": "Zone not found"}

        try:
            session = await self._get_session()

            # Get analytics data
            params = {
                "since": since,
                "until": 0,
                "continuous": True
            }

            response = await session.get(f"/zones/{zone_id}/analytics/dashboard", params=params)

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    return {
                        "zone": domain,
                        "analytics": data["result"],
                        "timestamp": datetime.now().isoformat()
                    }

            return {"error": f"Failed to get analytics: {response.status_code}"}

        except Exception as e:
            logger.error(f"Error getting zone analytics: {str(e)}")
            return {"error": str(e)}

    async def get_dns_records(self, domain: str = "envoyou.com") -> List[Dict[str, Any]]:
        """Get all DNS records for a zone"""
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return []

        try:
            session = await self._get_session()
            response = await session.get(f"/zones/{zone_id}/dns_records")

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    return data["result"]

            logger.error(f"Failed to get DNS records: {response.text}")
            return []

        except Exception as e:
            logger.error(f"Error getting DNS records: {str(e)}")
            return []

    async def create_dns_record(self, domain: str, record_type: str, name: str,
                               content: str, ttl: int = 1, proxied: bool = True) -> Dict[str, Any]:
        """Create a new DNS record"""
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return {"error": "Zone not found"}

        try:
            session = await self._get_session()

            record_data = {
                "type": record_type,
                "name": name,
                "content": content,
                "ttl": ttl,
                "proxied": proxied
            }

            response = await session.post(
                f"/zones/{zone_id}/dns_records",
                json=record_data
            )

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    logger.info(f"Created DNS record: {name} -> {content}")
                    return data["result"]

            logger.error(f"Failed to create DNS record: {response.text}")
            return {"error": f"Failed to create record: {response.status_code}"}

        except Exception as e:
            logger.error(f"Error creating DNS record: {str(e)}")
            return {"error": str(e)}

    async def update_dns_record(self, domain: str, record_id: str,
                               record_type: str, name: str, content: str,
                               ttl: int = 1, proxied: bool = True) -> Dict[str, Any]:
        """Update an existing DNS record"""
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return {"error": "Zone not found"}

        try:
            session = await self._get_session()

            record_data = {
                "type": record_type,
                "name": name,
                "content": content,
                "ttl": ttl,
                "proxied": proxied
            }

            response = await session.put(
                f"/zones/{zone_id}/dns_records/{record_id}",
                json=record_data
            )

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    logger.info(f"Updated DNS record: {name} -> {content}")
                    return data["result"]

            logger.error(f"Failed to update DNS record: {response.text}")
            return {"error": f"Failed to update record: {response.status_code}"}

        except Exception as e:
            logger.error(f"Error updating DNS record: {str(e)}")
            return {"error": str(e)}

    async def delete_dns_record(self, domain: str, record_id: str) -> bool:
        """Delete a DNS record"""
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return False

        try:
            session = await self._get_session()
            response = await session.delete(f"/zones/{zone_id}/dns_records/{record_id}")

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    logger.info(f"Deleted DNS record: {record_id}")
                    return True

            logger.error(f"Failed to delete DNS record: {response.text}")
            return False

        except Exception as e:
            logger.error(f"Error deleting DNS record: {str(e)}")
            return False

    async def get_firewall_rules(self, domain: str = "envoyou.com") -> List[Dict[str, Any]]:
        """Get firewall rules for a zone"""
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return []

        try:
            session = await self._get_session()
            response = await session.get(f"/zones/{zone_id}/firewall/rules")

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    return data["result"]

            logger.error(f"Failed to get firewall rules: {response.text}")
            return []

        except Exception as e:
            logger.error(f"Error getting firewall rules: {str(e)}")
            return []

    async def create_firewall_rule(self, domain: str, description: str,
                                  expression: str, action: str = "block") -> Dict[str, Any]:
        """Create a firewall rule"""
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return {"error": "Zone not found"}

        try:
            session = await self._get_session()

            rule_data = {
                "description": description,
                "expression": expression,
                "action": action,
                "enabled": True
            }

            response = await session.post(
                f"/zones/{zone_id}/firewall/rules",
                json=rule_data
            )

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    logger.info(f"Created firewall rule: {description}")
                    return data["result"][0]

            logger.error(f"Failed to create firewall rule: {response.text}")
            return {"error": f"Failed to create rule: {response.status_code}"}

        except Exception as e:
            logger.error(f"Error creating firewall rule: {str(e)}")
            return {"error": str(e)}

    async def get_rate_limits(self, domain: str = "envoyou.com") -> List[Dict[str, Any]]:
        """Get rate limiting rules"""
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return []

        try:
            session = await self._get_session()
            response = await session.get(f"/zones/{zone_id}/rate_limits")

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    return data["result"]

            logger.error(f"Failed to get rate limits: {response.text}")
            return []

        except Exception as e:
            logger.error(f"Error getting rate limits: {str(e)}")
            return []

    async def create_rate_limit(self, domain: str, url_pattern: str,
                               requests_per_period: int = 100,
                               period: int = 60, action: str = "block") -> Dict[str, Any]:
        """Create a rate limiting rule"""
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return {"error": "Zone not found"}

        try:
            session = await self._get_session()

            rate_limit_data = {
                "match": {
                    "request": {
                        "url": url_pattern
                    }
                },
                "threshold": requests_per_period,
                "period": period,
                "action": {
                    "mode": action,
                    "timeout": 60
                },
                "enabled": True
            }

            response = await session.post(
                f"/zones/{zone_id}/rate_limits",
                json=rate_limit_data
            )

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    logger.info(f"Created rate limit for: {url_pattern}")
                    return data["result"]

            logger.error(f"Failed to create rate limit: {response.text}")
            return {"error": f"Failed to create rate limit: {response.status_code}"}

        except Exception as e:
            logger.error(f"Error creating rate limit: {str(e)}")
            return {"error": str(e)}

    async def purge_cache(self, domain: str, urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """Purge Cloudflare cache"""
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return {"error": "Zone not found"}

        try:
            session = await self._get_session()

            if urls:
                # Purge specific URLs
                purge_data = {"files": urls}
            else:
                # Purge everything
                purge_data = {"purge_everything": True}

            response = await session.post(
                f"/zones/{zone_id}/purge_cache",
                json=purge_data
            )

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    logger.info(f"Cache purged for zone: {domain}")
                    return {"success": True, "message": "Cache purged successfully"}

            logger.error(f"Failed to purge cache: {response.text}")
            return {"error": f"Failed to purge cache: {response.status_code}"}

        except Exception as e:
            logger.error(f"Error purging cache: {str(e)}")
            return {"error": str(e)}

    async def get_ssl_status(self, domain: str = "envoyou.com") -> Dict[str, Any]:
        """Get SSL/TLS status for the zone"""
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return {"error": "Zone not found"}

        try:
            session = await self._get_session()
            response = await session.get(f"/zones/{zone_id}/ssl/certificate_packs")

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    return {
                        "zone": domain,
                        "ssl_status": data["result"],
                        "timestamp": datetime.now().isoformat()
                    }

            logger.error(f"Failed to get SSL status: {response.text}")
            return {"error": f"Failed to get SSL status: {response.status_code}"}

        except Exception as e:
            logger.error(f"Error getting SSL status: {str(e)}")
            return {"error": str(e)}

    async def get_page_rules(self, domain: str = "envoyou.com") -> List[Dict[str, Any]]:
        """Get page rules for the zone"""
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return []

        try:
            session = await self._get_session()
            response = await session.get(f"/zones/{zone_id}/pagerules")

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    return data["result"]

            logger.error(f"Failed to get page rules: {response.text}")
            return []

        except Exception as e:
            logger.error(f"Error getting page rules: {str(e)}")
            return []

    async def create_page_rule(self, domain: str, url_pattern: str,
                              actions: List[Dict[str, Any]], priority: int = 1) -> Dict[str, Any]:
        """Create a page rule"""
        zone_id = await self._get_zone_id(domain)
        if not zone_id:
            return {"error": "Zone not found"}

        try:
            session = await self._get_session()

            rule_data = {
                "targets": [{
                    "target": "url",
                    "constraint": {
                        "operator": "matches",
                        "value": url_pattern
                    }
                }],
                "actions": actions,
                "priority": priority,
                "status": "active"
            }

            response = await session.post(
                f"/zones/{zone_id}/pagerules",
                json=rule_data
            )

            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    logger.info(f"Created page rule for: {url_pattern}")
                    return data["result"]

            logger.error(f"Failed to create page rule: {response.text}")
            return {"error": f"Failed to create page rule: {response.status_code}"}

        except Exception as e:
            logger.error(f"Error creating page rule: {str(e)}")
            return {"error": str(e)}

    async def get_health_check(self, domain: str = "envoyou.com") -> Dict[str, Any]:
        """Get Cloudflare health using a zone-scoped endpoint to match token scopes."""
        try:
            session = await self._get_session()

            zone_id = await self._get_zone_id(domain)
            if not zone_id:
                return {
                    "status": "unhealthy",
                    "api_access": False,
                    "error": "Zone ID not found",
                    "timestamp": datetime.now().isoformat()
                }

            # Use a zone-scoped, read-only endpoint compatible with tokens that have Zone:Read
            response = await session.get(f"/zones/{zone_id}/dns_records", params={"per_page": 1})

            if response.status_code == 200:
                data = response.json()
                # success true indicates token valid for zone scope
                if data.get("success"):
                    return {
                        "status": "healthy",
                        "zone_id": zone_id,
                        "api_access": True,
                        "timestamp": datetime.now().isoformat()
                    }

            # Provide non-sensitive diagnostics
            return {
                "status": "unhealthy",
                "api_access": False,
                "error": f"API returned {response.status_code}",
                "details": response.text[:300],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "api_access": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global Cloudflare service instance
cloudflare_service = CloudflareService()