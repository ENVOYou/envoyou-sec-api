# Postman Testing Guide

## Quick Test All Endpoints

1. **Import Collection**
   - Import `Envoyou-SEC-API.postman_collection.json` into Postman
   - Collection includes all MVP endpoints with sample data

2. **Environment Setup**
   - Base URL: `http://localhost:8000`
   - API Key: `demo_key`

3. **Test Sequence**
   ```
   1. Health Check ✅
   2. Emissions - Get Factors ✅
   3. Emissions - Get Units ✅
   4. Emissions - Calculate ✅
   5. Admin - Create Mapping ✅
   6. Validation - EPA Cross-Validate ✅
   7. Export - SEC CEVS (JSON) ✅
   8. Export - SEC Package ✅
   ```

## Expected Results

- **Health Check**: Status 200, healthy response
- **Factors/Units**: Status 200, emission factors data
- **Calculate**: Status 200, emissions calculation result
- **Validation**: Status 200, EPA validation with flags
- **Export**: Status 200, SEC-ready data formats
- **Admin**: Status 200, mapping CRUD operations

## Quick CLI Test

```bash
# Health check
curl http://localhost:8000/health

# Emissions calculation
curl -X POST http://localhost:8000/v1/emissions/calculate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo_key" \
  -d '{"company":"Demo Corp","scope1":{"fuel_type":"natural_gas","amount":1000,"unit":"mmbtu"},"scope2":{"kwh":500000,"grid_region":"US_default"}}'
```