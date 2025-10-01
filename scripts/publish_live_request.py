#!/usr/bin/env python3
"""Simple helper to publish a test message to Redis channel `live:requests`."""
import json
import time
import sys
from app.services.redis_service import redis_service

def main():
    if not redis_service.is_connected():
        print('Redis not connected; set REDIS_URL and install redis package')
        sys.exit(1)

    prefix = None
    if len(sys.argv) > 1:
        prefix = sys.argv[1]

    payload = {
        'ts': int(time.time() * 1000),
        'path': '/v1/test/publish',
        'method': 'GET',
        'key_prefix': prefix
    }

    ok = redis_service.publish_message('live:requests', payload)
    print('Published:', ok, json.dumps(payload))

if __name__ == '__main__':
    main()
