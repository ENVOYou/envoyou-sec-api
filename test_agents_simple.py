#!/usr/bin/env python3
"""
Simple test for Envoyou SEC API Agents (without database)
"""

import asyncio
import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.data_quality_agent import DataQualityAgent
from app.agents.epa_validation_agent import EPAValidationAgent


async def test_agents_simple():
    """Test agents without database dependency."""
    
    print("🤖 Envoyou SEC API Agents - User Experience Test")
    print("=" * 55)
    
    # Demo data - what a user would submit
    user_data = {
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
        "reporting_period": "2024",
        "methodology": "EPA guidelines"
    }
    
    print(f"📊 User Input:")
    print(f"   Company: {user_data['company']}")
    print(f"   Scope 1: {user_data['scope1']['amount']:,} {user_data['scope1']['unit']} of {user_data['scope1']['fuel_type']}")
    print(f"   Scope 2: {user_data['scope2']['kwh']:,} kWh in {user_data['scope2']['grid_region']} region")
    print()
    
    # Test 1: Data Quality Analysis
    print("🔍 STEP 1: Data Quality Analysis")
    print("-" * 35)
    
    dq_agent = DataQualityAgent()
    dq_result = await dq_agent.process(user_data)
    
    if dq_result["status"] == "success":
        dq_data = dq_result["data"]
        
        # Quality Scores
        quality_scores = dq_data.get("quality_scores", {})
        overall_score = quality_scores.get("overall_score", 0)
        quality_level = quality_scores.get("quality_level", "unknown")
        
        print(f"✅ Overall Quality Score: {overall_score:.1f}/100")
        print(f"📈 Quality Level: {quality_level.upper()}")
        
        # Dimension breakdown
        dimension_scores = quality_scores.get("dimension_scores", {})
        print(f"📊 Quality Dimensions:")
        for dimension, score in dimension_scores.items():
            emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            print(f"   {emoji} {dimension.replace('_', ' ').title()}: {score:.1f}/100")
        
        # Assessment
        assessment = dq_data.get("assessment", {})
        ready_for_filing = assessment.get("ready_for_sec_filing", False)
        print(f"📋 SEC Filing Ready: {'✅ YES' if ready_for_filing else '❌ NO'}")
        
        # Anomalies
        anomalies = dq_data.get("anomalies", {})
        total_anomalies = anomalies.get("summary", {}).get("total_anomalies", 0)
        if total_anomalies > 0:
            print(f"🚨 Anomalies Detected: {total_anomalies}")
            severity_summary = anomalies.get("summary", {}).get("by_severity", {})
            for severity, count in severity_summary.items():
                if count > 0:
                    print(f"   • {severity.title()}: {count}")
        else:
            print(f"✅ No Anomalies Detected")
        
        # Recommendations
        recommendations = dq_data.get("recommendations", [])
        if recommendations:
            print(f"💡 Top Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                priority = rec.get("priority", "medium")
                title = rec.get("title", "No title")
                print(f"   {i}. [{priority.upper()}] {title}")
    
    print()
    
    # Test 2: EPA Validation
    print("🏛️ STEP 2: EPA Validation Analysis")
    print("-" * 35)
    
    epa_agent = EPAValidationAgent()
    epa_result = await epa_agent.process(user_data, state="CA")
    
    if epa_result["status"] == "success":
        epa_data = epa_result["data"]
        
        # Basic validation info
        epa_info = epa_data.get("epa", {})
        matches_count = epa_info.get("matches_count", 0)
        flags = epa_data.get("flags", [])
        
        print(f"🔍 EPA Facility Matches: {matches_count}")
        print(f"⚠️ Validation Flags: {len(flags)}")
        
        # Enhanced confidence
        enhanced_confidence = epa_data.get("enhanced_confidence", {})
        if enhanced_confidence:
            confidence_score = enhanced_confidence.get("enhanced_score", 0)
            confidence_level = enhanced_confidence.get("confidence_level", "unknown")
            
            emoji = "🟢" if confidence_score >= 80 else "🟡" if confidence_score >= 60 else "🔴"
            print(f"{emoji} EPA Confidence Score: {confidence_score:.1f}/100 ({confidence_level.upper()})")
        
        # Advanced matches
        advanced_matches = epa_data.get("advanced_matches", {})
        if advanced_matches:
            match_summary = advanced_matches.get("match_summary", {})
            best_confidence = match_summary.get("best_confidence", 0)
            recommendation = match_summary.get("recommendation", "No recommendation")
            
            print(f"🎯 Best Match Confidence: {best_confidence:.1f}")
            print(f"💡 EPA Recommendation: {recommendation}")
        
        # Flags details
        if flags:
            print(f"🚩 Validation Issues:")
            for flag in flags[:3]:  # Show top 3 flags
                severity = flag.get("severity", "unknown")
                message = flag.get("message", "No message")
                emoji = "🚨" if severity == "critical" else "⚠️" if severity == "high" else "ℹ️"
                print(f"   {emoji} [{severity.upper()}] {message}")
        
        # EPA-specific recommendations
        epa_recommendations = epa_data.get("recommendations", [])
        if epa_recommendations:
            print(f"📋 EPA Recommendations:")
            for rec in epa_recommendations[:2]:
                print(f"   • {rec}")
    
    print()
    
    # Summary for User
    print("📊 SUMMARY FOR USER")
    print("-" * 20)
    
    # Overall assessment
    overall_quality = quality_scores.get("overall_score", 0) if 'quality_scores' in locals() else 0
    epa_confidence = enhanced_confidence.get("enhanced_score", 0) if 'enhanced_confidence' in locals() else 0
    
    avg_score = (overall_quality + epa_confidence) / 2 if epa_confidence > 0 else overall_quality
    
    if avg_score >= 85:
        status_emoji = "🟢"
        status_text = "EXCELLENT - Ready for SEC Filing"
        next_steps = "Your data is ready for SEC Climate Disclosure filing."
    elif avg_score >= 70:
        status_emoji = "🟡"
        status_text = "GOOD - Minor Review Recommended"
        next_steps = "Address minor issues before filing."
    elif avg_score >= 50:
        status_emoji = "🟠"
        status_text = "FAIR - Improvements Needed"
        next_steps = "Significant improvements required before filing."
    else:
        status_emoji = "🔴"
        status_text = "POOR - Major Issues Detected"
        next_steps = "Comprehensive data review required."
    
    print(f"{status_emoji} Overall Status: {status_text}")
    print(f"📈 Combined Score: {avg_score:.1f}/100")
    print(f"🎯 Next Steps: {next_steps}")
    
    print()
    print("🎉 Analysis Complete!")
    print()
    print("💡 What users get:")
    print("   ✅ Quantitative confidence scores (0-100)")
    print("   ✅ Specific issue identification and prioritization")
    print("   ✅ Actionable recommendations for improvement")
    print("   ✅ SEC filing readiness assessment")
    print("   ✅ EPA cross-validation results")
    print("   ✅ Data quality analysis across 5 dimensions")


if __name__ == "__main__":
    asyncio.run(test_agents_simple())