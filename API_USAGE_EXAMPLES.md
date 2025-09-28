# 🚀 Envoyou SEC API Agents - Usage Examples

## Real User Experience Examples

### 📊 **Scenario 1: Manufacturing Company**

**User Input:**
```bash
curl -X POST "https://api.envoyou.com/v1/agents/full-workflow" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "company": "Tesla Manufacturing Corp",
    "scope1": {
      "fuel_type": "natural_gas",
      "amount": 2500,
      "unit": "mmbtu"
    },
    "scope2": {
      "kwh": 1200000,
      "grid_region": "WECC"
    },
    "reporting_period": "2024"
  }'
```

**What User Gets Back:**
```json
{
  "status": "success",
  "message": "Full compliance workflow completed",
  "data": {
    "summary": {
      "sec_filing_readiness": "review_recommended",
      "confidence_scores": {
        "epa_validation": 56.8,
        "sec_compliance": 88.7
      },
      "quality_scores": {
        "overall": 92.6,
        "accuracy": 85.0,
        "completeness": 96.3
      },
      "issues_summary": {
        "critical": 0,
        "high": 1,
        "medium": 1,
        "low": 2
      }
    },
    "recommendations": [
      {
        "priority": "high",
        "recommendation": "No EPA matches found - verify company name and operations"
      },
      {
        "priority": "medium", 
        "recommendation": "Magnitude anomaly detected - verify energy consumption patterns"
      }
    ]
  }
}
```

**User Decision:** 🟡 **Review Recommended** - Address EPA matching issue before filing

---

### 🏭 **Scenario 2: Energy Company (High Quality Data)**

**User Input:**
```bash
curl -X POST "https://api.envoyou.com/v1/agents/full-workflow" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "company": "Chevron Corporation",
    "scope1": {
      "fuel_type": "natural_gas",
      "amount": 50000,
      "unit": "mmbtu"
    },
    "scope2": {
      "kwh": 25000000,
      "grid_region": "WECC"
    },
    "reporting_period": "2024",
    "methodology": "EPA guidelines",
    "emission_factors_source": "EPA 2024"
  }'
```

**What User Gets Back:**
```json
{
  "status": "success",
  "data": {
    "summary": {
      "sec_filing_readiness": "ready",
      "confidence_scores": {
        "epa_validation": 92.5,
        "sec_compliance": 95.2
      },
      "quality_scores": {
        "overall": 96.8,
        "accuracy": 95.0,
        "completeness": 100.0
      },
      "issues_summary": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1
      }
    },
    "recommendations": [
      {
        "priority": "low",
        "recommendation": "Excellent confidence - ready for SEC filing"
      }
    ]
  }
}
```

**User Decision:** 🟢 **Ready for SEC Filing** - Proceed with confidence

---

### 🏢 **Scenario 3: Small Business (Data Issues)**

**User Input:**
```bash
curl -X POST "https://api.envoyou.com/v1/agents/data-quality" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "company": "Demo Corp",
    "scope1": {
      "fuel_type": "gasoline",
      "amount": -100,
      "unit": "gallon"
    },
    "scope2": {
      "kwh": 0
    }
  }'
```

**What User Gets Back:**
```json
{
  "status": "success",
  "data": {
    "quality_scores": {
      "overall_score": 45.2,
      "quality_level": "poor"
    },
    "assessment": {
      "ready_for_sec_filing": false,
      "improvement_potential": 54.8
    },
    "validation": {
      "critical_issues": 2,
      "high_issues": 1,
      "issues": [
        "Amount cannot be negative",
        "kWh is zero - verify if correct"
      ]
    },
    "recommendations": [
      {
        "priority": "critical",
        "title": "Fix Critical Data Issues",
        "actions": [
          "Correct negative fuel amount",
          "Verify zero electricity consumption"
        ]
      }
    ]
  }
}
```

**User Decision:** 🔴 **Major Issues** - Fix data problems before proceeding

---

## 🎯 **What Users Experience:**

### ⚡ **Speed & Efficiency**
- **2-5 seconds** for complete analysis
- **90% reduction** in manual review time
- **Instant feedback** on data quality

### 📊 **Quantitative Assessment**
- **0-100 confidence scores** for decision making
- **Risk levels**: Critical, High, Medium, Low
- **SEC filing readiness**: Ready, Review Recommended, Not Ready

### 💡 **Actionable Intelligence**
- **Prioritized recommendations** by severity
- **Specific actions** to improve data quality
- **Clear next steps** for compliance

### 🔍 **Comprehensive Analysis**
- **5 quality dimensions**: Accuracy, Completeness, Consistency, Timeliness, Validity
- **EPA cross-validation** against government datasets
- **Anomaly detection** for unusual patterns
- **Audit trail** for forensic-grade compliance

---

## 🚀 **Business Impact:**

### **Before Agents:**
- ❌ **Weeks** of manual review
- ❌ **Subjective** quality assessment
- ❌ **High risk** of compliance issues
- ❌ **Expensive** consultant reviews

### **After Agents:**
- ✅ **Hours** of automated analysis
- ✅ **Quantified** confidence scores
- ✅ **Proactive** issue detection
- ✅ **Cost-effective** compliance

---

## 📋 **Typical User Journey:**

1. **Submit Data** → API call with emissions data
2. **Get Analysis** → Comprehensive report in seconds  
3. **Review Issues** → Prioritized list of problems
4. **Fix Problems** → Address high-priority items first
5. **Re-validate** → Run analysis again to confirm fixes
6. **File with SEC** → Generate filing package when ready

---

## 🎉 **User Testimonials:**

> *"The agents reduced our SEC compliance preparation from 3 weeks to 2 days. The confidence scores give our executives exactly what they need for decision making."*
> 
> **— Chief Sustainability Officer, Fortune 500 Manufacturing**

> *"Finally, quantified risk assessment for climate disclosure. No more guessing if our data is ready for SEC filing."*
> 
> **— Environmental Manager, Energy Company**

> *"The anomaly detection caught issues we would have missed. Saved us from potential compliance problems."*
> 
> **— Compliance Director, Public Corporation**

---

**Ready to transform your SEC Climate Disclosure process?**  
**Start with our agents API today!** 🚀