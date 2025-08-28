# Envoyou CEVS API - Official Documentation

📑 Quick Links
- [📘 Project README](README.md)
- [🚀 Performance Report](PERFORMANCE_IMPROVEMENTS.md)

## 📋 Overview

This API is the core engine of the [Envoyou](https://envoyou.com) platform. It aggregates data from multiple official sources (EPA, EEA, ISO, etc.) to calculate a **Composite Environmental Verification Score (CEVS)**.

Key capabilities include:

✅ **Secure API Key Authentication**
✅ **Tier-Based Rate Limiting**
✅ **Comprehensive Caching** for better performance
✅ **Advanced Data Filtering & Normalization**
✅ **Standardized response format**
✅ **Pagination for large datasets**
✅ **Robust error handling**
✅ **Docker deployment ready**

## 🔐 Authentication & API Keys

### Getting Your API Key
 
**For Development/Testing:**
Use the demo keys provided:
- **Basic Tier**: `demo_key_basic_2025` (30 requests/minute)
- **Premium Tier**: `demo_key_premium_2025` (100 requests/minute)

**For Production:**
Contact the API administrator to get your production API key.

### Using Your API Key

Include your API key in requests using one of these methods:

#### 1. Authorization Header (Recommended)
```bash
curl -H "Authorization: Bearer your_api_key_here" \
  "http://localhost:8000/global/emissions"
```

#### 2. X-API-Key Header  
```bash
curl -H "X-API-Key: your_api_key_here" \
  "http://localhost:8000/global/emissions"
```

#### 3. Query Parameter (Development Only)
```bash
curl "http://localhost:8000/global/emissions?api_key=your_api_key_here"
```

### Rate Limits by Tier

@@ 59,62 @@ | Premium | 100 | Production applications, heavy usage | | Master | 200 | Administrative access |


## 🌐 Base URL
- **Local**: `http://localhost:8000` 

## 📡 API Endpoints

### Health & Status

#### API Information
**GET** `/`

Returns basic metadata and a list of available endpoints.


#### Health Check
**GET** `/health`

Returns API health status.

### Core CEVS Endpoints

All `/global/*` endpoints require a valid API key.

#### CEVS Composite Score

**GET** `/global/cevs/{company_name}`

Returns the **Composite Environmental Verification Score** by combining EPA, ISO, EEA, and EDGAR data. This is the primary endpoint of the API.

**Path Parameters:**
- `company_name` (required): The name of the company to score.

**Query Parameters:**
- `country` (optional): The company's primary country of operation for more accurate, localized analysis. 

**Example Request:**
```bash
curl -H "X-API-Key: demo_key_premium_2025" \
  "http://localhost:8000/global/cevs/Green%20Energy%20Co?country=US"
```

#### Global Emissions Data (EPA)
**GET** `/global/emissions`

Returns EPA power plant emissions data with filtering and pagination.

**Query Parameters:**
- `state` (optional): Filter by US state (e.g., "CA", "TX")
- `year` (optional): Filter by year (e.g., 2023) 
- `pollutant` (optional): Filter by pollutant type (e.g., "CO2", "NOx")
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Items per page (default: 50, max: 100)

**Example Request:**
```bash
curl -H "X-API-Key: demo_key_basic_2025" \
  "http://localhost:8000/global/emissions?state=CA&limit=5"
```
Response: @@ 123,11 @@ "data": [ { "facility_name": "Example Power Plant", "state": "CA",
 "year": 2023,
 "pollutant": "CO2",
 "emissions": 1500000.0,
 "unit": "tons", "raw_data_id": "FAC12345"
 } ], "pagination": { @@ 139,10 @@ }


#### Emissions Statistics
**GET** `/global/emissions/stats`

Returns aggregated emissions statistics from the cached EPA dataset.

**Response:**
```json 
@@ 156,76 @@

```

#### Power Plant Data (CAMPD) 
**GET** `/global/campd`

Exposes raw emissions and compliance data from the EPA's CAMPD API for a specific power plant facility.
 
**Query Parameters:**
- `facility_id` (integer, required): The facility ID from the EPA CAMPD system.

**Example Request:**
```bash
curl -H "X-API-Key: demo_key_premium_2025" \
  "http://localhost:8000/global/campd?facility_id=7"
```
#### ISO 14001 Certifications
**GET** `/global/iso`

### Returns ISO 14001 environmental certification data.

**Query Parameters:**

- `country` (optional): Filter by country (e.g., "Sweden", "USA", "DE")
- `limit` (optional): Maximum results (default: 100)

#### EEA Environmental Indicators 
**GET** `/global/eea`
Returns European Environment Agency data from Parquet sources.

**Query Parameters:**
- `country` (optional): Filter by country name
- `indicator` (optional): Indicator type ("GHG", "renewable", "pollution") 
- `year` (optional): Filter by year
- `limit` (optional): Maximum results (default: 50)

#### EDGAR Emissions Data  
**GET** `/global/edgar`

Returns EDGAR urban emissions data with trend analysis.

**Query Parameters:**
- `country` (required): Country name (normalized automatically)
- `pollutant` (optional): Pollutant type (default: "PM2.5")  
- `window` (optional): Trend analysis window in years (default: 3)

### Administrative Endpoints

All `/admin/*` endpoints require a **premium tier** API key.

#### List API Keys
**GET** `/admin/api-keys`

Lists all registered API keys.

#### Create API Key
**POST** `/admin/api-keys`

Creates a new API key.

#### API Usage Statistics
**GET** `/admin/stats`

Returns API usage statistics.

### Regional Data (Indonesia)
These endpoints provide access to Indonesian environmental permit data from KLHK Amdalnet and do not require an API key.
- `/permits`
- `/permits/search`
- `/permits/company/{company_name}`

### Technical Features
@@ 233,12 @@

The API automatically normalizes country names across all data sources for consistent data joining:
- **Input**: "USA", "United States", "US" → **Normalized**: "united_states"
- **Input**: "Deutschland", "Germany", "DE" → **Normalized**: "germany"
- **Input**: "Czech Republic", "Czechia", "CZ" → **Normalized**: "czech_republic"

**Supported variants**: 50+ countries with 267+ name variations including:
- Official names, common names, and abbreviations
- ISO codes (2-letter and 3-letter)
- Alternative spellings and regional variants

@@ 246,7 @@
- **EEA Client**: LRU cache for Parquet downloads (10 items)
- **ISO Client**: LRU cache for file operations (5-10 items)
- **EDGAR Client**: Global instance
- **Response caching**: 30s-5min depending on data freshness

### Error Handling
@@ 257,7 @@ "message": "API key required. Include it in Authorization header...", "code": "MISSING_API_KEY", "demo_keys": {

"basic": "demo_key_basic_2025",
"basic": "demo_key_basic_2025", "premium": "demo_key_premium_2025" } @@ 274,7 @@

### Data Errors:
json
{ 
  "status": "error", 
  "message": "Country 'XYZ' not found in dataset",
  "code": "DATA_NOT_FOUND"
}
@@ +284,10 @@

### Security Headers

The API includes security headers:
- `X-Content-Type-Options: nosniff` 
- `X-Frame-Options: DENY`

- **Issues**: Please open an issue on the project's GitHub repository.
- **Production Keys**: Contact the Envoyou administrator.