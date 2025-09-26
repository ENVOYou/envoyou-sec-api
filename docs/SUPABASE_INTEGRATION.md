# Supabase Integration Guide

## Overview

Integration guide for Envoyou SEC API with Supabase PostgreSQL and Auth.

## Existing Supabase Tables

Current tables in Supabase database:
- `api_keys` - API key management
- `notification_preferences` - User notification settings
- `notification_templates` - Email/notification templates
- `notifications` - User notifications
- `profiles` - User profile data
- `sessions` - User session management
- `users` - User authentication data

## New SEC API Tables

Added tables for SEC compliance functionality:

### 1. `audit_trail`
```sql
-- SEC compliance audit trail
- id (SERIAL PRIMARY KEY)
- source_file (VARCHAR) - Source of calculation
- calculation_version (VARCHAR) - Version of calculation engine
- company_cik (VARCHAR) - Company identifier
- inputs (JSONB) - Input data for calculation
- factors (JSONB) - Emission factors used
- source_urls (TEXT[]) - Data source URLs
- timestamp (TIMESTAMPTZ) - When calculation was performed
- notes (TEXT) - Additional notes
```

### 2. `company_facility_map`
```sql
-- Company to facility mapping for EPA validation
- id (SERIAL PRIMARY KEY)
- company (VARCHAR UNIQUE) - Company name
- facility_id (VARCHAR) - EPA facility ID
- facility_name (VARCHAR) - Facility name
- state (VARCHAR) - State code
- notes (TEXT) - Additional notes
```

### 3. `emissions_calculations`
```sql
-- User emissions calculation history
- id (SERIAL PRIMARY KEY)
- user_id (UUID) - References auth.users(id)
- company (VARCHAR) - Company name
- calculation_data (JSONB) - Input data
- result (JSONB) - Calculation result
- version (VARCHAR) - Calculation version
```

### 4. `sec_export_packages`
```sql
-- SEC export package tracking
- id (SERIAL PRIMARY KEY)
- user_id (UUID) - References auth.users(id)
- company (VARCHAR) - Company name
- package_data (JSONB) - Package metadata
- file_url (TEXT) - Download URL
- file_size (INTEGER) - File size in bytes
```

## Row Level Security (RLS)

### Admin-Only Tables
- `audit_trail` - Only admin@envoyou.com and hello@envoyou.com
- `company_facility_map` - Only admin users

### User-Specific Tables
- `emissions_calculations` - Users can only access their own records
- `sec_export_packages` - Users can only access their own packages

## Migration Instructions

### 1. Run Migration Script
```bash
# Make sure .env.production has DATABASE_URL
./scripts/run_supabase_migration.sh
```

### 2. Verify Tables Created
```sql
-- Connect to Supabase and check tables
\dt

-- Check new SEC tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('audit_trail', 'company_facility_map', 'emissions_calculations', 'sec_export_packages');
```

### 3. Test RLS Policies
```sql
-- Test as authenticated user
SELECT * FROM emissions_calculations; -- Should only show user's records
SELECT * FROM audit_trail; -- Should be empty unless admin
```

## Authentication Integration

### JWT Token Structure
```json
{
  "iss": "supabase",
  "ref": "mxxyzzvwrkafcldokehp",
  "role": "authenticated",
  "iat": 1757401325,
  "exp": 2072977325,
  "email": "user@example.com",
  "sub": "user-uuid-here"
}
```

### API Authentication Flow
```python
# Backend: Validate Supabase JWT
from app.utils.supabase_auth import verify_jwt_token

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/v1/"):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user = verify_jwt_token(token)
        request.state.user = user
    response = await call_next(request)
    return response
```

## Environment Variables

### Required for Supabase Integration
```bash
DATABASE_URL=postgresql://postgres.mxxyzzvwrkafcldokehp:password@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://mxxyzzvwrkafcldokehp.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret-here
ENABLE_SUPABASE_AUTH=true
```

## Frontend Integration

### 1. Supabase Client Setup
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://mxxyzzvwrkafcldokehp.supabase.co',
  'your-anon-key'
)
```

### 2. Authentication
```javascript
// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Get session for API calls
const { data: { session } } = await supabase.auth.getSession()
const token = session?.access_token
```

### 3. API Calls
```javascript
// Call SEC API with Supabase JWT
const response = await fetch('https://api.envoyou.com/v1/emissions/calculate', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(calculationData)
})
```

## Database Backup & Recovery

### Automated Backups
- Supabase provides automated daily backups
- Point-in-time recovery available
- Manual backups can be triggered via Supabase dashboard

### Manual Backup
```bash
# Backup specific SEC tables
pg_dump "$DATABASE_URL" \
  --table=audit_trail \
  --table=company_facility_map \
  --table=emissions_calculations \
  --table=sec_export_packages \
  > sec_api_backup.sql
```

## Monitoring & Performance

### Key Metrics to Monitor
- Connection pool usage
- Query performance on JSONB columns
- RLS policy performance
- Index usage on frequently queried columns

### Optimization Tips
- Use JSONB indexes for complex queries
- Monitor slow queries via Supabase dashboard
- Consider partitioning for large audit_trail table
- Use connection pooling for high traffic

## Troubleshooting

### Common Issues
1. **RLS Policy Errors**: Check JWT token contains correct email/user_id
2. **Connection Timeouts**: Verify DATABASE_URL and connection limits
3. **Migration Failures**: Check table permissions and existing data conflicts

### Debug Commands
```sql
-- Check RLS policies
SELECT * FROM pg_policies WHERE tablename = 'audit_trail';

-- Check user permissions
SELECT * FROM information_schema.role_table_grants 
WHERE table_name = 'emissions_calculations';

-- Monitor active connections
SELECT * FROM pg_stat_activity WHERE datname = 'postgres';
```