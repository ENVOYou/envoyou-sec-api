# MCP Servers for Envoyou SEC API

Model Context Protocol (MCP) servers untuk integrasi dengan Supabase, Redis (Upstash), dan Cloudflare.

## Setup

1. **Install dependencies**:
```bash
pip install supabase redis requests
```

2. **Set environment variables**:
```bash
export SUPABASE_URL="your_supabase_url"
export SUPABASE_ANON_KEY="your_supabase_key"
export REDIS_URL="your_upstash_redis_url"
export CLOUDFLARE_API_TOKEN="your_cloudflare_token"
export CLOUDFLARE_ACCOUNT_ID="your_cloudflare_account_id"
```

## Usage

### Supabase MCP

```bash
# Query table
python3 mcp/servers/supabase_mcp.py query '{"table": "users", "filters": {"email": "test@example.com"}}'

# Insert data
python3 mcp/servers/supabase_mcp.py insert '{"table": "users", "data": {"email": "new@example.com", "name": "New User"}}'

# Update data
python3 mcp/servers/supabase_mcp.py update '{"table": "users", "filters": {"email": "test@example.com"}, "data": {"name": "Updated Name"}}'

# Delete data
python3 mcp/servers/supabase_mcp.py delete '{"table": "users", "filters": {"email": "test@example.com"}}'
```

### Redis MCP

```bash
# Get value
python3 mcp/servers/redis_mcp.py get '{"key": "user:123"}'

# Set value with TTL
python3 mcp/servers/redis_mcp.py set '{"key": "user:123", "value": {"name": "John"}, "ttl": 3600}'

# Delete key
python3 mcp/servers/redis_mcp.py delete '{"key": "user:123"}'

# List keys
python3 mcp/servers/redis_mcp.py keys '{"pattern": "user:*"}'

# Check rate limit
python3 mcp/servers/redis_mcp.py rate_limit_check '{"key": "ratelimit:user:123", "limit": 10, "window": 60}'
```

### Cloudflare MCP

```bash
# Purge cache
python3 mcp/servers/cloudflare_mcp.py purge_cache '{"zone_id": "your_zone_id"}'

# Get analytics
python3 mcp/servers/cloudflare_mcp.py get_zone_analytics '{"zone_id": "your_zone_id"}'

# List DNS records
python3 mcp/servers/cloudflare_mcp.py list_dns_records '{"zone_id": "your_zone_id"}'

# Create DNS record
python3 mcp/servers/cloudflare_mcp.py create_dns_record '{"zone_id": "your_zone_id", "record_type": "A", "name": "api", "content": "1.2.3.4"}'

# Get firewall rules
python3 mcp/servers/cloudflare_mcp.py get_firewall_rules '{"zone_id": "your_zone_id"}'
```

## Integration with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "supabase": {
      "command": "python3",
      "args": ["/path/to/envoyou-sec-api/mcp/servers/supabase_mcp.py"],
      "env": {
        "SUPABASE_URL": "your_url",
        "SUPABASE_ANON_KEY": "your_key"
      }
    },
    "redis": {
      "command": "python3",
      "args": ["/path/to/envoyou-sec-api/mcp/servers/redis_mcp.py"],
      "env": {
        "REDIS_URL": "your_redis_url"
      }
    },
    "cloudflare": {
      "command": "python3",
      "args": ["/path/to/envoyou-sec-api/mcp/servers/cloudflare_mcp.py"],
      "env": {
        "CLOUDFLARE_API_TOKEN": "your_token",
        "CLOUDFLARE_ACCOUNT_ID": "your_account_id"
      }
    }
  }
}
```

## Features

### Supabase MCP
- Query tables with filters
- Insert, update, delete operations
- Full CRUD support

### Redis MCP
- Get/Set/Delete operations
- Key pattern matching
- Rate limiting checks
- TTL support

### Cloudflare MCP
- Cache purging
- Zone analytics
- DNS management
- Firewall rules

## Security

- All credentials via environment variables
- No hardcoded secrets
- Token-based authentication
