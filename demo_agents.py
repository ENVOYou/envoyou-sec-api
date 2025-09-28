#!/usr/bin/env python3
"""
Demo script for Envoyou SEC API Agents

This script demonstrates how to use the intelligent agents for SEC compliance.
"""

import asyncio
import json
from app.agents.agent_manager import AgentManager


async def demo_agents():
    """Demonstrate the SEC compliance agents."""
    
    print("🤖 Envoyou SEC API Agents Demo")
    print("=" * 50)
    
    # Initialize agent manager
    agent_manager = AgentManager()
    
    # Demo data
    demo_data = {
        "company": "Demo Manufacturing Corp",
        "scope1": {
            "fuel_type": "natural_gas",
            "amount": 1000,
            "unit": "mmbtu"
        },
        "scope2": {
            "kwh": 500000,
            "grid_region": "RFC"
        },
        "reporting_period": "2024",
        "methodology": "EPA guidelines"
    }
    
    print(f"📊 Demo Company: {demo_data['company']}")
    print(f"🔥 Scope 1: {demo_data['scope1']['amount']} {demo_data['scope1']['unit']} of {demo_data['scope1']['fuel_type']}")
    print(f"⚡ Scope 2: {demo_data['scope2']['kwh']:,} kWh in {demo_data['scope2']['grid_region']} region")
    print()
    
    # 1. Data Quality Analysis
    print("🔍 Step 1: Data Quality Analysis")
    print("-" * 30)
    
    dq_result = await agent_manager.agents["data_quality"].process(demo_data)
    
    if dq_result["status"] == "success":
        dq_data = dq_result["data"]
        quality_scores = dq_data.get("quality_scores", {})
        overall_score = quality_scores.get("overall_score", 0)
        quality_level = quality_scores.get("quality_level", "unknown")
        
        print(f"✅ Overall Quality Score: {overall_score:.1f}/100 ({quality_level})")
        
        dimension_scores = quality_scores.get("dimension_scores", {})
        for dimension, score in dimension_scores.items():
            print(f"   • {dimension.title()}: {score:.1f}/100")
        
        anomalies = dq_data.get("anomalies", {})
        total_anomalies = anomalies.get("summary", {}).get("total_anomalies", 0)
        print(f"🚨 Anomalies Detected: {total_anomalies}")
    else:
        print(f"❌ Data Quality Analysis Failed: {dq_result.get('message', 'Unknown error')}")
    
    print()
    
    # 2. EPA Validation
    print("🏛️ Step 2: EPA Validation")
    print("-" * 25)
    
    epa_result = await agent_manager.agents["epa_validation"].process(demo_data)
    
    if epa_result["status"] == "success":
        epa_data = epa_result["data"]
        
        # Basic validation results
        epa_info = epa_data.get("epa", {})
        matches_count = epa_info.get("matches_count", 0)
        flags = epa_data.get("flags", [])
        
        print(f"🔍 EPA Matches Found: {matches_count}")
        print(f"⚠️ Validation Flags: {len(flags)}")
        
        # Enhanced confidence analysis
        enhanced_confidence = epa_data.get("enhanced_confidence", {})
        if enhanced_confidence:
            confidence_score = enhanced_confidence.get("enhanced_score", 0)
            confidence_level = enhanced_confidence.get("confidence_level", "unknown")
            print(f"📊 Enhanced Confidence: {confidence_score:.1f}/100 ({confidence_level})")
        
        # Show flags if any
        if flags:
            print("   Flags:")
            for flag in flags[:3]:  # Show first 3 flags
                severity = flag.get("severity", "unknown")
                message = flag.get("message", "No message")
                print(f"   • {severity.upper()}: {message}")
    else:
        print(f"❌ EPA Validation Failed: {epa_result.get('message', 'Unknown error')}")
    
    print()
    
    # 3. SEC Compliance Analysis
    print("📋 Step 3: SEC Compliance Analysis")
    print("-" * 33)
    
    sec_result = await agent_manager.agents["sec_compliance"].process(demo_data)
    
    if sec_result["status"] == "success":
        sec_data = sec_result["data"]
        
        # Emissions results
        emissions = sec_data.get("emissions", {})
        if emissions:
            totals = emissions.get("totals", {})
            emissions_kg = totals.get("emissions_kg", 0)
            emissions_tonnes = totals.get("emissions_tonnes", 0)
            
            print(f"🏭 Total Emissions: {emissions_tonnes:.2f} tonnes CO2e ({emissions_kg:,.0f} kg)")
        
        # Confidence analysis
        confidence = sec_data.get("confidence", {})
        if confidence:
            score = confidence.get("score", 0)
            level = confidence.get("level", "unknown")
            recommendation = confidence.get("recommendation", "No recommendation")
            
            print(f"📈 SEC Confidence: {score}/100 ({level})")
            print(f"💡 Recommendation: {recommendation}")
        
        # SEC package status
        sec_package = sec_data.get("sec_package")
        if sec_package:
            print("📦 SEC Filing Package: Generated")
        else:
            print("📦 SEC Filing Package: Not generated (confidence too low)")
        
        # Recommendations
        recommendations = sec_data.get("recommendations", [])
        if recommendations:
            print("📝 Recommendations:")
            for rec in recommendations[:3]:  # Show first 3
                print(f"   • {rec}")
    else:
        print(f"❌ SEC Compliance Analysis Failed: {sec_result.get('message', 'Unknown error')}")
    
    print()
    
    # 4. Full Workflow Demo
    print("🚀 Step 4: Full Workflow Demo")
    print("-" * 28)
    
    print("Running complete compliance workflow...")
    workflow_result = await agent_manager.run_full_compliance_workflow(demo_data)
    
    if workflow_result["status"] == "success":
        summary = workflow_result.get("summary", {})
        
        overall_status = summary.get("overall_status", "unknown")
        sec_readiness = summary.get("sec_filing_readiness", "unknown")
        
        print(f"✅ Workflow Status: {overall_status}")
        print(f"📋 SEC Filing Readiness: {sec_readiness}")
        
        # Confidence scores summary
        confidence_scores = summary.get("confidence_scores", {})
        if confidence_scores:
            print("📊 Confidence Scores:")
            for source, score in confidence_scores.items():
                print(f"   • {source.replace('_', ' ').title()}: {score:.1f}/100")
        
        # Issues summary
        issues = summary.get("issues_summary", {})
        total_issues = sum(issues.values())
        if total_issues > 0:
            print(f"⚠️ Total Issues: {total_issues}")
            for severity, count in issues.items():
                if count > 0:
                    print(f"   • {severity.title()}: {count}")
        
        # Top recommendations
        recommendations = workflow_result.get("recommendations", [])
        if recommendations:
            print("🎯 Top Recommendations:")
            for rec in recommendations[:3]:
                priority = rec.get("priority", "medium")
                text = rec.get("recommendation", rec.get("title", "No recommendation"))
                print(f"   • [{priority.upper()}] {text}")
    else:
        print(f"❌ Full Workflow Failed: {workflow_result.get('error', 'Unknown error')}")
    
    print()
    print("🎉 Demo completed! The agents are now active and ready for use.")
    print()
    print("💡 Next steps:")
    print("   • Start the API server: uvicorn app.api_server:app --reload")
    print("   • Test agents via API: POST /v1/agents/full-workflow")
    print("   • Check agent status: GET /v1/agents/status")


if __name__ == "__main__":
    asyncio.run(demo_agents())