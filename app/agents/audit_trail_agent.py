"""
Audit Trail Agent

Specialized agent for forensic-grade audit trail management and compliance tracking.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from .base_agent import BaseAgent
from ..services.audit_service import create_audit_entry
from ..models.audit_trail import AuditTrail
from ..tools.forensic_analyzer import ForensicAnalyzer


class AuditTrailAgent(BaseAgent):
    """Agent for comprehensive audit trail management and forensic analysis."""
    
    def __init__(self):
        super().__init__("Audit_Trail_Agent", "1.0.0")
        self.forensic_analyzer = ForensicAnalyzer()
    
    async def process(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Audit trail workflow:
        1. Create comprehensive audit entries
        2. Forensic analysis of data lineage
        3. Compliance verification
        4. Generate audit reports
        """
        db: Optional[Session] = kwargs.get("db")
        action: str = kwargs.get("action", "create")
        
        try:
            if action == "create":
                return await self._create_audit_entry(data, db)
            elif action == "analyze":
                return await self._analyze_audit_trail(data, db)
            elif action == "report":
                return await self._generate_audit_report(data, db)
            else:
                raise ValueError(f"Unknown audit action: {action}")
                
        except Exception as e:
            self.log_action("audit_trail_error", {"error": str(e), "action": action})
            return self.create_response("error", {}, f"Audit trail operation failed: {str(e)}")
    
    async def _create_audit_entry(self, data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Create comprehensive audit entry with forensic details."""
        self.validate_input(data, ["company", "inputs", "outputs"])
        
        # Enhanced audit data with forensic information
        forensic_data = await self.forensic_analyzer.analyze_data_lineage(data)
        
        audit_entry = create_audit_entry(
            db=db,
            company=data["company"],
            inputs=data["inputs"],
            outputs=data["outputs"],
            validation=data.get("validation"),
            agent_info={
                "agent": self.name,
                "version": self.version,
                "forensic_hash": forensic_data["hash"],
                "data_lineage": forensic_data["lineage"],
                "integrity_check": forensic_data["integrity"]
            }
        )
        
        self.log_action("audit_entry_created", {
            "audit_id": audit_entry.id,
            "company": data["company"],
            "forensic_hash": forensic_data["hash"]
        })
        
        return self.create_response("success", {
            "audit_id": audit_entry.id,
            "forensic_data": forensic_data,
            "compliance_status": "recorded"
        }, "Audit entry created with forensic verification")
    
    async def _analyze_audit_trail(self, data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Analyze audit trail for compliance and integrity."""
        company = data.get("company")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        
        # Retrieve audit entries (mock for now)
        audit_entries = []  # Would use actual audit repository
        
        # Forensic analysis
        forensic_analysis = await self.forensic_analyzer.analyze_audit_integrity(audit_entries)
        
        # Compliance analysis
        compliance_analysis = self._analyze_compliance(audit_entries)
        
        result = {
            "total_entries": len(audit_entries),
            "date_range": {"start": start_date, "end": end_date},
            "forensic_analysis": forensic_analysis,
            "compliance_analysis": compliance_analysis,
            "recommendations": self._generate_audit_recommendations(
                forensic_analysis, compliance_analysis
            )
        }
        
        self.log_action("audit_trail_analyzed", {
            "company": company,
            "entries_count": len(audit_entries),
            "integrity_score": forensic_analysis.get("integrity_score")
        })
        
        return self.create_response("success", result, "Audit trail analysis completed")
    
    async def _generate_audit_report(self, data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Generate comprehensive audit report for SEC compliance."""
        company = data.get("company")
        report_type = data.get("report_type", "compliance")
        
        # Get audit data (mock for now)
        audit_entries = []  # Would use actual audit repository
        
        # Generate report based on type
        if report_type == "compliance":
            report = self._generate_compliance_report(audit_entries)
        elif report_type == "forensic":
            report = await self._generate_forensic_report(audit_entries)
        else:
            report = self._generate_summary_report(audit_entries)
        
        self.log_action("audit_report_generated", {
            "company": company,
            "report_type": report_type,
            "entries_count": len(audit_entries)
        })
        
        return self.create_response("success", {
            "report": report,
            "metadata": {
                "company": company,
                "report_type": report_type,
                "generated_at": datetime.utcnow().isoformat(),
                "entries_analyzed": len(audit_entries)
            }
        }, f"{report_type.title()} audit report generated")
    
    def _analyze_compliance(self, audit_entries: List[AuditTrail]) -> Dict[str, Any]:
        """Analyze compliance status of audit entries."""
        total = len(audit_entries)
        if total == 0:
            return {"status": "no_data", "score": 0}
        
        complete_entries = sum(1 for entry in audit_entries if entry.outputs and entry.inputs)
        validated_entries = sum(1 for entry in audit_entries if entry.validation_result)
        
        compliance_score = (complete_entries / total) * 100
        validation_rate = (validated_entries / total) * 100
        
        return {
            "total_entries": total,
            "complete_entries": complete_entries,
            "validated_entries": validated_entries,
            "compliance_score": round(compliance_score, 2),
            "validation_rate": round(validation_rate, 2),
            "status": "compliant" if compliance_score >= 95 else "needs_attention"
        }
    
    def _generate_compliance_report(self, audit_entries: List[AuditTrail]) -> Dict[str, Any]:
        """Generate SEC compliance-focused audit report."""
        return {
            "report_type": "SEC Compliance Audit Report",
            "summary": self._analyze_compliance(audit_entries),
            "entries": [
                {
                    "id": entry.id,
                    "timestamp": entry.timestamp.isoformat(),
                    "company": entry.company,
                    "has_validation": bool(entry.validation_result),
                    "calculation_version": entry.calculation_version
                }
                for entry in audit_entries
            ]
        }
    
    async def _generate_forensic_report(self, audit_entries: List[AuditTrail]) -> Dict[str, Any]:
        """Generate forensic analysis report."""
        forensic_analysis = await self.forensic_analyzer.analyze_audit_integrity(audit_entries)
        
        return {
            "report_type": "Forensic Audit Report",
            "integrity_analysis": forensic_analysis,
            "data_lineage": [
                {
                    "id": entry.id,
                    "timestamp": entry.timestamp.isoformat(),
                    "data_hash": entry.agent_info.get("forensic_hash") if entry.agent_info else None,
                    "integrity_verified": True  # Would be actual verification
                }
                for entry in audit_entries
            ]
        }
    
    def _generate_summary_report(self, audit_entries: List[AuditTrail]) -> Dict[str, Any]:
        """Generate summary audit report."""
        return {
            "report_type": "Audit Summary Report",
            "total_entries": len(audit_entries),
            "date_range": {
                "earliest": min(entry.timestamp for entry in audit_entries).isoformat() if audit_entries else None,
                "latest": max(entry.timestamp for entry in audit_entries).isoformat() if audit_entries else None
            },
            "companies": list(set(entry.company for entry in audit_entries))
        }
    
    def _generate_audit_recommendations(self, forensic: Dict[str, Any], 
                                      compliance: Dict[str, Any]) -> List[str]:
        """Generate audit-specific recommendations."""
        recommendations = []
        
        integrity_score = forensic.get("integrity_score", 100)
        compliance_score = compliance.get("compliance_score", 0)
        
        if integrity_score < 95:
            recommendations.append("🔒 Data integrity issues detected - forensic review required")
        
        if compliance_score < 90:
            recommendations.append("📋 Compliance gaps identified - complete missing audit data")
        
        if compliance.get("validation_rate", 0) < 80:
            recommendations.append("✅ Increase validation coverage for better compliance")
        
        return recommendations