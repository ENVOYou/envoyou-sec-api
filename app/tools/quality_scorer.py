"""
Quality Scorer Tool

Multi-dimensional data quality scoring system.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import statistics


class QualityScorer:
    """Multi-dimensional data quality scoring for emissions data."""
    
    def __init__(self):
        self.version = "1.0.0"
        self.dimensions = {
            "accuracy": 0.25,
            "completeness": 0.25,
            "consistency": 0.20,
            "timeliness": 0.15,
            "validity": 0.15
        }
    
    async def score_data_quality(self, data: Dict[str, Any], 
                               validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Score data quality across multiple dimensions."""
        
        scores = {
            "accuracy": self._score_accuracy(data, validation_result),
            "completeness": self._score_completeness(data, validation_result),
            "consistency": self._score_consistency(data),
            "timeliness": self._score_timeliness(data),
            "validity": self._score_validity(data, validation_result)
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            scores[dimension] * weight 
            for dimension, weight in self.dimensions.items()
        )
        
        # Quality assessment
        quality_level = self._determine_quality_level(overall_score, scores)
        
        return {
            "overall_score": round(overall_score, 2),
            "quality_level": quality_level,
            "dimension_scores": scores,
            "dimension_weights": self.dimensions,
            "assessment": self._create_quality_assessment(scores, overall_score),
            "recommendations": self._generate_quality_recommendations(scores)
        }
    
    def _score_accuracy(self, data: Dict[str, Any], 
                       validation_result: Dict[str, Any]) -> float:
        """Score data accuracy (0-100)."""
        base_score = 80  # Base accuracy assumption
        
        # Deduct for validation issues
        critical_issues = validation_result.get("critical_issues", 0)
        high_issues = validation_result.get("high_issues", 0)
        medium_issues = validation_result.get("medium_issues", 0)
        
        accuracy_penalty = (critical_issues * 20 + high_issues * 10 + medium_issues * 5)
        
        # Bonus for data source quality indicators
        accuracy_bonus = 0
        
        # Check for emission factors source
        if data.get("emission_factors_source"):
            if "epa" in data["emission_factors_source"].lower():
                accuracy_bonus += 10
            elif "official" in data["emission_factors_source"].lower():
                accuracy_bonus += 5
        
        # Check for calculation methodology
        if data.get("methodology"):
            accuracy_bonus += 5
        
        # Check for uncertainty estimates
        if data.get("uncertainty"):
            accuracy_bonus += 5
        
        final_score = base_score - accuracy_penalty + accuracy_bonus
        return max(0, min(100, final_score))
    
    def _score_completeness(self, data: Dict[str, Any], 
                          validation_result: Dict[str, Any]) -> float:
        """Score data completeness (0-100)."""
        # Use validation completeness score as base
        base_completeness = validation_result.get("completeness_score", 0)
        
        # Additional completeness factors
        optional_fields = [
            "reporting_period", "facility_info", "methodology",
            "emission_factors_source", "calculation_version", "uncertainty"
        ]
        
        present_optional = sum(1 for field in optional_fields if data.get(field))
        optional_bonus = (present_optional / len(optional_fields)) * 20
        
        # Scope coverage
        scope_coverage = 0
        if data.get("scope1"):
            scope_coverage += 50
        if data.get("scope2"):
            scope_coverage += 50
        
        # Weighted completeness score
        completeness_score = (base_completeness * 0.6 + 
                            optional_bonus * 0.2 + 
                            scope_coverage * 0.2)
        
        return min(100, completeness_score)
    
    def _score_consistency(self, data: Dict[str, Any]) -> float:
        """Score data consistency (0-100)."""
        consistency_score = 90  # Base consistency assumption
        
        # Check for internal consistency issues
        consistency_issues = []
        
        # Unit consistency within scopes
        if data.get("scope1"):
            scope1 = data["scope1"]
            fuel_type = scope1.get("fuel_type")
            unit = scope1.get("unit")
            
            # Check fuel type and unit compatibility
            valid_combinations = {
                "gasoline": ["gallon", "liter"],
                "diesel": ["gallon", "liter"],
                "natural_gas": ["m3", "therm", "mmbtu"]
            }
            
            if fuel_type and unit:
                if fuel_type in valid_combinations:
                    if unit not in valid_combinations[fuel_type]:
                        consistency_issues.append("Scope 1 fuel type and unit mismatch")
        
        # Magnitude consistency checks
        if data.get("scope1") and data.get("scope2"):
            scope1_amount = data["scope1"].get("amount", 0)
            scope2_kwh = data["scope2"].get("kwh", 0)
            
            # Very rough magnitude check (this would be more sophisticated in practice)
            if scope1_amount > 0 and scope2_kwh > 0:
                # Check if magnitudes are reasonable relative to each other
                if scope1_amount > scope2_kwh * 100:  # Very rough heuristic
                    consistency_issues.append("Unusual magnitude relationship between Scope 1 and 2")
        
        # Temporal consistency
        if data.get("reporting_period"):
            # Check if reporting period is reasonable
            current_year = datetime.now().year
            try:
                if data["reporting_period"].isdigit():
                    year = int(data["reporting_period"])
                    if year > current_year:
                        consistency_issues.append("Future reporting period")
                    elif year < current_year - 5:
                        consistency_issues.append("Very old reporting period")
            except (ValueError, AttributeError):
                pass
        
        # Deduct points for consistency issues
        consistency_penalty = len(consistency_issues) * 15
        
        return max(0, consistency_score - consistency_penalty)
    
    def _score_timeliness(self, data: Dict[str, Any]) -> float:
        """Score data timeliness (0-100)."""
        base_score = 85  # Assume reasonably current data
        
        # Check reporting period recency
        if data.get("reporting_period"):
            try:
                current_year = datetime.now().year
                
                if data["reporting_period"].isdigit():
                    year = int(data["reporting_period"])
                    years_old = current_year - year
                    
                    if years_old == 0:
                        timeliness_bonus = 15  # Current year
                    elif years_old == 1:
                        timeliness_bonus = 10  # Last year
                    elif years_old == 2:
                        timeliness_bonus = 5   # Two years ago
                    elif years_old <= 5:
                        timeliness_bonus = 0   # Acceptable
                    else:
                        timeliness_bonus = -20  # Too old
                    
                    base_score += timeliness_bonus
                
            except (ValueError, AttributeError):
                base_score -= 10  # Penalty for unclear reporting period
        
        # Check for data collection timestamp
        if data.get("data_collection_date"):
            # This would check how recent the data collection was
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _score_validity(self, data: Dict[str, Any], 
                       validation_result: Dict[str, Any]) -> float:
        """Score data validity (0-100)."""
        # Use validation validity score as base
        return validation_result.get("validity_score", 0)
    
    def _determine_quality_level(self, overall_score: float, 
                               dimension_scores: Dict[str, float]) -> str:
        """Determine overall quality level."""
        if overall_score >= 90:
            return "excellent"
        elif overall_score >= 80:
            return "good"
        elif overall_score >= 70:
            return "fair"
        elif overall_score >= 60:
            return "poor"
        else:
            return "unacceptable"
    
    def _create_quality_assessment(self, dimension_scores: Dict[str, float], 
                                 overall_score: float) -> Dict[str, Any]:
        """Create detailed quality assessment."""
        
        # Find strongest and weakest dimensions
        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)
        strongest = sorted_dimensions[0]
        weakest = sorted_dimensions[-1]
        
        # Identify dimensions needing attention
        needs_attention = [dim for dim, score in dimension_scores.items() if score < 70]
        
        return {
            "overall_score": overall_score,
            "strongest_dimension": {
                "name": strongest[0],
                "score": strongest[1]
            },
            "weakest_dimension": {
                "name": weakest[0],
                "score": weakest[1]
            },
            "dimensions_needing_attention": needs_attention,
            "ready_for_sec_filing": overall_score >= 75 and len(needs_attention) <= 1,
            "improvement_potential": 100 - overall_score
        }
    
    def _generate_quality_recommendations(self, dimension_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate quality improvement recommendations."""
        recommendations = []
        
        for dimension, score in dimension_scores.items():
            if score < 70:
                rec = self._get_dimension_recommendation(dimension, score)
                recommendations.append(rec)
        
        # Overall recommendations
        avg_score = statistics.mean(dimension_scores.values())
        if avg_score < 60:
            recommendations.append({
                "priority": "critical",
                "dimension": "overall",
                "title": "Comprehensive Quality Improvement Required",
                "description": "Multiple quality dimensions are below acceptable thresholds",
                "actions": [
                    "Implement comprehensive data quality management",
                    "Review data collection and validation processes",
                    "Consider third-party data verification"
                ]
            })
        
        return recommendations
    
    def _get_dimension_recommendation(self, dimension: str, score: float) -> Dict[str, Any]:
        """Get specific recommendation for quality dimension."""
        
        priority = "high" if score < 50 else "medium"
        
        recommendations_map = {
            "accuracy": {
                "title": "Improve Data Accuracy",
                "description": f"Accuracy score ({score:.1f}) indicates potential data quality issues",
                "actions": [
                    "Verify emission factors and calculation methods",
                    "Cross-check data against source documents",
                    "Implement data validation checkpoints"
                ]
            },
            "completeness": {
                "title": "Enhance Data Completeness", 
                "description": f"Completeness score ({score:.1f}) shows missing data elements",
                "actions": [
                    "Fill missing required data fields",
                    "Add optional fields for better context",
                    "Ensure all emission sources are captured"
                ]
            },
            "consistency": {
                "title": "Improve Data Consistency",
                "description": f"Consistency score ({score:.1f}) indicates internal data conflicts",
                "actions": [
                    "Review data for internal consistency",
                    "Standardize units and formats",
                    "Reconcile conflicting data points"
                ]
            },
            "timeliness": {
                "title": "Update Data Timeliness",
                "description": f"Timeliness score ({score:.1f}) suggests outdated information",
                "actions": [
                    "Update to most recent reporting period",
                    "Establish regular data refresh cycles",
                    "Verify data collection dates"
                ]
            },
            "validity": {
                "title": "Enhance Data Validity",
                "description": f"Validity score ({score:.1f}) shows format or range issues",
                "actions": [
                    "Validate data formats and ranges",
                    "Check business rule compliance",
                    "Fix data type and format issues"
                ]
            }
        }
        
        rec = recommendations_map.get(dimension, {
            "title": f"Improve {dimension.title()}",
            "description": f"{dimension.title()} needs attention",
            "actions": ["Review and improve data quality"]
        })
        
        return {
            "priority": priority,
            "dimension": dimension,
            **rec
        }