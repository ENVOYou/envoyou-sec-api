# E2E Demo — Envoyou SEC API

Complete end-to-end demonstration of the Envoyou SEC API workflow: input → calculate → validate → export.

## Prerequisites

- API running on `http://localhost:8000`
- Valid API key (set in environment)
- Admin access for mapping endpoints

## Step 1: Calculate Emissions

Calculate Scope 1 & 2 emissions for a company:

```bash
curl -X POST "http://localhost:8000/v1/emissions/calculate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "company": "Demo Energy Corp",
    "scope1": {
      "fuel_type": "natural_gas",
      "amount": 1000.0,
      "unit": "mmbtu"
    },
    "scope2": {
      "kwh": 500000.0,
      "grid_region": "RFC"
    }
  }'
```

**Expected Response:**

```json
{
  "status": "success",
  "result": {
    "version": "0.1",
    "company": "Demo Energy Corp",
    "components": {
      "scope1": {
        "fuel_type": "natural_gas",
        "unit": "mmbtu",
        "amount": 1000.0,
        "factor": 53.06,
        "emissions_kg": 53060.0
      },
      "scope2": {
        "region": "RFC",
        "kwh": 500000.0,
        "factor": 0.45,
        "emissions_kg": 225000.0
      }
    },
    "totals": {
      "emissions_kg": 278060.0,
      "emissions_tonnes": 278.06
    }
  },
  "audit_trail_id": "audit_123456"
}
```

## Step 2: Create Company Mapping (Admin)

Map the company to a specific facility for enhanced validation:

```bash
curl -X POST "http://localhost:8000/v1/admin/mappings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-supabase-jwt" \
  -d '{
    "company": "Demo Energy Corp",
    "facility_id": "12345",
    "facility_name": "Demo Power Plant",
    "state": "TX",
    "notes": "Primary generation facility"
  }'
```

**Expected Response:**

```json
{
  "status": "success",
  "mapping": {
    "company": "Demo Energy Corp",
    "facility_id": "12345",
    "facility_name": "Demo Power Plant",
    "state": "TX",
    "notes": "Primary generation facility",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
}
```

## Step 3: Cross-Validate with EPA

Validate calculated emissions against EPA data:

```bash
curl -X POST "http://localhost:8000/v1/validation/epa?state=TX&year=2023" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "company": "Demo Energy Corp",
    "scope1": {
      "fuel_type": "natural_gas",
      "amount": 1000.0,
      "unit": "mmbtu"
    },
    "scope2": {
      "kwh": 500000.0,
      "grid_region": "RFC"
    }
  }'
```

**Expected Response:**

```json
{
  "status": "success",
  "company": "Demo Energy Corp",
  "inputs": {
    "scope1": {
      "fuel_type": "natural_gas",
      "amount": 1000.0,
      "unit": "mmbtu"
    },
    "scope2": {
      "kwh": 500000.0,
      "grid_region": "RFC"
    }
  },
  "calc": {
    "totals": {
      "emissions_kg": 278060.0,
      "emissions_tonnes": 278.06
    }
  },
  "epa": {
    "state": "TX",
    "matches_count": 2,
    "sample": [
      {
        "facility_name": "Demo Energy Corp Plant 1",
        "state": "TX",
        "city": "Houston"
      }
    ]
  },
  "mapping": {
    "facility_id": "12345",
    "facility_name": "Demo Power Plant",
    "state": "TX",
    "notes": "Primary generation facility"
  },
  "quantitative_deviation": {
    "facility_id": "12345",
    "year": 2023,
    "deviations": [
      {
        "pollutant": "CO2",
        "reported": 278.06,
        "reference": 265.0,
        "deviation_pct": 4.9,
        "threshold": 15.0,
        "severity": "medium",
        "source": "CAMPD"
      }
    ],
    "thresholds": {
      "co2": 15.0,
      "nox": 20.0,
      "so2": 25.0
    }
  },
  "flags": [],
  "metrics": {
    "min_matches": 1,
    "low_density_threshold": 3,
    "require_state_match": false
  },
  "notes": "EPA TRI tidak memuat angka emisi; heuristik ini memeriksa keberadaan & kepadatan kecocokan.",
  "suggestions": []
}
```

## Step 4: Export SEC Package

Generate a complete SEC filing package:

```bash
curl -X POST "http://localhost:8000/v1/export/sec/package" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "company": "Demo Energy Corp",
    "scope1": {
      "fuel_type": "natural_gas",
      "amount": 1000.0,
      "unit": "mmbtu"
    },
    "scope2": {
      "kwh": 500000.0,
      "grid_region": "RFC"
    },
    "include_validation": true,
    "include_audit": true
  }'
```

**Expected Response:**

```json
{
  "status": "success",
  "package": {
    "company": "Demo Energy Corp",
    "filename": "demo_energy_corp_sec_package_20250115_103000.zip",
    "url": "http://localhost:8000/uploads/exports/demo_energy_corp_sec_package_20250115_103000.zip",
    "size_bytes": 15420,
    "files": [
      "validation.json",
      "audit.csv",
      "cevs.json",
      "summary.txt",
      "README.txt"
    ],
    "created_at": "2025-01-15T10:30:00Z"
  },
  "audit_trail_id": "audit_789012"
}
```

