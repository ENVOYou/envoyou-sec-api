#!/usr/bin/env python3
"""MCP Server for Cloudflare operations"""
import os
import json
import requests

class CloudflareMCP:
    def __init__(self):
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def purge_cache(self, zone_id: str, files: list = None) -> dict:
        """Purge Cloudflare cache"""
        url = f"{self.base_url}/zones/{zone_id}/purge_cache"
        data = {"purge_everything": True} if not files else {"files": files}
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def get_zone_analytics(self, zone_id: str, since: int = -10080) -> dict:
        """Get zone analytics (last 7 days by default)"""
        url = f"{self.base_url}/zones/{zone_id}/analytics/dashboard"
        params = {"since": since}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def list_dns_records(self, zone_id: str) -> dict:
        """List DNS records"""
        url = f"{self.base_url}/zones/{zone_id}/dns_records"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def create_dns_record(self, zone_id: str, record_type: str, name: str, content: str, ttl: int = 1) -> dict:
        """Create DNS record"""
        url = f"{self.base_url}/zones/{zone_id}/dns_records"
        data = {"type": record_type, "name": name, "content": content, "ttl": ttl}
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def get_firewall_rules(self, zone_id: str) -> dict:
        """Get firewall rules"""
        url = f"{self.base_url}/zones/{zone_id}/firewall/rules"
        response = requests.get(url, headers=self.headers)
        return response.json()

def main():
    import sys
    mcp = CloudflareMCP()
    
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: cloudflare_mcp.py <command> [args]"}))
        sys.exit(1)
    
    command = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    
    commands = {
        "purge_cache": lambda: mcp.purge_cache(**args),
        "get_zone_analytics": lambda: mcp.get_zone_analytics(**args),
        "list_dns_records": lambda: mcp.list_dns_records(**args),
        "create_dns_record": lambda: mcp.create_dns_record(**args),
        "get_firewall_rules": lambda: mcp.get_firewall_rules(**args),
    }
    
    result = commands.get(command, lambda: {"error": "Unknown command"})()
    print(json.dumps(result))

if __name__ == "__main__":
    main()
