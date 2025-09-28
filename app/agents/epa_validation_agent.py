"""
EPA Validation Agent

Specialized agent for EPA data cross-validation and confidence scoring.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from .base_agent import BaseAgent
from ..services.validation_service import cross_validate_epa
from ..tools.confidence_analyzer import ConfidenceAnalyzer
from ..tools.epa_matcher import EPAMatcher


class EPAValidationAgent(BaseAgent):
    """Agent specialized in EPA data validation and confidence assessment."""
    
    def __init__(self):
        super().__init__("EPA_Validation_Agent", "1.0.0")
        self.confidence_analyzer = ConfidenceAnalyzer()
        self.epa_matcher = EPAMatcher()
    
    async def process(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        EPA validation workflow:
        1. Cross-validate against EPA data
        2. Analyze confidence score
        3. Detect anomalies and flags
        4. Provide actionable recommendations
        """
        db: Optional[Session] = kwargs.get("db")
        state: Optional[str] = kwargs.get("state")
        year: Optional[int] = kwargs.get("year")
        
        try:
            self.validate_input(data, ["company"])
            self.log_action("epa_validation_start", {"company": data.get("company")})
            
            # Step 1: EPA cross-validation
            validation_result = cross_validate_epa(data, db=db, state=state, year=year)
            
            # Step 2: Enhanced confidence analysis
            enhanced_confidence = await self.confidence_analyzer.analyze_confidence(
                validation_result, data
            )
            
            # Step 3: Advanced EPA matching
            advanced_matches = await self.epa_matcher.find_advanced_matches(
                data["company"], state=state
            )
            
            # Step 4: Flag analysis and recommendations
            flags_analysis = self._analyze_flags(validation_result.get("flags", []))
            
            # Compile enhanced result
            result = {
                **validation_result,
                "enhanced_confidence": enhanced_confidence,
                "advanced_matches": advanced_matches,
                "flags_analysis": flags_analysis,
                "recommendations": self._generate_epa_recommendations(
                    validation_result, enhanced_confidence, flags_analysis
                )
            }
            
            self.log_action("epa_validation_completed", {
                "confidence_score": enhanced_confidence.get("score"),
                "matches_count": len(advanced_matches.get("matches", []))
            })
            
            return self.create_response("success", result, "EPA validation completed")
            
        except Exception as e:
            self.log_action("epa_validation_error", {"error": str(e)})
            return self.create_response("error", {}, f"EPA validation failed: {str(e)}")
    
    def _analyze_flags(self, flags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze validation flags and categorize by severity."""
        analysis = {
            "total_flags": len(flags),
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_category": {},
            "actionable_items": []
        }
        
        for flag in flags:
            severity = flag.get("severity", "low")
            analysis["by_severity"][severity] += 1
            
            code = flag.get("code", "unknown")
            if code not in analysis["by_category"]:
                analysis["by_category"][code] = 0
            analysis["by_category"][code] += 1
            
            # Generate actionable items
            if severity in ["critical", "high"]:
                analysis["actionable_items"].append({
                    "priority": "high" if severity == "critical" else "medium",
                    "action": self._get_flag_action(code),
                    "details": flag.get("message", "")
                })
        
        return analysis
    
    def _get_flag_action(self, flag_code: str) -> str:
        """Get recommended action for specific flag codes."""
        actions = {
            "no_epa_match": "Verify company legal name and check for subsidiaries",
            "low_match_density": "Review company operations and facility locations",
            "state_mismatch": "Confirm operational state and facility addresses",
            "quantitative_deviation": "Verify calculation inputs and emission factors"
        }
        return actions.get(flag_code, "Review data quality and validation parameters")
    
    def _generate_epa_recommendations(self, validation: Dict[str, Any], 
                                    confidence: Dict[str, Any], 
                                    flags_analysis: Dict[str, Any]) -> List[str]:
        """Generate EPA-specific recommendations."""
        recommendations = []
        
        confidence_score = confidence.get("score", 0)
        critical_flags = flags_analysis["by_severity"]["critical"]
        high_flags = flags_analysis["by_severity"]["high"]
        
        if critical_flags > 0:
            recommendations.append("🚨 Critical EPA validation issues - immediate attention required")
        
        if high_flags > 0:
            recommendations.append("⚠️ High-priority EPA validation flags - review before proceeding")
        
        if confidence_score < 60:
            recommendations.append("📋 Low EPA confidence - consider manual facility verification")
        
        matches_count = validation.get("epa", {}).get("matches_count", 0)
        if matches_count == 0:
            recommendations.append("🔍 No EPA matches found - verify company name and operations")
        elif matches_count < 3:
            recommendations.append("📊 Limited EPA matches - consider expanding search criteria")
        
        return recommendations