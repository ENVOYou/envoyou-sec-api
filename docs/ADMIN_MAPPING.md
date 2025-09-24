# Admin — Company → Facility Mapping

Manual mapping to link a company (CIK/name) with an EPA facility ID for improved validation and reporting.

## Endpoints (requires premium API key)

Base prefix: `/v1/admin`

- POST `/mappings`
  - Body:
    {
      "company": "DemoCo",
      "facility_id": "PLT1001",
      "facility_name": "Demo Plant",
      "state": "TX",
      "notes": "manual mapping"
    }
  - Upsert (create or update) mapping for company.

- GET `/mappings/{company}`
  - Return mapping details for a company.

- GET `/mappings?limit=100&offset=0`
  - List mappings.

## Example (curl)

```bash
API_KEY=demo_key_premium_2025
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "company": "DemoCo",
    "facility_id": "PLT1001",
    "facility_name": "Demo Plant",
    "state": "TX",
    "notes": "manual mapping"
  }' \
  http://localhost:8000/v1/admin/mappings | jq .
```

## Notes

- Use this mapping to refine validation and reporting.
- This model can be extended later (effective dates, multiple facilities per company, etc.).
