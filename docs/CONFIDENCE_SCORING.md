# Confidence Scoring Implementation

## Overview

Confidence scoring provides CSOs with quantitative assessment of data reliability for SEC filing purposes. This addresses the key feedback about needing "confidence scores" rather than just binary pass/fail validation.

## Implementation

### Emissions Calculation Confidence

**Base Score:** 85 points
**Adjustments:**
- Complete Scope 1 & 2 data: +10 points
- Missing all data: -50 points
- Very large emissions (>100k tonnes): -10 points
- Very small emissions (<1 tonne): -5 points

**Levels:**
- **High (80-100):** "Complete Scope 1 & 2 data - ready for SEC filing"
- **Medium (60-79):** "Partial data - consider EPA validation"
- **Low (0-59):** "No emission data provided"

### EPA Validation Confidence

**Base Score:** 100 points
**Flag Penalties:**
- Critical flags: -40 points
- High flags: -25 points
- Medium flags: -15 points
- Low flags: -5 points

**Match Bonuses:**
- 5+ EPA matches: +10 points
- 3-4 EPA matches: +5 points

**Quantitative Deviation Penalties:**
- >50% deviation: -30 points
- >25% deviation: -20 points
- >10% deviation: -10 points

**Levels:**
- **High (80-100):** "Data appears reliable for SEC filing"
- **Medium (60-79):** "Review recommended before SEC filing"
- **Low (0-59):** "Manual verification required before SEC filing"

## API Response Format

### Emissions Calculation
```json
{
  "confidence_analysis": {
    "score": 95,
    "level": "high",
    "recommendation": "Complete Scope 1 & 2 data - ready for SEC filing"
  }
}
```

### EPA Validation
```json
{
  "validation": {
    "confidence_score": 75,
    "confidence_level": "medium",
    "recommendation": "Review recommended before SEC filing",
    "matches_found": 2,
    "flags_count": 1
  },
  "confidence_analysis": {
    "score": 75,
    "level": "medium",
    "recommendation": "Review recommended before SEC filing"
  }
}
```

## Business Value

### For CSOs
- **Quantified Risk Assessment:** Clear numerical scores instead of subjective judgments
- **Actionable Recommendations:** Specific guidance on next steps
- **Audit Preparation:** Confidence levels help prioritize review efforts
- **SEC Compliance:** Built-in assessment of filing readiness

### For Auditors
- **Transparent Methodology:** Clear scoring criteria
- **Risk Prioritization:** Focus on low-confidence calculations
- **Documentation Trail:** Confidence scores included in audit trail

## Configuration

Confidence scoring thresholds can be adjusted via environment variables:
- `CONFIDENCE_HIGH_THRESHOLD` (default: 80)
- `CONFIDENCE_MEDIUM_THRESHOLD` (default: 60)
- `VALIDATION_CO2_DEVIATION_THRESHOLD` (default: 15.0)

## Future Enhancements

### Phase 2 (Q2 2025)
- Industry-specific confidence baselines
- Historical confidence trending
- Peer comparison confidence metrics

### Phase 3 (Q3 2025)
- Machine learning confidence prediction
- Automated confidence improvement suggestions
- Integration with external audit systems

## Testing

Run confidence scoring tests:
```bash
python3 test_confidence_scoring.py
```

## Implementation Files

- `app/services/validation_service.py` - Core confidence calculation
- `app/routes/validation.py` - EPA validation endpoint
- `app/routes/emissions.py` - Emissions calculation endpoint
- `test_confidence_scoring.py` - Test suite