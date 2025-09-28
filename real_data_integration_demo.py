#!/usr/bin/env python3
"""
Demo: How Agents Access Real EPA Data
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.clients.global_client import EPAClient
from app.clients.campd_client import CAMDClient


async def demo_real_data_access():
    """Demonstrate how agents access real EPA data."""
    
    print("🌐 REAL DATA INTEGRATION DEMO")
    print("=" * 40)
    print()
    
    # 1. EPA Envirofacts Data
    print("📊 1. EPA ENVIROFACTS DATA ACCESS")
    print("-" * 35)
    
    epa_client = EPAClient()
    
    # Get real EPA facility data for California
    print("🔍 Fetching real EPA facilities in California...")
    ca_facilities = epa_client.get_emissions_data(region="CA", limit=5)
    
    print(f"✅ Found {len(ca_facilities)} facilities")
    if ca_facilities:
        print("📋 Sample facilities:")
        for i, facility in enumerate(ca_facilities[:3], 1):
            name = facility.get("facility_name", "Unknown")
            state = facility.get("state", "N/A")
            county = facility.get("county", "N/A")
            print(f"   {i}. {name} ({state}, {county})")
    
    print()
    
    # 2. CAMPD Data (if API key available)
    print("🏭 2. EPA CAMPD DATA ACCESS")
    print("-" * 28)
    
    campd_client = CAMDClient()
    
    if campd_client.api_key:
        print("🔍 Fetching real CAMPD emissions data...")
        # Example facility ID (would be from mapping)
        facility_id = 3  # Sample facility ID
        emissions_data = campd_client.get_emissions_data(facility_id=facility_id, year=2023)
        
        if emissions_data:
            print(f"✅ Found emissions data for facility {facility_id}")
            print("📊 Sample emissions record:")
            sample = emissions_data[0] if emissions_data else {}
            co2_mass = sample.get("co2_mass_tons", "N/A")
            nox_mass = sample.get("nox_mass_lbs", "N/A")
            print(f"   • CO2: {co2_mass} tons")
            print(f"   • NOx: {nox_mass} lbs")
        else:
            print("⚠️ No emissions data found for sample facility")
    else:
        print("⚠️ CAMPD API key not configured - using mock data")
    
    print()
    
    # 3. How Agents Use This Data
    print("🤖 3. HOW AGENTS USE REAL DATA")
    print("-" * 32)
    
    print("📋 EPA Validation Agent Process:")
    print("   1. User submits: 'Tesla Manufacturing Corp'")
    print("   2. Agent calls EPA API: Search facilities containing 'Tesla'")
    print("   3. Agent gets real EPA data: Facility matches")
    print("   4. Agent analyzes: Match quality and confidence")
    print("   5. Agent returns: Quantified confidence score")
    
    print()
    print("📊 Data Quality Agent Process:")
    print("   1. User submits emissions data")
    print("   2. Agent validates against EPA standards")
    print("   3. Agent checks data ranges vs. real industry data")
    print("   4. Agent detects anomalies using EPA benchmarks")
    print("   5. Agent returns: Quality scores and recommendations")
    
    print()
    print("🏛️ SEC Compliance Agent Process:")
    print("   1. Agent orchestrates full workflow")
    print("   2. Agent calls EPA validation with real data")
    print("   3. Agent performs quantitative deviation analysis")
    print("   4. Agent generates SEC package with EPA references")
    print("   5. Agent creates audit trail with data sources")
    
    print()
    
    # 4. Real Data Benefits
    print("✅ 4. REAL DATA BENEFITS")
    print("-" * 25)
    
    benefits = [
        "🎯 **Accurate Validation**: Cross-check against actual EPA facilities",
        "📊 **Quantitative Analysis**: Compare emissions with real CAMPD data", 
        "🔍 **Anomaly Detection**: Detect outliers using real industry benchmarks",
        "📋 **Compliance Verification**: Validate against actual regulatory data",
        "🏛️ **SEC Readiness**: Reference real EPA data in filing packages",
        "⚡ **Live Updates**: Always use current EPA datasets",
        "🔒 **Audit Trail**: Document real data sources for compliance"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
    
    print()
    
    # 5. Data Sources Summary
    print("📚 5. DATA SOURCES INTEGRATED")
    print("-" * 31)
    
    sources = {
        "EPA Envirofacts": {
            "url": "https://data.epa.gov/efservice",
            "data": "Facility registry, TRI data",
            "usage": "Facility matching, presence validation"
        },
        "EPA CAMPD": {
            "url": "EPA Clean Air Markets API", 
            "data": "Power plant emissions (CO2, NOx, SO2)",
            "usage": "Quantitative deviation analysis"
        },
        "EPA TRI": {
            "url": "Toxic Release Inventory",
            "data": "Industrial facility information",
            "usage": "Cross-validation, compliance checking"
        }
    }
    
    for source, info in sources.items():
        print(f"   📊 **{source}**")
        print(f"      • URL: {info['url']}")
        print(f"      • Data: {info['data']}")
        print(f"      • Usage: {info['usage']}")
        print()
    
    print("🎉 AGENTS PROVIDE REAL-WORLD VALIDATION!")
    print("   • Not just theoretical analysis")
    print("   • Actual EPA data integration")
    print("   • Live government dataset access")
    print("   • Forensic-grade audit trails")


if __name__ == "__main__":
    asyncio.run(demo_real_data_access())