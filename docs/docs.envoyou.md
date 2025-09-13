# EnvoyOU API Documentation

## Table of Contents

- [Introduction](#introduction)
  - [What is EnvoyOU, Purpose, Value](#what-is-envoyou-purpose-value)
  - [Real Use Cases](#real-use-cases)
- [Getting Started](#getting-started)
  - [How to Register, Login, Get API Key](#how-to-register-login-get-api-key)
  - [Quickstart](#quickstart)
- [Authentication](#authentication)
  - [Authentication Scheme](#authentication-scheme)
  - [Request + Response Examples](#request--response-examples)
- [API Reference](#api-reference)
  - [Endpoint /v1/auth/register](#endpoint-v1authregister)
  - [Endpoint /v1/auth/login](#endpoint-v1authlogin)
  - [Other Data Endpoints](#other-data-endpoints)
  - [Request & Response Format](#request--response-format)
- [Errors](#errors)
  - [400 Bad Request, 401 Unauthorized, etc](#400-bad-request-401-unauthorized-etc)
  - [General Debug Tips](#general-debug-tips)
- [Guides / Tutorials](#guides--tutorials)
  - [Step by Step Web App Integration](#step-by-step-web-app-integration)
  - [How to Verify Environmental Dataset](#how-to-verify-environmental-dataset)
- [FAQ](#faq)
  - [Common Errors](#common-errors)
  - [Limitations](#limitations)
- [Changelog](#changelog)
  -   - [API Versions, Feature Updates, Breaking Changes](#api-versions-feature-updates-breaking-changes)
- [Support](#support)
  - [Contact Email](#contact-email)

---

## Introduction

### What is EnvoyOU, Purpose, Value

**EnvoyOU** is a sophisticated API platform for global environmental data aggregation that calculates the **Composite Environmental Verification Score (CEVS)** - a standard metric for corporate environmental performance.

#### Vision
To create a dynamic and real-time global environmental verification platform that provides not only static scores but also continuous updates based on the latest data. This enables benchmarking of company and sector performance, and supports global efforts towards sustainable development.

#### Mission
- **Environmental Data Verification**: Provide a structured and unified API for environmental verification data.
- **CEVS Calculation**: Develop a holistic composite score for evaluating company environmental performance.
- **Multi-Source Integration**: Combine data from EPA, EEA, ISO, EDGAR, KLHK, and others with standard normalization.
- **Data Standardization**: Transform fragmented raw data into consistent and integrated insights.
- **Transparency and Accessibility**: Ensure data is easily accessible to ESG investors, supply chain managers, regulators, and developers through a secure and scalable API.

#### Value Proposition
- **For ESG Investors**: Transparent score evaluation for sustainable investments.
- **For Supply Chain Managers**: Environmental compliance checks in supply chains.
- **For Regulators**: Real-time monitoring of industry performance.
- **For Developers**: Ready-to-use standard API for application integration.

#### Goals
- **Target Users**: ESG Investors, Supply Chain Managers, Regulators, Developers.
- **Key Metrics**: Response Time < 2 seconds, Uptime 99.9%, Tier-based Rate Limiting.
- **Development Phases**: Current MVP Global, ongoing expansion to national data, harmonization protocols.

### Real Use Cases

1. **ESG Investment Screening**: Investors use CEVS to assess environmental risks before investing in companies.
2. **Supply Chain Compliance**: Manufacturing companies verify their suppliers' environmental compliance.
3. **Regulatory Monitoring**: Governments monitor industrial pollution trends using aggregated data.
4. **Corporate Reporting**: Companies generate automated ESG reports based on CEVS scores.
5. **Academic Research**: Researchers access standardized environmental data for impact studies.

---

## Getting Started

### How to Register, Login, Get API Key

1. **Register Account**:
   - Visit `https://app.envoyou.com`
   - Click "Sign Up"
   - Enter email, password (min 8 characters with uppercase, lowercase, numbers), name, company (optional)
   - Verify email via sent link

2. **Login**:
   - Login with email and password
   - Receive access token and refresh token

3. **Get API Key**:
   - After login, go to Developer Dashboard
   - Select tier: Basic (free), Premium, Enterprise
   - Generate API key for data endpoint authentication

### Quickstart

#### Using cURL

**Register**:
```bash
curl -X POST https://api.envoyou.com/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password123",
    "name": "John Doe",
    "company": "Example Corp"
  }'
```

**Login**:
```bash
curl -X POST https://api.envoyou.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password123"
  }'
```

**Get Data**:
```bash
curl -X GET "https://api.envoyou.com/v1/global/emissions?limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-API-Key: YOUR_API_KEY"
```

#### Using Python

```python
import requests

# Login
response = requests.post('https://api.envoyou.com/v1/auth/login', json={
    'email': 'user@example.com',
    'password': 'Password123'
})
token = response.json()['access_token']

# Get data
headers = {
    'Authorization': f'Bearer {token}',
    'X-API-Key': 'YOUR_API_KEY'
}
data = requests.get('https://api.envoyou.com/v1/global/emissions', headers=headers)
print(data.json())
```

#### Using JavaScript

```javascript
// Login
const loginResponse = await fetch('https://api.envoyou.com/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'Password123'
  })
});
const { access_token } = await loginResponse.json();

// Get data
const dataResponse = await fetch('https://api.envoyou.com/v1/global/emissions', {
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'X-API-Key': 'YOUR_API_KEY'
  }
});
const data = await dataResponse.json();
console.log(data);
```

---

## Authentication

### Authentication Scheme

EnvoyOU uses a combination of JWT (JSON Web Token) and API Key for authentication:

- **JWT**: For user authentication (login/register)
  - Access Token: Valid for 15 minutes
  - Refresh Token: To get new access token
- **API Key**: For data endpoint access
  - Tier-based: Basic (1000 requests/day), Premium (10000), Enterprise (unlimited)
  - Rate limiting with Redis

### Request + Response Examples

**Login Request**:
```json
POST /v1/auth/login
{
  "email": "user@example.com",
  "password": "Password123"
}
```

**Login Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "123",
    "email": "user@example.com",
    "name": "John Doe",
    "company": "Example Corp"
  }
}
```

---

## API Reference

### Endpoint /v1/auth/register

**Method**: POST  
**Description**: Register new user account  
**Authentication**: None required  

**Request Body**:
```json
{
  "email": "string (required)",
  "password": "string (required, min 8 chars)",
  "name": "string (required)",
  "company": "string (optional)",
  "job_title": "string (optional)"
}
```

**Response (200)**:
```json
{
  "success": true,
  "message": "Registration successful. Please check your email to verify your account.",
  "email_sent": true
}
```

**Response (400)**:
```json
{
  "detail": "Password must be at least 8 characters with uppercase, lowercase, and number"
}
```

### Endpoint /v1/auth/login

**Method**: POST  
**Description**: Authenticate user and get tokens  
**Authentication**: None required  

**Request Body**:
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

**Response (200)**:
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user": {
    "id": "string",
    "email": "string",
    "name": "string",
    "company": "string"
  }
}
```

**Response (401)**:
```json
{
  "detail": "Invalid email or password"
}
```

### Other Data Endpoints

#### /v1/global/emissions
**Method**: GET  
**Description**: Get US emissions data  
**Authentication**: API Key required  

**Query Parameters**:
- `state`: string (optional) - Filter by state
- `year`: integer (optional) - Filter by year
- `pollutant`: string (optional) - Filter by pollutant
- `limit`: integer (default 50, max 100)

**Response (200)**:
```json
{
  "data": [
    {
      "facility_name": "Plant A",
      "state": "CA",
      "year": 2023,
      "pollutant": "CO2",
      "emissions": 1000.5
    }
  ],
  "source": "epa",
  "total": 1
}
```

#### /v1/global/eea/renewables
**Method**: GET  
**Description**: Get EEA renewable energy data  
**Authentication**: API Key required  

#### /v1/global/iso/certifications
**Method**: GET  
**Description**: Get ISO 14001 certifications  
**Authentication**: API Key required  

#### /v1/permits/search
**Method**: GET  
**Description**: Search Indonesian environmental permits  
**Authentication**: API Key required  

### Request & Response Format

All requests use JSON. Responses always in format:
```json
{
  "success": boolean,
  "data": object/array,
  "message": "string (optional)",
  "error": "string (optional)"
}
```

---

## Errors

### 400 Bad Request, 401 Unauthorized, etc

- **400 Bad Request**: Invalid or missing parameters
- **401 Unauthorized**: Invalid or expired token/API key
- **403 Forbidden**: Unverified email or access denied
- **404 Not Found**: Endpoint or resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### General Debug Tips

1. **401 Error**: Check token expiration, ensure "Bearer <token>" format
2. **429 Error**: Wait for reset window or upgrade tier
3. **Infinite Loading**: Check internet connection, CORS settings
4. **404 Error**: Verify endpoint URL and method
5. **Email Verification**: Check spam folder for verification email

---

## Guides / Tutorials

### Step by Step Web App Integration

1. **Setup Project**:
   ```bash
   npm install axios
   ```

2. **Create API Client**:
   ```javascript
   class EnvoyouAPI {
     constructor(apiKey) {
       this.apiKey = apiKey;
       this.baseURL = 'https://api.envoyou.com/v1';
     }

     async login(email, password) {
       const response = await fetch(`${this.baseURL}/auth/login`, {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ email, password })
       });
       const data = await response.json();
       this.token = data.access_token;
       return data;
     }

     async getEmissions(params = {}) {
       const query = new URLSearchParams(params);
       const response = await fetch(`${this.baseURL}/global/emissions?${query}`, {
         headers: {
           'Authorization': `Bearer ${this.token}`,
           'X-API-Key': this.apiKey
         }
       });
       return response.json();
     }
   }
   ```

3. **Use in Component**:
   ```javascript
   const api = new EnvoyouAPI('your-api-key');
   const data = await api.getEmissions({ state: 'CA', limit: 10 });
   ```

### How to Verify Environmental Dataset

1. **Select Endpoint**: Use `/v1/global/emissions` for emission data
2. **Filter Data**: Add state, year, pollutant parameters
3. **Validate**: Compare with original source (EPA website)
4. **CEVS Calculation**: Use `/v1/cevs/calculate` for composite score

---

## FAQ

### Common Errors

**Q: Why 401 Unauthorized?**  
A: Token expired or invalid. Login again for new token.

**Q: Why infinite loading?**  
A: CORS issue or rate limit. Check browser console for errors.

**Q: Email verification not received?**  
A: Check spam folder or contact support@envoyou.com

### Limitations

- **Rate Limits**: Basic: 1000/day, Premium: 10000/day, Enterprise: unlimited
- **Data Freshness**: Cache TTL 1 hour for external data
- **Response Time**: < 2 seconds for main endpoints
- **Data Coverage**: Focus on US/EU/Indonesia, ongoing expansion

---

## Changelog

### v1.0.0 (September 2025)
- Initial release MVP Global
- Authentication system with JWT + API keys
- Endpoints: auth, global emissions, EEA, ISO, permits
- CEVS calculation algorithm
- Production deployment on Railway

### v1.1.0 (Upcoming)
- Enhanced error handling
- Additional data sources
- Improved Redis caching
- Two-factor authentication

### Breaking Changes
- None in v1.0.x
- Future: API versioning for major changes

---

## Support

### Contact Email
support@envoyou.com

For technical assistance, bug reports, or feature requests, send email to support@envoyou.com with detailed information including:
- Used endpoint
- Request/response samples
- Error messages
- Browser/OS info

---

**Last Updated**: September 13, 2025  
**API Version**: v1.0.0  
**Status**: Production Ready

---

## Getting Started

### How to Register, Login, Get API Key

1. **Register Account**:
   - Visit `https://app.envoyou.com`
   - Click "Sign Up"
   - Enter email, password (min 8 characters with uppercase, lowercase, numbers), name, company (optional)
   - Verify email via sent link

2. **Login**:
   - Login with email and password
   - Receive access token and refresh token

3. **Get API Key**:
   - After login, go to Developer Dashboard
   - Select tier: Basic (free), Premium, Enterprise
   - Generate API key for data endpoint authentication

### Quickstart

#### Menggunakan cURL

**Register**:
```bash
curl -X POST https://api.envoyou.com/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password123",
    "name": "John Doe",
    "company": "Example Corp"
  }'
```

**Login**:
```bash
curl -X POST https://api.envoyou.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password123"
  }'
```

**Get Data**:
```bash
curl -X GET "https://api.envoyou.com/v1/global/emissions?limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-API-Key: YOUR_API_KEY"
```

#### Menggunakan Python

```python
import requests

# Login
response = requests.post('https://api.envoyou.com/v1/auth/login', json={
    'email': 'user@example.com',
    'password': 'Password123'
})
token = response.json()['access_token']

# Get data
headers = {
    'Authorization': f'Bearer {token}',
    'X-API-Key': 'YOUR_API_KEY'
}
data = requests.get('https://api.envoyou.com/v1/global/emissions', headers=headers)
print(data.json())
```

#### Menggunakan JavaScript

```javascript
// Login
const loginResponse = await fetch('https://api.envoyou.com/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'Password123'
  })
});
const { access_token } = await loginResponse.json();

// Get data
const dataResponse = await fetch('https://api.envoyou.com/v1/global/emissions', {
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'X-API-Key': 'YOUR_API_KEY'
  }
});
const data = await dataResponse.json();
console.log(data);
```

---

## Authentication

### Authentication Scheme

EnvoyOU uses a combination of JWT (JSON Web Token) and API Key for authentication:

- **JWT**: For user authentication (login/register)
  - Access Token: Valid for 15 minutes
  - Refresh Token: To get new access token
- **API Key**: For data endpoint access
  - Tier-based: Basic (1000 requests/day), Premium (10000), Enterprise (unlimited)
  - Rate limiting with Redis

### Request + Response Examples

**Login Request**:
```json
POST /v1/auth/login
{
  "email": "user@example.com",
  "password": "Password123"
}
```

**Login Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "123",
    "email": "user@example.com",
    "name": "John Doe",
    "company": "Example Corp"
  }
}
```

---

## API Reference

### Endpoint /v1/auth/register

**Method**: POST  
**Description**: Register new user account  
**Authentication**: None required  

**Request Body**:
```json
{
  "email": "string (required)",
  "password": "string (required, min 8 chars)",
  "name": "string (required)",
  "company": "string (optional)",
  "job_title": "string (optional)"
}
```

**Response (200)**:
```json
{
  "success": true,
  "message": "Registration successful. Please check your email to verify your account.",
  "email_sent": true
}
```

**Response (400)**:
```json
{
  "detail": "Password must be at least 8 characters with uppercase, lowercase, and number"
}
```

### Endpoint /v1/auth/login

**Method**: POST  
**Description**: Authenticate user and get tokens  
**Authentication**: None required  

**Request Body**:
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

**Response (200)**:
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user": {
    "id": "string",
    "email": "string",
    "name": "string",
    "company": "string"
  }
}
```

**Response (401)**:
```json
{
  "detail": "Invalid email or password"
}
```

### Other Data Endpoints

#### /v1/global/emissions
**Method**: GET  
**Description**: Get US emissions data  
**Authentication**: API Key required  

**Query Parameters**:
- `state`: string (optional) - Filter by state
- `year`: integer (optional) - Filter by year
- `pollutant`: string (optional) - Filter by pollutant
- `limit`: integer (default 50, max 100)

**Response (200)**:
```json
{
  "data": [
    {
      "facility_name": "Plant A",
      "state": "CA",
      "year": 2023,
      "pollutant": "CO2",
      "emissions": 1000.5
    }
  ],
  "source": "epa",
  "total": 1
}
```

#### /v1/global/eea/renewables
**Method**: GET  
**Description**: Get EEA renewable energy data  
**Authentication**: API Key required  

#### /v1/global/iso/certifications
**Method**: GET  
**Description**: Get ISO 14001 certifications  
**Authentication**: API Key required  

#### /v1/permits/search
**Method**: GET  
**Description**: Search Indonesian environmental permits  
**Authentication**: API Key required  

### Request & Response Format

Semua request menggunakan JSON. Response selalu dalam format:
```json
{
  "success": boolean,
  "data": object/array,
  "message": "string (optional)",
  "error": "string (optional)"
}
```

---

## Errors

### 400 Bad Request, 401 Unauthorized, etc

- **400 Bad Request**: Invalid or missing parameters
- **401 Unauthorized**: Invalid or expired token/API key
- **403 Forbidden**: Unverified email or access denied
- **404 Not Found**: Endpoint or resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### General Debug Tips

1. **401 Error**: Cek token expiration, pastikan format "Bearer <token>"
2. **429 Error**: Tunggu reset window atau upgrade tier
3. **Infinite Loading**: Cek koneksi internet, CORS settings
4. **404 Error**: Verifikasi endpoint URL dan method
5. **Email Verification**: Cek spam folder untuk verification email

---

## Guides / Tutorials

### Step by Step Web App Integration

1. **Setup Project**:
   ```bash
   npm install axios
   ```

2. **Create API Client**:
   ```javascript
   class EnvoyouAPI {
     constructor(apiKey) {
       this.apiKey = apiKey;
       this.baseURL = 'https://api.envoyou.com/v1';
     }

     async login(email, password) {
       const response = await fetch(`${this.baseURL}/auth/login`, {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ email, password })
       });
       const data = await response.json();
       this.token = data.access_token;
       return data;
     }

     async getEmissions(params = {}) {
       const query = new URLSearchParams(params);
       const response = await fetch(`${this.baseURL}/global/emissions?${query}`, {
         headers: {
           'Authorization': `Bearer ${this.token}`,
           'X-API-Key': this.apiKey
         }
       });
       return response.json();
     }
   }
   ```

3. **Use in Component**:
   ```javascript
   const api = new EnvoyouAPI('your-api-key');
   const data = await api.getEmissions({ state: 'CA', limit: 10 });
   ```

### How to Verify Environmental Dataset

1. **Pilih Endpoint**: Gunakan `/v1/global/emissions` untuk data emisi
2. **Filter Data**: Tambahkan parameter state, year, pollutant
3. **Validasi**: Bandingkan dengan sumber asli (EPA website)
4. **CEVS Calculation**: Gunakan `/v1/cevs/calculate` untuk skor komposit

---

## FAQ

### Common Errors

**Q: Why 401 Unauthorized?**  
A: Token expired or invalid. Login again for new token.

**Q: Why infinite loading?**  
A: CORS issue or rate limit. Check browser console for errors.

**Q: Email verification not received?**  
A: Check spam folder or contact support@envoyou.com

### Limitations

- **Rate Limits**: Basic: 1000/hari, Premium: 10000/hari, Enterprise: unlimited
- **Data Freshness**: Cache TTL 1 jam untuk data eksternal
- **Response Time**: < 2 detik untuk endpoint utama
- **Data Coverage**: Fokus US/EU/Indonesia, ekspansi ongoing

---

## Changelog

### v1.0.0 (September 2025)
- Initial release MVP Global
- Authentication system dengan JWT + API keys
- Endpoint: auth, global emissions, EEA, ISO, permits
- CEVS calculation algorithm
- Production deployment di Railway

### v1.1.0 (Upcoming)
- Enhanced error handling
- Additional data sources
- Improved caching dengan Redis
- Two-factor authentication

### Breaking Changes
- None in v1.0.x
- Future: API versioning untuk major changes

---

## Support

### Contact Email
support@envoyou.com

Untuk bantuan teknis, bug reports, atau pertanyaan fitur, kirim email ke support@envoyou.com dengan detail lengkap termasuk:
- Endpoint yang digunakan
- Request/response sample
- Error messages
- Browser/OS info

---

**Last Updated**: September 13, 2025  
**API Version**: v1.0.0  
**Status**: Production Ready</content>
<parameter name="filePath">/home/husni/PROJECT-ENVOYOU-API/api-envoyou/docs/docs.envoyou.md