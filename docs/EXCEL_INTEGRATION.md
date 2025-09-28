# Excel Integration Guide

## Pre-Formatted Exports

### SEC Filing Template
**Download:** `/v1/export/sec/excel-template`
**Format:** Ready-to-use Excel file with:
- Pre-built pivot tables
- SEC-compliant formatting
- Audit trail summary
- Deviation highlights

### CSV Export Structure
**Optimized for Excel import:**
```csv
Company,Scope,Fuel_Type,Amount,Unit,CO2e_Emissions,EPA_Comparison,Confidence,Notes
Demo Corp,Scope 1,Natural Gas,1000,MMBTU,53.02,Within Range,High,EPA Factor 2024
Demo Corp,Scope 2,Electricity,500000,kWh,250.5,15% Above Average,Medium,Grid Region RFC
```

### Pivot Table Ready
**Pre-configured columns for:**
- Scope 1 vs Scope 2 analysis
- Fuel type breakdown
- Monthly/quarterly trends
- Deviation analysis

## Excel Formulas Included
**Automatic calculations for:**
- Total emissions by scope
- Percentage breakdowns
- Deviation percentages
- Confidence scoring

## Import Instructions
1. Download CSV from `/v1/export/sec/cevs?format=excel`
2. Open in Excel
3. Data → Text to Columns (if needed)
4. Use pre-built pivot table templates

## Enterprise Integration Roadmap
**Future enhancements:**
- Direct Excel plugin (Q3 2025)
- Power BI connector (Q4 2025)
- Tableau integration (2026)

**Current workaround:** CSV export + Excel templates