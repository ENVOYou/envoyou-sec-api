# API Keys Management Guide

## Overview

Complete guide for managing API keys in Envoyou SEC API with Supabase authentication.

## Available Endpoints

### User API Key Management
- `GET /user/api-keys` - List all API keys
- `POST /user/api-keys` - Create new API key
- `DELETE /user/api-keys/{key_id}` - Delete API key

### Personal API Token
- `GET /user/api-token` - Get personal token info
- `POST /user/api-token` - Create personal token
- `POST /user/api-token/regenerate` - Regenerate token

### User Profile & Sessions
- `GET /user/profile` - Get user profile
- `PUT /user/profile` - Update profile
- `GET /user/sessions` - List active sessions
- `DELETE /user/sessions/{session_id}` - Delete session

## Authentication Flow

### 1. User Login (Supabase)
```javascript
// Frontend: Login with Supabase
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

const jwtToken = data.session.access_token
```

### 2. Create API Key
```javascript
// Create API key for SEC API access
const response = await fetch('https://api.envoyou.com/user/api-keys', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'SEC Calculator Key',
    permissions: ['emissions:calculate', 'validation:epa', 'export:sec']
  })
})

const { key, prefix, id } = await response.json()
// Save the key securely - it's only shown once!
```

### 3. Use API Key for SEC Endpoints
```javascript
// Use API key for SEC calculations
const response = await fetch('https://api.envoyou.com/v1/emissions/calculate', {
  method: 'POST',
  headers: {
    'X-API-Key': key, // Use the API key from step 2
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    company: "Demo Corp",
    scope1: { fuel_type: "natural_gas", amount: 1000, unit: "mmbtu" },
    scope2: { kwh: 500000, grid_region: "US_default" }
  })
})
```

## API Key Types

### 1. Personal API Token
- **Purpose**: Quick access for personal use
- **Permissions**: Basic read access
- **Management**: Can be regenerated easily
- **Usage**: Development and testing

### 2. Named API Keys
- **Purpose**: Production applications
- **Permissions**: Customizable permissions
- **Management**: Full CRUD operations
- **Usage**: Frontend applications, integrations

## Permissions System

### Available Permissions
```json
{
  "emissions:calculate": "Calculate emissions",
  "emissions:factors": "Access emission factors",
  "validation:epa": "EPA cross-validation",
  "export:sec": "SEC package export",
  "admin:mappings": "Manage facility mappings",
  "audit:read": "Read audit trail"
}
```

### Permission Examples
```javascript
// Basic user permissions
{
  "name": "Frontend App",
  "permissions": [
    "emissions:calculate",
    "emissions:factors", 
    "validation:epa",
    "export:sec"
  ]
}

// Admin permissions
{
  "name": "Admin Dashboard",
  "permissions": [
    "emissions:calculate",
    "validation:epa",
    "export:sec",
    "admin:mappings",
    "audit:read"
  ]
}
```

## Frontend Integration Examples

### React Hook for API Keys
```jsx
// hooks/useApiKeys.js
import { useState, useEffect } from 'react'
import { useSupabaseClient, useUser } from '@supabase/auth-helpers-react'

export const useApiKeys = () => {
  const [apiKeys, setApiKeys] = useState([])
  const [loading, setLoading] = useState(true)
  const supabase = useSupabaseClient()
  const user = useUser()

  const fetchApiKeys = async () => {
    if (!user) return
    
    const { data: { session } } = await supabase.auth.getSession()
    const response = await fetch('/user/api-keys', {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    })
    
    const data = await response.json()
    setApiKeys(data.api_keys)
    setLoading(false)
  }

  const createApiKey = async (name, permissions) => {
    const { data: { session } } = await supabase.auth.getSession()
    const response = await fetch('/user/api-keys', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name, permissions })
    })
    
    const newKey = await response.json()
    await fetchApiKeys() // Refresh list
    return newKey
  }

  useEffect(() => {
    fetchApiKeys()
  }, [user])

  return { apiKeys, loading, createApiKey, fetchApiKeys }
}
```

