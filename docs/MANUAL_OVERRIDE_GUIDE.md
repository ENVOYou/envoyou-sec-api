# Manual Override Best Practices

## When to Use Manual Overrides

### Scenario 1: Third-Party Audit Data
**Situation:** You have more accurate data from energy audits
**Action:** Document the override reason in audit trail
**Example:** "Using certified energy audit data from [Auditor Name] dated [Date]"

### Scenario 2: Facility-Specific Factors
**Situation:** Your facility has unique characteristics
**Action:** Note the specific circumstances
**Example:** "Cogeneration facility - adjusted for steam export per EPA guidelines"

### Scenario 3: Timing Differences
**Situation:** Reporting period misalignment
**Action:** Explain the temporal adjustment
**Example:** "Adjusted for fiscal year vs calendar year reporting difference"

## Override Documentation Requirements

### Mandatory Fields
1. **Original Value:** System-calculated amount
2. **Override Value:** Your corrected amount
3. **Reason Code:** Category of override
4. **Detailed Explanation:** Minimum 50 characters
5. **Supporting Documentation:** Reference to source

### Audit Trail Impact
- All overrides are permanently recorded
- Original calculations remain visible
- Override rationale is included in SEC export
- Auditor can see complete decision history

## Current Implementation
**Note:** Manual overrides are currently handled through:
1. API calculation with notes field
2. Documentation in audit trail
3. Export includes both original and final values

**Future Enhancement:** Dedicated override interface (roadmap item)

## Contact for Override Support
For complex override scenarios, contact: support@envoyou.com
Response time: 24 hours for enterprise customers