"""
Data Quality Agent

Specialized agent for data quality assessment and improvement recommendations.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_agent import BaseAgent
from ..tools.data_validator import DataValidator
from ..tools.quality_scorer import QualityScorer
from ..tools.anomaly_detector import AnomalyDetector


class DataQualityAgent(BaseAgent):
    """Agent for comprehensive data quality assessment and improvement."""
    
    def __init__(self):
        super().__init__("Data_Quality_Agent", "1.0.0")
        self.data_validator = DataValidator()
        self.quality_scorer = QualityScorer()
        self.anomaly_detector = AnomalyDetector()
    
    async def process(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Data quality workflow:
        1. Validate data completeness and format
        2. Score data quality across dimensions
        3. Detect anomalies and outliers
        4. Generate improvement recommendations
        """
        try:
            self.validate_input(data, ["company"])
            self.log_action("data_quality_start", {"company": data.get("company")})
            
            # Step 1: Data validation
            validation_results = await self.data_validator.validate_emissions_data(data)
            
            # Step 2: Quality scoring
            quality_scores = await self.quality_scorer.score_data_quality(data, validation_results)
            
            # Step 3: Anomaly detection
            anomalies = await self.anomaly_detector.detect_anomalies(data)
            
            # Step 4: Comprehensive assessment
            assessment = self._create_quality_assessment(
                validation_results, quality_scores, anomalies
            )
            
            # Step 5: Improvement recommendations
            recommendations = self._generate_improvement_recommendations(assessment)
            
            result = {
                "validation": validation_results,
                "quality_scores": quality_scores,
                "anomalies": anomalies,
                "assessment": assessment,
                "recommendations": recommendations
            }
            
            self.log_action("data_quality_completed", {
                "overall_score": assessment.get("overall_score"),
                "anomalies_count": len(anomalies.get("detected", []))
            })
            
            return self.create_response("success", result, "Data quality analysis completed")
            
        except Exception as e:
            self.log_action("data_quality_error", {"error": str(e)})
            return self.create_response("error", {}, f"Data quality analysis failed: {str(e)}")
    
    def _create_quality_assessment(self, validation: Dict[str, Any], 
                                 quality: Dict[str, Any], 
                                 anomalies: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive data quality assessment."""
        
        # Calculate overall quality score
        validation_score = validation.get("score", 0)
        quality_score = quality.get("overall_score", 0)
        anomaly_penalty = len(anomalies.get("detected", [])) * 5  # 5 points per anomaly
        
        overall_score = max(0, min(100, (validation_score + quality_score) / 2 - anomaly_penalty))
        
        # Determine quality level
        if overall_score >= 90:
            level = "excellent"
            status = "ready_for_filing"
        elif overall_score >= 75:
            level = "good"
            status = "minor_improvements_needed"
        elif overall_score >= 60:
            level = "fair"
            status = "improvements_required"
        else:
            level = "poor"
            status = "major_improvements_required"
        
        return {
            "overall_score": round(overall_score, 2),
            "level": level,
            "status": status,
            "dimensions": {
                "completeness": validation.get("completeness_score", 0),
                "accuracy": quality.get("accuracy_score", 0),
                "consistency": quality.get("consistency_score", 0),
                "timeliness": quality.get("timeliness_score", 0),
                "validity": validation.get("validity_score", 0)
            },
            "issues_summary": {
                "critical": validation.get("critical_issues", 0) + len([a for a in anomalies.get("detected", []) if a.get("severity") == "critical"]),
                "high": validation.get("high_issues", 0) + len([a for a in anomalies.get("detected", []) if a.get("severity") == "high"]),
                "medium": validation.get("medium_issues", 0) + len([a for a in anomalies.get("detected", []) if a.get("severity") == "medium"]),
                "low": validation.get("low_issues", 0) + len([a for a in anomalies.get("detected", []) if a.get("severity") == "low"])
            }
        }
    
    def _generate_improvement_recommendations(self, assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized improvement recommendations."""
        recommendations = []
        
        overall_score = assessment.get("overall_score", 0)
        dimensions = assessment.get("dimensions", {})
        issues = assessment.get("issues_summary", {})
        
        # Critical issues first
        if issues.get("critical", 0) > 0:
            recommendations.append({
                "priority": "critical",
                "category": "data_integrity",
                "title": "Critical Data Issues Detected",
                "description": "Address critical data integrity issues before proceeding with SEC filing",
                "actions": [
                    "Review data sources and collection methods",
                    "Verify calculation inputs and emission factors",
                    "Validate data against source documents"
                ]
            })
        
        # Dimension-specific recommendations
        for dimension, score in dimensions.items():
            if score < 70:
                recommendations.append(self._get_dimension_recommendation(dimension, score))
        
        # Overall score recommendations
        if overall_score < 60:
            recommendations.append({
                "priority": "high",
                "category": "overall_quality",
                "title": "Comprehensive Data Quality Improvement Needed",
                "description": "Overall data quality is below acceptable threshold for SEC filing",
                "actions": [
                    "Implement data quality management processes",
                    "Establish data validation checkpoints",
                    "Consider third-party data verification"
                ]
            })
        
        return recommendations
    
    def _get_dimension_recommendation(self, dimension: str, score: float) -> Dict[str, Any]:
        """Get specific recommendation for data quality dimension."""
        recommendations_map = {
            "completeness": {
                "title": "Improve Data Completeness",
                "description": f"Data completeness score ({score:.1f}) is below threshold",
                "actions": [
                    "Fill missing data fields",
                    "Verify all required emissions sources are included",
                    "Complete facility and operational data"
                ]
            },
            "accuracy": {
                "title": "Enhance Data Accuracy",
                "description": f"Data accuracy score ({score:.1f}) needs improvement",
                "actions": [
                    "Verify emission factors and calculation methods",
                    "Cross-check against source documents",
                    "Implement data validation rules"
                ]
            },
            "consistency": {
                "title": "Improve Data Consistency",
                "description": f"Data consistency score ({score:.1f}) indicates inconsistencies",
                "actions": [
                    "Standardize data formats and units",
                    "Reconcile conflicting data points",
                    "Establish data governance standards"
                ]
            },
            "timeliness": {
                "title": "Update Data Timeliness",
                "description": f"Data timeliness score ({score:.1f}) suggests outdated information",
                "actions": [
                    "Update to most recent reporting period",
                    "Verify data collection dates",
                    "Establish regular data refresh cycles"
                ]
            },
            "validity": {
                "title": "Enhance Data Validity",
                "description": f"Data validity score ({score:.1f}) indicates format or range issues",
                "actions": [
                    "Validate data formats and ranges",
                    "Check for logical inconsistencies",
                    "Verify against business rules"
                ]
            }
        }
        
        rec = recommendations_map.get(dimension, {
            "title": f"Improve {dimension.title()}",
            "description": f"{dimension.title()} score needs attention",
            "actions": ["Review and improve data quality"]
        })
        
        return {
            "priority": "high" if score < 50 else "medium",
            "category": f"data_{dimension}",
            **rec
        }