"""
Agents API Routes

API endpoints for SEC compliance agents.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from ..models.database import get_db
from ..agents.agent_manager import AgentManager
from .dependencies import get_current_user

router = APIRouter(tags=["Agents"])

# Initialize agent manager
agent_manager = AgentManager()


@router.post("/full-workflow")
async def run_full_compliance_workflow(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Run complete SEC compliance workflow using all agents.
    
    This endpoint orchestrates:
    1. Data quality assessment
    2. EPA validation with confidence scoring
    3. SEC compliance analysis
    4. Audit trail creation
    """
    try:
        result = await agent_manager.run_full_compliance_workflow(data, db)
        return {
            "status": "success",
            "message": "Full compliance workflow completed",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow failed: {str(e)}"
        )


@router.post("/validate-and-score")
async def validate_and_score_data(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Quick validation and scoring of emissions data.
    
    Runs data quality and EPA validation agents only.
    """
    try:
        result = await agent_manager.validate_and_score(data, db)
        return {
            "status": "success",
            "message": "Validation and scoring completed",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/targeted-analysis")
async def run_targeted_analysis(
    data: Dict[str, Any],
    agents: List[str],
    db: Session = Depends(get_db),
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Run analysis using specific agents only.
    
    Available agents:
    - sec_compliance
    - epa_validation
    - audit_trail
    - data_quality
    """
    try:
        result = await agent_manager.run_targeted_analysis(data, agents, db)
        return {
            "status": "success",
            "message": f"Targeted analysis completed using {len(agents)} agents",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Targeted analysis failed: {str(e)}"
        )


@router.get("/audit-report/{company}")
async def generate_audit_report(
    company: str,
    report_type: str = "compliance",
    db: Session = Depends(get_db),
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Generate comprehensive audit report for a company.
    
    Report types:
    - compliance: SEC compliance focused report
    - forensic: Forensic analysis report
    - summary: Summary report
    """
    try:
        result = await agent_manager.generate_audit_report(company, db, report_type)
        return {
            "status": "success",
            "message": f"{report_type.title()} audit report generated",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audit report generation failed: {str(e)}"
        )


@router.get("/status")
async def get_agents_status():
    """Get status and information about available agents."""
    try:
        status_info = agent_manager.get_agent_status()
        return {
            "status": "success",
            "message": "Agent status retrieved",
            "data": status_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.post("/data-quality")
async def analyze_data_quality(
    data: Dict[str, Any],
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Run data quality analysis only."""
    try:
        result = await agent_manager.agents["data_quality"].process(data)
        return {
            "status": "success",
            "message": "Data quality analysis completed",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data quality analysis failed: {str(e)}"
        )


@router.post("/epa-validation")
async def run_epa_validation(
    data: Dict[str, Any],
    state: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Run EPA validation analysis only."""
    try:
        result = await agent_manager.agents["epa_validation"].process(
            data, db=db, state=state, year=year
        )
        return {
            "status": "success",
            "message": "EPA validation completed",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"EPA validation failed: {str(e)}"
        )


@router.post("/sec-compliance")
async def run_sec_compliance_analysis(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Run SEC compliance analysis only."""
    try:
        result = await agent_manager.agents["sec_compliance"].process(data, db=db)
        return {
            "status": "success",
            "message": "SEC compliance analysis completed",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SEC compliance analysis failed: {str(e)}"
        )