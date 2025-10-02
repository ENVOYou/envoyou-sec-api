#!/usr/bin/env python3
"""Test script for MCP servers"""
import subprocess
import json
import sys
import os

def test_supabase():
    """Test Supabase MCP"""
    print("\n=== Testing Supabase MCP ===")
    
    # Test query
    cmd = ['python3', 'mcp/servers/supabase_mcp.py', 'query', 
           json.dumps({"table": "audit_trail", "select": "*"})]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if "ModuleNotFoundError" in result.stderr:
        print("Skipped - supabase module not installed (run: pip install -r mcp/requirements.txt)")
        return True
    
    if "Invalid API key" in result.stderr:
        print("Skipped - Invalid Supabase API key (check SUPABASE_ANON_KEY in .env)")
        return True
    
    print(f"Query: {result.stdout}")
    if result.stderr:
        print(f"Error: {result.stderr}")
    
    try:
        data = json.loads(result.stdout)
        return result.returncode == 0 and data.get("success", False)
    except:
        return False

def test_redis():
    """Test Redis MCP"""
    print("\n=== Testing Redis MCP ===")
    
    # Test set
    cmd = ['python3', 'mcp/servers/redis_mcp.py', 'set',
           json.dumps({"key": "test:mcp", "value": {"test": "data"}, "ttl": 60})]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Set: {result.stdout}")
    
    # Test get
    cmd = ['python3', 'mcp/servers/redis_mcp.py', 'get',
           json.dumps({"key": "test:mcp"})]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Get: {result.stdout}")
    
    return result.returncode == 0

def test_cloudflare():
    """Test Cloudflare MCP"""
    print("\n=== Testing Cloudflare MCP ===")
    import os
    
    # Use zone_id from env or skip
    zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
    if not zone_id:
        print("Skipped - no CLOUDFLARE_ZONE_ID in env")
        return True
    
    cmd = ['python3', 'mcp/servers/cloudflare_mcp.py', 'get_zone_details',
           json.dumps({"zone_id": zone_id})]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Zone Details: {result.stdout}")
    
    return result.returncode == 0

if __name__ == "__main__":
    print("MCP Servers Test Suite")
    print("=" * 50)
    
    results = {
        "Supabase": test_supabase(),
        "Redis": test_redis(),
        "Cloudflare": test_cloudflare()
    }
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
    
    sys.exit(0 if all(results.values()) else 1)
