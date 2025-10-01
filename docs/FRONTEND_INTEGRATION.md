# Frontend Integration Guide

## Overview

    Integration guide for connecting Envoyou SEC API with existing frontend applications.

## Architecture

    envoyou.com (Landing) ←→ api.envoyou.com (SEC API)
    app.envoyou.com (Dashboard) ←→ Supabase (Auth + PostgreSQL)
    docs.envoyou.com (API Docs) ←→ Upstash Redis (Cache)

## Authentication Flow

### 1. User Authentication (Supabase)

```javascript
// Frontend: Login user
const { data, error } = await supabase.auth.signInWithPassword({
    email: 'user@example.com',
    password: 'password'
})

// Get JWT token for API calls
const token = data.session.access_token
```

### 2. API Calls with JWT

```javascript
// Frontend: Call SEC API with Supabase JWT
const response = await fetch('https://api.envoyou.com/v1/emissions/calculate', {
    method: 'POST',
    headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
    },
    body: JSON.stringify({
    company: "Demo Corp",
    scope1: { fuel_type: "natural_gas", amount: 1000, unit: "mmbtu" },
    scope2: { kwh: 500000, grid_region: "US_default" }
    })
})
```

## Available Endpoints

### Authentication (Supabase Integration)

- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /user/profile` - Get user profile
- `PUT /user/profile` - Update user profile

### SEC Compliance API

- `POST /v1/emissions/calculate` - Calculate emissions
- `GET /v1/emissions/factors` - Get emission factors
- `POST /v1/validation/epa` - EPA validation
- `POST /v1/export/sec/package` - Generate SEC package

### User Calculation (History) Endpoints

- `GET /user/calculations` - Get user's calculation history (requires authenticated user)
- `POST /user/calculations` - Save a calculation for the current user (requires authenticated user)
- `GET /user/calculations/{calculation_id}` - Get a single saved calculation
- `DELETE /user/calculations/{calculation_id}` - Delete a saved calculation

Notes:

- All `/user/*` endpoints require an `Authorization: Bearer <supabase_jwt_token>` header issued by Supabase auth.
- Frontend should prefer server-first saves (`POST /user/calculations`) and fall back to `localStorage` when offline; the app implements this hybrid approach.

Example: save a calculation (JSON body contains `company`, `calculation_data`, `result`, `version`)

```bash
curl -X POST "https://api.envoyou.com/user/calculations" \
    -H "Authorization: Bearer $SUPABASE_JWT" \
    -H "Content-Type: application/json" \
    -d '{"company":"Demo Corp","calculation_data": {"scope1": {"fuel_type":"natural_gas","amount":100}},"result": {"total_emissions": 1234},"version":"v0.1.0"}'
```

## Frontend Components Needed

### 1. SEC Emissions Calculator (UI)

```jsx
// app.envoyou.com/sec-calculator
const SECCalculator = () => {
    const [formData, setFormData] = useState({
    company: '',
    scope1: { fuel_type: '', amount: 0, unit: '' },
    scope2: { kwh: 0, grid_region: '' }
    })

    const calculateEmissions = async () => {
    const response = await apiClient.post('/v1/emissions/calculate', formData)
    // Handle response
    }

    return (
    <form onSubmit={calculateEmissions}>
        {/* Form fields */}
    </form>
    )
}
```

### 2. EPA Validation Results

```jsx
// Display validation results with flags
const ValidationResults = ({ validationData }) => {
    return (
    <div className="validation-results">
        {validationData.flags.map(flag => (
        <div key={flag.code} className={`alert alert-${flag.severity}`}>
            {flag.message}
        </div>
        ))}
    </div>
    )
}
```

### 3. SEC Package Download

```jsx
// Download SEC filing package
const SECExport = ({ calculationData }) => {
    const downloadPackage = async () => {
    const response = await apiClient.post('/v1/export/sec/package', calculationData)
    // Download ZIP file
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'sec-filing-package.zip'
    a.click()
    }

    return (
    <button onClick={downloadPackage}>
        Download SEC Package
    </button>
    )
}
```

## Environment Variables

### Frontend (.env)

```bash
NEXT_PUBLIC_API_URL=https://api.envoyou.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### Backend (Production)

```bash
DATABASE_URL=postgresql://postgres:[password]@db.your-project.supabase.co:5432/postgres
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
CORS_ALLOWED_ORIGINS=https://envoyou.com,https://app.envoyou.com,https://docs.envoyou.com
REDIS_URL=redis://your-upstash-redis-url
```

## API Client Setup

### JavaScript/TypeScript

```typescript
// utils/apiClient.ts
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

class APIClient {
    private baseURL = process.env.NEXT_PUBLIC_API_URL

    async request(endpoint: string, options: RequestInit = {}) {
    const { data: { session } } = await supabase.auth.getSession()

    return fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers: {
        'Authorization': `Bearer ${session?.access_token}`,
        'Content-Type': 'application/json',
        ...options.headers
        }
    })
    }

    async post(endpoint: string, data: any) {
    return this.request(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
    })
    }
}

export const apiClient = new APIClient()
```

## Next Steps

1. **Update app.envoyou.com**:

    - Add SEC Calculator page
    - Integrate with Supabase auth
    - Add EPA validation display
    - Add SEC package download

2. **Update docs.envoyou.com**:

    - Document SEC API endpoints
    - Add authentication examples
    - Update from CEVS to SEC focus

3. **Testing**:

    - Test auth flow end-to-end
    - Validate CORS configuration
    - Test all SEC API endpoints from frontend

## Support

For integration support, check:

- API documentation: [https://docs.envoyou.com](https://docs.envoyou.com)
- Health check: [https://api.envoyou.com/health](https://api.envoyou.com/health)
- Contact: <support@envoyou.com>

For integration support, check:

- API documentation: [https://docs.envoyou.com](https://docs.envoyou.com)
- Health check: [https://api.envoyou.com/health](https://api.envoyou.com/health)
- Contact: <support@envoyou.com>

## Environment Variables

### Frontend (.env)

```bash
NEXT_PUBLIC_API_URL=https://api.envoyou.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### Backend (Production)

```bash
DATABASE_URL=postgresql://postgres:[password]@db.your-project.supabase.co:5432/postgres
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
CORS_ALLOWED_ORIGINS=https://envoyou.com,https://app.envoyou.com,https://docs.envoyou.com
REDIS_URL=redis://your-upstash-redis-url
```

## API Client Setup

### JavaScript/TypeScript

```typescript
// utils/apiClient.ts
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,


- API documentation: [https://docs.envoyou.com](https://docs.envoyou.com)
- Health check: [https://api.envoyou.com/health](https://api.envoyou.com/health)
- Contact: <support@envoyou.com>
