# Supabase Authentication Integration

This document explains how to use the new Supabase JWT authentication system that replaces manual OAuth handling.

## Overview

The Envoyou API now supports Supabase Auth integration, which simplifies OAuth authentication by leveraging Supabase's built-in OAuth providers (Google, GitHub, etc.). Instead of manually handling OAuth token exchanges, the backend now verifies Supabase JWT tokens.

## Architecture

1. **Frontend**: Uses Supabase Auth SDK to handle OAuth login
2. **Supabase**: Manages OAuth flow and issues JWT tokens
3. **Backend**: Verifies Supabase JWT tokens and creates user sessions

## Environment Variables

Add these variables to your `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
ENABLE_SUPABASE_AUTH=true
```

## API Endpoints

### 1. Verify Supabase Token

**Endpoint**: `POST /auth/supabase/verify`

**Request Body**:
```json
{
  "supabase_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response**:
```json
{
  "access_token": "your-backend-jwt-token",
  "refresh_token": "your-backend-refresh-token",
  "token_type": "bearer",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "name": "User Name",
    "email_verified": true,
    "auth_provider": "supabase"
  },
  "message": "Successfully authenticated with Supabase"
}
```

### 2. Get User Info

**Endpoint**: `GET /auth/supabase/me`

**Headers**:
```
Authorization: Bearer your-supabase-jwt-token
```

**Response**:
```json
{
  "id": "supabase-user-id",
  "email": "user@example.com",
  "name": "User Name",
  "avatar_url": "https://...",
  "email_verified": true
}
```

## Frontend Integration

### Using Supabase Auth SDK

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.REACT_APP_SUPABASE_URL,
  process.env.REACT_APP_SUPABASE_ANON_KEY
)

// Sign in with Google
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: `${window.location.origin}/auth/callback`
  }
})

// Get the JWT token after authentication
const { data: { session } } = await supabase.auth.getSession()
const supabaseToken = session?.access_token

// Send token to your backend
const response = await fetch('/auth/supabase/verify', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    supabase_token: supabaseToken
  })
})

const { access_token, user } = await response.json()
// Use access_token for authenticated API calls
```

## Migration from Manual OAuth

### What Changed

1. **Removed**: Manual OAuth endpoints (`/auth/google/callback`, `/auth/github/callback`)
2. **Added**: Supabase JWT verification endpoints
3. **Updated**: User creation/update logic to handle Supabase user data

### Benefits

- **Simplified Flow**: No need to handle OAuth token exchanges manually
- **Better Security**: Supabase handles OAuth securely
- **Multi-Provider**: Easy to add more OAuth providers through Supabase
- **Token Management**: Supabase handles token refresh automatically

## Testing

### Test the Integration

1. Set up Supabase project and configure OAuth providers
2. Add environment variables to your backend
3. Test the `/auth/supabase/verify` endpoint with a valid Supabase JWT token
4. Verify user creation/update in your database

### Example Test Script

```python
import requests

# Replace with actual Supabase JWT token
supabase_token = "your-supabase-jwt-token"

response = requests.post(
    "http://localhost:8000/auth/supabase/verify",
    json={"supabase_token": supabase_token}
)

print(response.json())
```

## Troubleshooting

### Common Issues

1. **"SUPABASE_JWT_SECRET environment variable is required"**
   - Add `SUPABASE_JWT_SECRET` to your environment variables
   - Get this from Supabase Dashboard > Settings > API > JWT Secret

2. **"Invalid token" error**
   - Verify the Supabase token is valid and not expired
   - Check that the token was issued by your Supabase project

3. **"Database error" during user creation**
   - Ensure your database is properly configured
   - Check database connection and User model

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

This will show detailed logs for authentication processes.

## Security Considerations

1. **JWT Secret**: Never expose `SUPABASE_JWT_SECRET` in client-side code
2. **HTTPS**: Always use HTTPS in production
3. **Token Validation**: The middleware validates token expiration and signature
4. **User Data**: Only essential user data is stored in your database

## Next Steps

1. Update your frontend to use Supabase Auth SDK
2. Test the complete authentication flow
3. Remove old manual OAuth endpoints (optional, they can coexist)
4. Add more OAuth providers through Supabase dashboard
5. Implement proper logout handling