### API Key Management Component
```jsx
// components/ApiKeyManager.jsx
import { useState } from 'react'
import { useApiKeys } from '../hooks/useApiKeys'

const ApiKeyManager = () => {
  const { apiKeys, loading, createApiKey } = useApiKeys()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newKeyData, setNewKeyData] = useState({ name: '', permissions: [] })

  const handleCreateKey = async (e) => {
    e.preventDefault()
    const result = await createApiKey(newKeyData.name, newKeyData.permissions)
    
    // Show the key to user (only time it's visible)
    alert(`API Key created: ${result.key}\nSave this key securely!`)
    
    setShowCreateForm(false)
    setNewKeyData({ name: '', permissions: [] })
  }

  if (loading) return <div>Loading...</div>

  return (
    <div className="api-key-manager">
      <h2>API Keys</h2>
      
      <div className="api-keys-list">
        {apiKeys.map(key => (
          <div key={key.id} className="api-key-item">
            <h3>{key.name}</h3>
            <p>Prefix: {key.prefix}***</p>
            <p>Created: {new Date(key.created_at).toLocaleDateString()}</p>
            <p>Last Used: {key.last_used ? new Date(key.last_used).toLocaleDateString() : 'Never'}</p>
            <p>Usage: {key.usage_count} calls</p>
          </div>
        ))}
      </div>

      <button onClick={() => setShowCreateForm(true)}>
        Create New API Key
      </button>

      {showCreateForm && (
        <form onSubmit={handleCreateKey}>
          <input
            type="text"
            placeholder="Key name"
            value={newKeyData.name}
            onChange={(e) => setNewKeyData({...newKeyData, name: e.target.value})}
            required
          />
          
          <div className="permissions">
            {['emissions:calculate', 'validation:epa', 'export:sec'].map(perm => (
              <label key={perm}>
                <input
                  type="checkbox"
                  checked={newKeyData.permissions.includes(perm)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setNewKeyData({
                        ...newKeyData,
                        permissions: [...newKeyData.permissions, perm]
                      })
                    } else {
                      setNewKeyData({
                        ...newKeyData,
                        permissions: newKeyData.permissions.filter(p => p !== perm)
                      })
                    }
                  }}
                />
                {perm}
              </label>
            ))}
          </div>
          
          <button type="submit">Create Key</button>
          <button type="button" onClick={() => setShowCreateForm(false)}>Cancel</button>
        </form>
      )}
    </div>
  )
}

export default ApiKeyManager
```

## Security Best Practices

### 1. API Key Storage
- **Frontend**: Store in secure HTTP-only cookies or encrypted localStorage
- **Backend**: Hash keys in database, never store plain text
- **Mobile**: Use secure keychain/keystore

### 2. Key Rotation
```javascript
// Rotate API keys regularly
const rotateApiKey = async (keyId) => {
  // Delete old key
  await fetch(`/user/api-keys/${keyId}`, { method: 'DELETE' })
  
  // Create new key with same permissions
  const newKey = await createApiKey('Rotated Key', permissions)
  
  // Update application configuration
  updateAppConfig({ apiKey: newKey.key })
}
```

### 3. Permission Principle
- Grant minimum required permissions
- Use specific permissions, avoid wildcards
- Regular permission audits

## Monitoring & Analytics

### Usage Tracking
```javascript
// Get API key usage statistics
const getUsageStats = async () => {
  const response = await fetch('/user/stats', {
    headers: { 'Authorization': `Bearer ${jwtToken}` }
  })
  
  const stats = await response.json()
  return {
    totalCalls: stats.total_calls,
    monthlyUsage: stats.monthly_calls,
    quota: stats.quota,
    activeKeys: stats.active_keys
  }
}
```

### Rate Limiting
- Default: 100 requests per minute per API key
- Burst allowance: 120% of rate limit
- Upgrade plans for higher limits

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check API key is valid and active
   - Verify X-API-Key header format
   - Ensure key has required permissions

2. **403 Forbidden**
   - Check user has permission for endpoint
   - Verify Supabase JWT is valid
   - Check RLS policies in database

3. **429 Rate Limited**
   - Implement exponential backoff
   - Check rate limit headers
   - Consider upgrading plan

### Debug Commands
```bash
# Test API key validity
curl -H "X-API-Key: your-key" https://api.envoyou.com/v1/emissions/factors

# Check user profile
curl -H "Authorization: Bearer jwt-token" https://api.envoyou.com/user/profile

# List API keys
curl -H "Authorization: Bearer jwt-token" https://api.envoyou.com/user/api-keys
```