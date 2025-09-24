# SEC Export — Sample Outputs

Contoh output untuk membantu CFO/Legal memahami format hasil tanpa perlu coding.

## CEVS (JSON)

```json
{
  "company": "Example Corp",
  "country": "US",
  "summary": {
    "score": 72.5,
    "components": {
      "base": 50,
      "iso_bonus": 20,
      "epa_penalty": -5,
      "renewables_bonus": 8,
      "pollution_penalty": -2,
      "campd_penalty": -0
    }
  },
  "data_sources": {
    "epa_matches": 2,
    "renewables_source": "EEA Parquet API",
    "pollution_source": "EEA Parquet API"
  },
  "technical_notes": {
    "methodology": "Composite score based on ISO presence, EPA matches, renewables proxy, pollution trends, and CAMPD penalties.",
    "version": "v0.1.0"
  }
}
```

## AuditTrail (CSV)

```csv
id,timestamp,company_cik,source_file,calculation_version,s3_path,gcs_path,notes
8ff2a1...,2025-09-24T01:23:45Z,0000123456,cevs_aggregator,0.1,,,components={...}
```

Catatan:

- Field dapat bertambah mengikuti kebutuhan auditor (mis. faktor emisi rinci).
- Format CSV disesuaikan untuk impor cepat ke spreadsheet/BI tools.
