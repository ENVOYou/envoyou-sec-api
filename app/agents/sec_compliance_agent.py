"""
SEC Compliance Agent

Intelligent agent for SEC Climate Disclosure compliance automation.
Handles emissions calculation, validation, and SEC filing preparation.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from .base_agent import BaseAgent
from ..services.emissions_calculator import calculate_emissions
from ..services.validation_service import cross_validate_epa
from ..services.sec_exporter import build_and_upload_sec_package
from ..services.audit_service import create_audit_entry
from ..tools.confidence_analyzer import ConfidenceAnalyzer
from ..tools.deviation_detector import DeviationDetector


class SECComplianceAgent(BaseAgent):
    """Agent for complete SEC Climate Disclosure compliance workflow."""
    
    def __init__(self):
        super().__init__("SEC_Compliance_Agent", "1.0.0")
        self.confidence_analyzer = ConfidenceAnalyzer()
        self.deviation_detector = DeviationDetector()
    
    async def process(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Complete SEC compliance workflow:
        1. Calculate emissions
        2. EPA validation with confidence scoring
        3. Generate SEC filing package
        4. Create audit trail
        """
        db: Optional[Session] = kwargs.get("db")
        
        try:
            self.validate_input(data, ["company", "scope1", "scope2"])
            self.log_action("sec_compliance_start", {"company": data.get("company")})
            
            # Step 1: Calculate emissions
            emissions_result = calculate_emissions(data)
            self.log_action("emissions_calculated", {"total_kg": emissions_result["totals"]["emissions_kg"]})
            
            # Step 2: EPA validation with confidence scoring
            validation_result = cross_validate_epa(data, db=db)
            confidence_score = validation_result.get("confidence_analysis", {})
            
            # Step 3: Deviation detection
            deviations = await self.deviation_detector.detect_deviations(
                emissions_result, validation_result
            )
            
            # Step 4: Generate SEC package if confidence is sufficient
            sec_package = None
            if confidence_score.get("score", 0) >= 60:  # Medium confidence threshold
                sec_package = build_and_upload_sec_package(
                company=data["company"],
                payload=data,
                db=db
            )
                self.log_action("sec_package_generated")
            
            # Step 5: Create audit trail
            if db:
                audit_entry = create_audit_entry(
                    db=db,
                    company=data["company"],
                    inputs=data,
                    outputs=emissions_result,
                    validation=validation_result,
                    agent_info={
                        "agent": self.name,
                        "version": self.version,
                        "confidence_score": confidence_score.get("score"),
                        "deviations": deviations
                    }
                )
                self.log_action("audit_trail_created", {"audit_id": audit_entry.id})
            
            # Compile final result
            result = {
                "emissions": emissions_result,
                "validation": validation_result,
                "confidence": confidence_score,
                "deviations": deviations,
                "sec_package": sec_package,
                "recommendations": self._generate_recommendations(confidence_score, deviations)
            }
            
            self.log_action("sec_compliance_completed", {"confidence_score": confidence_score.get("score")})
            return self.create_response("success", result, "SEC compliance analysis completed")
            
        except Exception as e:
            self.log_action("sec_compliance_error", {"error": str(e)})
            return self.create_response("error", {}, f"SEC compliance analysis failed: {str(e)}")
    
    def _generate_recommendations(self, confidence: Dict[str, Any], 
                                deviations: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis results."""
        recommendations = []
        
        score = confidence.get("score", 0)
        level = confidence.get("level", "low")
        
        if score >= 80:
            recommendations.append("✅ High confidence - Ready for SEC filing")
        elif score >= 60:
            recommendations.append("⚠️ Medium confidence - Review recommended before filing")
            recommendations.append("Consider additional data validation")
        else:
            recommendations.append("❌ Low confidence - Manual verification required")
            recommendations.append("Significant data quality issues detected")
        
        if deviations.get("high_severity_count", 0) > 0:
            recommendations.append("🔍 High-severity deviations detected - investigate before filing")
        
        if deviations.get("quantitative_deviations"):
            recommendations.append("📊 Quantitative deviations found - verify calculation inputs")
        
        return recommendations