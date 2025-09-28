# SEC Filing Workflow Guide

## From Zero to Filing-Ready in 5 Steps

### Step 1: Input Company Data
**What you provide:**
- Company name
- Scope 1 data (fuel consumption)
- Scope 2 data (electricity usage)

**API Call:**
```bash
POST /v1/emissions/calculate
{
  "company": "Your Company",
  "scope1": {"fuel_type": "natural_gas", "amount": 1000, "unit": "mmbtu"},
  "scope2": {"kwh": 500000, "grid_region": "RFC"}
}
```

### Step 2: Automatic EPA Cross-Validation
**What happens:**
- System compares your data against EPA databases
- Flags deviations >10% for review
- Provides confidence scores

**API Call:**
```bash
POST /v1/validation/epa
# Same payload as Step 1
```

### Step 3: Review Calculations & Deviations
**What you get:**
- Clear deviation indicators
- Confidence scores (High/Medium/Low)
- Recommended actions

**Response Example:**
```json
{
  "deviation_percentage": 15.2,
  "confidence_score": "medium",
  "recommendation": "Review fuel consumption data - 15% higher than EPA average"
}
```

### Step 4: Generate Audit Trail
**What's created:**
- Immutable calculation record
- Source data references
- Timestamp and methodology

**Automatic with every calculation**

### Step 5: Export SEC Package
**What you download:**
- JSON data for 10-K filing
- CSV for spreadsheet analysis
- Audit trail documentation

**API Call:**
```bash
POST /v1/export/sec/package
# Returns downloadable ZIP file
```

## Time Savings
- **Traditional Process**: 2-3 weeks
- **With Envoyou**: 2-3 hours
- **Audit Preparation**: Built-in, no additional work

## Risk Mitigation
- ✅ Forensic-grade audit trail
- ✅ EPA cross-validation
- ✅ Deviation flagging
- ✅ Source documentation