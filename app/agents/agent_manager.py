"""
Agent Manager

Orchestrates and manages all SEC compliance agents.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import asyncio
import logging

from .sec_compliance_agent import SECComplianceAgent
from .epa_validation_agent import EPAValidationAgent
from .audit_trail_agent import AuditTrailAgent
from .data_quality_agent import DataQualityAgent

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages and orchestrates SEC compliance agents."""
    
    def __init__(self):
        self.agents = {
            "sec_compliance": SECComplianceAgent(),
            "epa_validation": EPAValidationAgent(),
            "audit_trail": AuditTrailAgent(),
            "data_quality": DataQualityAgent()
        }
        self.version = "1.0.0"
    
    async def run_full_compliance_workflow(self, data: Dict[str, Any], 
                                         db: Optional[Session] = None) -> Dict[str, Any]:
        """Run complete SEC compliance workflow using all agents."""
        
        workflow_result = {
            "status": "success",
            "workflow_version": self.version,
            "agents_used": list(self.agents.keys()),
            "results": {},
            "summary": {},
            "recommendations": []
        }
        
        try:
            logger.info(f"Starting full compliance workflow for company: {data.get('company')}")
            
            # Step 1: Data Quality Assessment
            logger.info("Step 1: Running data quality assessment")
            dq_result = await self.agents["data_quality"].process(data)
            workflow_result["results"]["data_quality"] = dq_result
            
            # Step 2: EPA Validation
            logger.info("Step 2: Running EPA validation")
            epa_result = await self.agents["epa_validation"].process(data, db=db)
            workflow_result["results"]["epa_validation"] = epa_result
            
            # Step 3: SEC Compliance Analysis
            logger.info("Step 3: Running SEC compliance analysis")
            sec_result = await self.agents["sec_compliance"].process(data, db=db)
            workflow_result["results"]["sec_compliance"] = sec_result
            
            # Step 4: Audit Trail Creation
            if db:
                logger.info("Step 4: Creating audit trail")
                audit_data = {
                    "company": data["company"],
                    "inputs": data,
                    "outputs": sec_result.get("data", {}).get("emissions", {}),
                    "validation": epa_result.get("data", {}),
                    "workflow_results": {
                        "data_quality": dq_result.get("data", {}),
                        "epa_validation": epa_result.get("data", {}),
                        "sec_compliance": sec_result.get("data", {})
                    }
                }
                
                audit_result = await self.agents["audit_trail"].process(
                    audit_data, db=db, action="create"
                )
                workflow_result["results"]["audit_trail"] = audit_result
            
            # Step 5: Generate Workflow Summary
            workflow_result["summary"] = self._create_workflow_summary(workflow_result["results"])
            
            # Step 6: Compile Recommendations
            workflow_result["recommendations"] = self._compile_recommendations(workflow_result["results"])
            
            logger.info("Full compliance workflow completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            workflow_result["status"] = "error"
            workflow_result["error"] = str(e)
        
        return workflow_result
    
    async def run_targeted_analysis(self, data: Dict[str, Any], 
                                  agents: List[str],
                                  db: Optional[Session] = None) -> Dict[str, Any]:
        """Run analysis using specific agents only."""
        
        result = {
            "status": "success",
            "agents_used": agents,
            "results": {}
        }
        
        try:
            for agent_name in agents:
                if agent_name in self.agents:
                    logger.info(f"Running {agent_name} agent")
                    agent_result = await self.agents[agent_name].process(data, db=db)
                    result["results"][agent_name] = agent_result
                else:
                    logger.warning(f"Unknown agent: {agent_name}")
                    result["results"][agent_name] = {
                        "status": "error",
                        "message": f"Agent '{agent_name}' not found"
                    }
        
        except Exception as e:
            logger.error(f"Targeted analysis failed: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    async def validate_and_score(self, data: Dict[str, Any], 
                               db: Optional[Session] = None) -> Dict[str, Any]:
        """Quick validation and scoring workflow."""
        
        agents_to_run = ["data_quality", "epa_validation"]
        return await self.run_targeted_analysis(data, agents_to_run, db)
    
    async def generate_audit_report(self, company: str, 
                                  db: Session,
                                  report_type: str = "compliance") -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        
        audit_data = {
            "company": company,
            "report_type": report_type
        }
        
        return await self.agents["audit_trail"].process(
            audit_data, db=db, action="report"
        )
    
    def _create_workflow_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of workflow results."""
        
        summary = {
            "overall_status": "success",
            "confidence_scores": {},
            "quality_scores": {},
            "issues_summary": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "sec_filing_readiness": "unknown"
        }
        
        # Extract confidence scores
        if "epa_validation" in results:
            epa_data = results["epa_validation"].get("data", {})
            if "enhanced_confidence" in epa_data:
                summary["confidence_scores"]["epa_validation"] = epa_data["enhanced_confidence"].get("enhanced_score", 0)
        
        if "sec_compliance" in results:
            sec_data = results["sec_compliance"].get("data", {})
            if "confidence" in sec_data:
                summary["confidence_scores"]["sec_compliance"] = sec_data["confidence"].get("score", 0)
        
        # Extract quality scores
        if "data_quality" in results:
            dq_data = results["data_quality"].get("data", {})
            if "quality_scores" in dq_data:
                summary["quality_scores"] = dq_data["quality_scores"].get("dimension_scores", {})
                summary["quality_scores"]["overall"] = dq_data["quality_scores"].get("overall_score", 0)
        
        # Count issues across all agents
        for agent_name, agent_result in results.items():
            agent_data = agent_result.get("data", {})
            
            # Count validation issues
            if "validation" in agent_data:
                validation = agent_data["validation"]
                summary["issues_summary"]["critical"] += validation.get("critical_issues", 0)
                summary["issues_summary"]["high"] += validation.get("high_issues", 0)
                summary["issues_summary"]["medium"] += validation.get("medium_issues", 0)
                summary["issues_summary"]["low"] += validation.get("low_issues", 0)
            
            # Count anomalies
            if "anomalies" in agent_data:
                anomalies = agent_data["anomalies"]
                severity_summary = anomalies.get("summary", {}).get("by_severity", {})
                for severity, count in severity_summary.items():
                    if severity in summary["issues_summary"]:
                        summary["issues_summary"][severity] += count
        
        # Determine SEC filing readiness
        avg_confidence = sum(summary["confidence_scores"].values()) / len(summary["confidence_scores"]) if summary["confidence_scores"] else 0
        critical_issues = summary["issues_summary"]["critical"]
        high_issues = summary["issues_summary"]["high"]
        
        if critical_issues > 0:
            summary["sec_filing_readiness"] = "not_ready"
            summary["overall_status"] = "needs_attention"
        elif avg_confidence >= 80 and high_issues <= 1:
            summary["sec_filing_readiness"] = "ready"
        elif avg_confidence >= 60 and high_issues <= 3:
            summary["sec_filing_readiness"] = "review_recommended"
        else:
            summary["sec_filing_readiness"] = "improvements_needed"
            summary["overall_status"] = "needs_improvement"
        
        return summary
    
    def _compile_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compile recommendations from all agents."""
        
        all_recommendations = []
        
        for agent_name, agent_result in results.items():
            agent_data = agent_result.get("data", {})
            
            # Extract recommendations from different result structures
            recommendations = []
            
            if "recommendations" in agent_data:
                if isinstance(agent_data["recommendations"], list):
                    recommendations = agent_data["recommendations"]
            
            # Add agent context to recommendations
            for rec in recommendations:
                if isinstance(rec, str):
                    all_recommendations.append({
                        "source_agent": agent_name,
                        "priority": "medium",
                        "recommendation": rec
                    })
                elif isinstance(rec, dict):
                    rec["source_agent"] = agent_name
                    all_recommendations.append(rec)
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 2))
        
        return all_recommendations
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        
        return {
            "manager_version": self.version,
            "available_agents": list(self.agents.keys()),
            "agent_details": {
                name: {
                    "name": agent.name,
                    "version": agent.version,
                    "created_at": agent.created_at.isoformat()
                }
                for name, agent in self.agents.items()
            }
        }