## Step 5: Download and Inspect Package

Download the generated package:

```bash
curl -O "http://localhost:8000/uploads/exports/demo_energy_corp_sec_package_20250115_103000.zip"
```

Extract and inspect contents:

```bash
unzip demo_energy_corp_sec_package_20250115_103000.zip
ls -la
```

**Package Contents:**

### validation.json

```json
{
  "company": "Demo Energy Corp",
  "validation_date": "2025-01-15T10:30:00Z",
  "epa_matches": 2,
  "quantitative_deviations": [
    {
      "pollutant": "CO2",
      "reported_tonnes": 278.06,
      "reference_tonnes": 265.0,
      "deviation_percent": 4.9,
      "severity": "medium",
      "source": "CAMPD"
    }
  ],
  "flags": [],
  "validation_status": "passed"
}
```

### audit.csv

```csv
timestamp,company,action,inputs,outputs,factors_version,notes
2025-01-15T10:25:00Z,Demo Energy Corp,calculate_emissions,"{""scope1"":{""fuel_type"":""natural_gas"",""amount"":1000.0,""unit"":""mmbtu""},""scope2"":{""kwh"":500000.0,""grid_region"":""RFC""}}","{""emissions_kg"":278060.0,""emissions_tonnes"":278.06}",0.1,Automatic calculation
2025-01-15T10:30:00Z,Demo Energy Corp,export_package,"{""include_validation"":true,""include_audit"":true}","{""filename"":""demo_energy_corp_sec_package_20250115_103000.zip"",""size_bytes"":15420}",0.1,SEC package export
```

### cevs.json

```json
{
  "company": "Demo Energy Corp",
  "reporting_period": "2023",
  "scope1_emissions_tonnes": 53.06,
  "scope2_emissions_tonnes": 225.0,
  "total_emissions_tonnes": 278.06,
  "calculation_methodology": "EPA emission factors v0.1",
  "verification_status": "cross-validated",
  "data_sources": ["EPA", "CAMPD"],
  "last_updated": "2025-01-15T10:30:00Z"
}
```

### summary.txt

```txt

ENVOYOU SEC CLIMATE DISCLOSURE SUMMARY
=====================================

Company: Demo Energy Corp
Report Date: 2025-01-15
Reporting Period: 2023

EMISSIONS SUMMARY
-----------------
Scope 1 (Direct): 53.06 tonnes CO2e
Scope 2 (Indirect): 225.00 tonnes CO2e
Total: 278.06 tonnes CO2e

VALIDATION RESULTS
------------------
EPA Facility Matches: 2
Quantitative Validation: PASSED (4.9% deviation)
Data Quality Flags: None

AUDIT TRAIL
-----------
All calculations and validations are recorded with timestamps,
input parameters, and data sources for SEC compliance and
third-party verification.

For detailed audit records, see audit.csv
For validation details, see validation.json
For structured data, see cevs.json
```

## Step 6: Audit Trail Access (Admin)

Access detailed audit records:

```bash
curl "http://localhost:8000/v1/audit?company=Demo%20Energy%20Corp&limit=10" \
  -H "Authorization: Bearer your-supabase-jwt"
```

**Expected Response:**

```json
{
  "status": "success",
  "audit_records": [
    {
      "id": "audit_123456",
      "timestamp": "2025-01-15T10:25:00Z",
      "company": "Demo Energy Corp",
      "action": "calculate_emissions",
      "inputs": {
        "scope1": {
          "fuel_type": "natural_gas",
          "amount": 1000.0,
          "unit": "mmbtu"
        },
        "scope2": {
          "kwh": 500000.0,
          "grid_region": "RFC"
        }
      },
      "outputs": {
        "emissions_kg": 278060.0,
        "emissions_tonnes": 278.06
      },
      "factors_version": "0.1",
      "notes": "Automatic calculation"
    }
  ],
  "total_count": 3,
  "page": 1,
  "limit": 10
}
```

## Complete Workflow Summary

1. **Calculate** emissions using standardized factors
2. **Map** company to facility for enhanced validation
3. **Validate** against EPA/CAMPD data sources
4. **Export** SEC-ready package with all supporting data
5. **Audit** complete traceability for compliance

This workflow provides forensic-grade traceability and automated cross-validation required for SEC Climate Disclosure compliance.

## Error Handling Examples

### Invalid API Key

```bash
curl -X POST "http://localhost:8000/v1/emissions/calculate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: invalid-key" \
  -d '{"company": "Test"}'
```

**Response:**

```json
{
  "detail": "Invalid API key"
}
```

### Missing Required Fields

```bash
curl -X POST "http://localhost:8000/v1/emissions/calculate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "scope1": {
      "fuel_type": "natural_gas",
      "amount": 1000.0,
      "unit": "mmbtu"
    }
  }'
```

**Response:**

```json
{
  "detail": "company is required"
}
```

### Unsupported Fuel Type

```bash
curl -X POST "http://localhost:8000/v1/emissions/calculate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "company": "Test Corp",
    "scope1": {
      "fuel_type": "coal",
      "amount": 1000.0,
      "unit": "tons"
    }
  }'
```

**Response:**

```json
{
  "detail": "Unsupported fuel/unit: coal/tons"
}
```
