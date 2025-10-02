#!/usr/bin/env python3
"""MCP Server for Redis (Upstash) operations"""
import os
import json
import redis

class RedisMCP:
    def __init__(self):
        self.client = redis.from_url(
            os.getenv("REDIS_URL"),
            decode_responses=True
        )
    
    def get(self, key: str) -> dict:
        """Get value from Redis"""
        value = self.client.get(key)
        return {"value": json.loads(value) if value else None}
    
    def set(self, key: str, value: Any, ttl: int = None) -> dict:
        """Set value in Redis"""
        if ttl:
            self.client.setex(key, ttl, json.dumps(value))
        else:
            self.client.set(key, json.dumps(value))
        return {"success": True}
    
    def delete(self, key: str) -> dict:
        """Delete key from Redis"""
        deleted = self.client.delete(key)
        return {"deleted": bool(deleted)}
    
    def keys(self, pattern: str = "*") -> dict:
        """List keys matching pattern"""
        keys = self.client.keys(pattern)
        return {"keys": keys}
    
    def rate_limit_check(self, key: str, limit: int, window: int) -> dict:
        """Check rate limit"""
        import time
        now = int(time.time())
        window_start = now - window
        
        self.client.zremrangebyscore(key, '-inf', window_start)
        current = self.client.zcard(key)
        
        if current >= limit:
            return {"allowed": False, "remaining": 0}
        
        self.client.zadd(key, {str(now): now})
        self.client.expire(key, window)
        return {"allowed": True, "remaining": limit - current - 1}

def main():
    import sys
    mcp = RedisMCP()
    
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: redis_mcp.py <command> [args]"}))
        sys.exit(1)
    
    command = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    
    commands = {
        "get": lambda: mcp.get(**args),
        "set": lambda: mcp.set(**args),
        "delete": lambda: mcp.delete(**args),
        "keys": lambda: mcp.keys(**args),
        "rate_limit_check": lambda: mcp.rate_limit_check(**args),
    }
    
    result = commands.get(command, lambda: {"error": "Unknown command"})()
    print(json.dumps(result))

if __name__ == "__main__":
    main()
