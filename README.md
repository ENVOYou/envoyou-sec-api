# Envoyou SEC API

[Dokumen Tujuan & Fitur Kunci (Internal)](docs/GOALS.md)

Dokumen pendukung:

- [Metrics of Success (MVP)](docs/METRICS.md)
- [SEC Export — Sample Outputs](docs/SEC_EXPORT_SAMPLES.md)
- [Security Plan (Early Commitment)](docs/SECURITY_PLAN.md)
- [Partnering Strategy (Anchor Partners)](docs/PARTNERING.md)
- [Admin Mapping (Company → Facility)](docs/ADMIN_MAPPING.md)

## API Endpoints

### Core Endpoints
- POST `/v1/emissions/calculate` — calculate Scope 1 & 2 emissions with audit trail
- POST `/v1/validation/epa` — cross-validate against EPA data with quantitative deviation
- POST `/v1/export/sec/package` — generate complete SEC filing package (zip)

### Export Endpoints
- GET `/v1/export/sec/cevs` — export CEVS data (JSON/CSV)
- GET `/v1/export/sec/audit` — export audit trail (CSV)

### Admin Endpoints (Premium)
- POST `/v1/admin/mappings` — create/update company-facility mapping
- GET `/v1/admin/mappings/{company}` — get mapping details
- GET `/v1/admin/mappings` — list all mappings
- POST `/v1/audit` — create audit entry
- GET `/v1/audit` — list audit entries with filters

Envoyou SEC API is a focused backend service for SEC Climate Disclosure compliance. It provides auditable greenhouse gas (GHG) calculation, validation, and report export features tailored for public companies required to submit climate disclosures.

## Key goals

- Single-purpose MVP: calculate Scope 1 and Scope 2 emissions, produce auditable calculation records, and export SEC-ready reporting tables.
- Forensic-grade traceability: every calculation stores inputs, emission factors, and sources in an AuditTrail.
- Cross-validation: automatic comparison against public EPA datasets to flag significant discrepancies.

## Core components

- Emissions calculation engine (Scope 1 & 2)
- AuditTrail model and repository (stores inputs, factors, source URLs, timestamps)
- Validation service that compares reported results with EPA data
- Exporter for SEC filing formats (10-K friendly tables and notes)

## Getting started (development)

1. Copy environment template:

   ```bash
   cp .env.example .env
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run database migrations (local / staging only):

   ```bash
   # set TEST_DATABASE_URL or DATABASE_URL in env before running
   alembic upgrade head
   ```

4. Start server (development):

   ```bash
   uvicorn app.api_server:app --reload --port 8000
   ```

## Quick Example

Calculate emissions and generate SEC package:

```bash
# 1. Calculate emissions
curl -X POST "http://localhost:8000/v1/emissions/calculate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "company": "Demo Corp",
    "scope1": {"fuel_type": "natural_gas", "amount": 1000, "unit": "mmbtu"},
    "scope2": {"kwh": 500000, "grid_region": "RFC"}
  }'

# 2. Validate against EPA
curl -X POST "http://localhost:8000/v1/validation/epa" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "company": "Demo Corp",
    "scope1": {"fuel_type": "natural_gas", "amount": 1000, "unit": "mmbtu"},
    "scope2": {"kwh": 500000, "grid_region": "RFC"}
  }'

# 3. Generate SEC package
curl -X POST "http://localhost:8000/v1/export/sec/package" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "company": "Demo Corp",
    "scope1": {"fuel_type": "natural_gas", "amount": 1000, "unit": "mmbtu"},
    "scope2": {"kwh": 500000, "grid_region": "RFC"}
  }'
```

See [E2E Demo](docs/E2E_DEMO.md) for complete workflow examples.

## Tests

- Use `TEST_DATABASE_URL` to ensure tests do not touch production DB.

   ```bash
   export TEST_DATABASE_URL="sqlite:///./test.db"
   pytest -q
   ```

## Notes on production

- Do NOT commit production secrets. Store `DATABASE_URL` and other credentials in your deployment secrets manager.
- Always backup production DB before running migrations.

## Project status

- This repository is being re-focused from the original permit-API fork to a dedicated Envoyou SEC compliance API. Historical permit-API code is archived in `archive/permit-api` branch.

## Maintainer

- Husni Kusuma — [@hk-dev13](https://github.com/hk-dev13)
