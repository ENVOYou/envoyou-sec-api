"""
Confidence Analyzer Tool

Advanced confidence scoring and risk assessment for SEC compliance.
"""

from typing import Dict, Any, List, Optional
import math
from datetime import datetime


class ConfidenceAnalyzer:
    """Advanced confidence analysis for SEC emissions data."""
    
    def __init__(self):
        self.version = "1.0.0"
        self.scoring_weights = {
            "data_completeness": 0.25,
            "epa_validation": 0.30,
            "calculation_accuracy": 0.20,
            "source_reliability": 0.15,
            "temporal_consistency": 0.10
        }
    
    async def analyze_confidence(self, validation_result: Dict[str, Any], 
                               emissions_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive confidence analysis."""
        
        # Extract base confidence from validation
        base_confidence = validation_result.get("confidence_analysis", {})
        
        # Calculate enhanced confidence scores
        scores = {
            "data_completeness": self._score_data_completeness(emissions_data),
            "epa_validation": self._score_epa_validation(validation_result),
            "calculation_accuracy": self._score_calculation_accuracy(emissions_data),
            "source_reliability": self._score_source_reliability(validation_result),
            "temporal_consistency": self._score_temporal_consistency(emissions_data)
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            scores[dimension] * self.scoring_weights[dimension]
            for dimension in scores
        )
        
        # Risk assessment
        risk_assessment = self._assess_risk_factors(validation_result, emissions_data)
        
        # Confidence level and recommendations
        confidence_level, recommendations = self._determine_confidence_level(
            overall_score, scores, risk_assessment
        )
        
        return {
            "enhanced_score": round(overall_score, 2),
            "base_score": base_confidence.get("score", 0),
            "confidence_level": confidence_level,
            "dimension_scores": scores,
            "risk_assessment": risk_assessment,
            "recommendations": recommendations,
            "analysis_metadata": {
                "analyzer_version": self.version,
                "timestamp": datetime.utcnow().isoformat(),
                "scoring_weights": self.scoring_weights
            }
        }
    
    def _score_data_completeness(self, emissions_data: Dict[str, Any]) -> float:
        """Score data completeness (0-100)."""
        required_fields = ["company", "scope1", "scope2"]
        optional_fields = ["facility_info", "reporting_period", "methodology"]
        
        # Check required fields
        required_score = sum(
            100 if field in emissions_data and emissions_data[field] else 0
            for field in required_fields
        ) / len(required_fields)
        
        # Check optional fields (bonus points)
        optional_score = sum(
            20 if field in emissions_data and emissions_data[field] else 0
            for field in optional_fields
        ) / len(optional_fields)
        
        # Scope data completeness
        scope1_complete = self._check_scope_completeness(emissions_data.get("scope1", {}))
        scope2_complete = self._check_scope_completeness(emissions_data.get("scope2", {}))
        
        scope_score = (scope1_complete + scope2_complete) / 2
        
        return min(100, (required_score * 0.6 + scope_score * 0.3 + optional_score * 0.1))
    
    def _check_scope_completeness(self, scope_data: Dict[str, Any]) -> float:
        """Check completeness of scope data."""
        if not scope_data:
            return 0
        
        required_keys = ["amount", "unit"] if "fuel_type" in scope_data else ["kwh"]
        present_keys = sum(1 for key in required_keys if key in scope_data and scope_data[key])
        
        return (present_keys / len(required_keys)) * 100
    
    def _score_epa_validation(self, validation_result: Dict[str, Any]) -> float:
        """Score EPA validation quality (0-100)."""
        epa_data = validation_result.get("epa", {})
        flags = validation_result.get("flags", [])
        
        # Base score from matches
        matches_count = epa_data.get("matches_count", 0)
        match_score = min(100, matches_count * 20)  # 20 points per match, max 100
        
        # Penalty for flags
        flag_penalty = 0
        for flag in flags:
            severity = flag.get("severity", "low")
            penalties = {"critical": 40, "high": 25, "medium": 15, "low": 5}
            flag_penalty += penalties.get(severity, 5)
        
        # Quantitative validation bonus
        quantitative_bonus = 0
        if validation_result.get("quantitative_deviation"):
            deviations = validation_result["quantitative_deviation"].get("deviations", [])
            low_deviation_count = sum(1 for dev in deviations if dev.get("deviation_pct", 100) < 10)
            quantitative_bonus = low_deviation_count * 10
        
        return max(0, min(100, match_score - flag_penalty + quantitative_bonus))
    
    def _score_calculation_accuracy(self, emissions_data: Dict[str, Any]) -> float:
        """Score calculation accuracy and methodology (0-100)."""
        score = 70  # Base score for using standard methodology
        
        # Check for emission factors source
        if "emission_factors_source" in emissions_data:
            score += 15
        
        # Check for calculation version/methodology
        if "calculation_version" in emissions_data or "methodology" in emissions_data:
            score += 10
        
        # Check for uncertainty estimates
        if "uncertainty" in emissions_data:
            score += 5
        
        return min(100, score)
    
    def _score_source_reliability(self, validation_result: Dict[str, Any]) -> float:
        """Score data source reliability (0-100)."""
        score = 60  # Base score
        
        # EPA data availability
        epa_matches = validation_result.get("epa", {}).get("matches_count", 0)
        if epa_matches > 0:
            score += 20
        
        # Mapping availability
        if validation_result.get("mapping"):
            score += 15
        
        # Third-party validation
        if validation_result.get("quantitative_deviation"):
            score += 5
        
        return min(100, score)
    
    def _score_temporal_consistency(self, emissions_data: Dict[str, Any]) -> float:
        """Score temporal consistency and recency (0-100)."""
        score = 80  # Base score assuming current year data
        
        # Check for reporting period
        if "reporting_period" in emissions_data:
            score += 10
        
        # Check for data collection date
        if "data_collection_date" in emissions_data:
            score += 10
        
        return min(100, score)
    
    def _assess_risk_factors(self, validation_result: Dict[str, Any], 
                           emissions_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk factors for SEC filing."""
        risks = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": []
        }
        
        # Check for critical flags
        flags = validation_result.get("flags", [])
        critical_flags = [f for f in flags if f.get("severity") == "critical"]
        high_flags = [f for f in flags if f.get("severity") == "high"]
        
        if critical_flags:
            risks["high_risk"].append({
                "factor": "critical_validation_flags",
                "description": f"{len(critical_flags)} critical validation issues detected",
                "impact": "May prevent SEC filing approval"
            })
        
        if high_flags:
            risks["medium_risk"].append({
                "factor": "high_severity_flags",
                "description": f"{len(high_flags)} high-severity validation issues",
                "impact": "May require additional documentation"
            })
        
        # Check for quantitative deviations
        if validation_result.get("quantitative_deviation"):
            deviations = validation_result["quantitative_deviation"].get("deviations", [])
            high_deviations = [d for d in deviations if d.get("deviation_pct", 0) > 25]
            
            if high_deviations:
                risks["medium_risk"].append({
                    "factor": "quantitative_deviations",
                    "description": f"{len(high_deviations)} significant quantitative deviations",
                    "impact": "May require explanation in SEC filing"
                })
        
        # No EPA matches
        if validation_result.get("epa", {}).get("matches_count", 0) == 0:
            risks["medium_risk"].append({
                "factor": "no_epa_matches",
                "description": "No EPA facility matches found",
                "impact": "May require additional verification"
            })
        
        return risks
    
    def _determine_confidence_level(self, overall_score: float, 
                                  dimension_scores: Dict[str, float],
                                  risk_assessment: Dict[str, Any]) -> tuple:
        """Determine confidence level and generate recommendations."""
        
        high_risks = len(risk_assessment.get("high_risk", []))
        medium_risks = len(risk_assessment.get("medium_risk", []))
        
        # Determine level
        if overall_score >= 85 and high_risks == 0:
            level = "very_high"
            base_recommendation = "Excellent confidence - ready for SEC filing"
        elif overall_score >= 75 and high_risks == 0:
            level = "high"
            base_recommendation = "High confidence - ready for SEC filing with minor review"
        elif overall_score >= 60 and high_risks <= 1:
            level = "medium"
            base_recommendation = "Medium confidence - review recommended before filing"
        else:
            level = "low"
            base_recommendation = "Low confidence - significant improvements required"
        
        # Generate specific recommendations
        recommendations = [base_recommendation]
        
        # Dimension-specific recommendations
        for dimension, score in dimension_scores.items():
            if score < 60:
                recommendations.append(f"Improve {dimension.replace('_', ' ')}: {score:.1f}/100")
        
        # Risk-based recommendations
        if high_risks > 0:
            recommendations.append(f"Address {high_risks} high-risk factors before filing")
        
        if medium_risks > 2:
            recommendations.append(f"Review {medium_risks} medium-risk factors")
        
        return level, recommendations