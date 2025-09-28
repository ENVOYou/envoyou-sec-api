"""
Anomaly Detector Tool

Advanced anomaly detection for emissions data.
"""

from typing import Dict, Any, List, Optional, Tuple
import statistics
import math
from datetime import datetime


class AnomalyDetector:
    """Advanced anomaly detection for emissions data validation."""
    
    def __init__(self):
        self.version = "1.0.0"
        self.thresholds = {
            "z_score": 2.0,        # Standard deviations for outlier detection
            "iqr_multiplier": 1.5,  # IQR multiplier for outlier detection
            "magnitude_ratio": 10.0  # Ratio threshold for magnitude anomalies
        }
    
    async def detect_anomalies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in emissions data."""
        
        anomalies = {
            "detected": [],
            "summary": {
                "total_anomalies": 0,
                "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "by_type": {}
            },
            "analysis": {}
        }
        
        # Value range anomalies
        range_anomalies = self._detect_range_anomalies(data)
        anomalies["detected"].extend(range_anomalies)
        
        # Magnitude anomalies
        magnitude_anomalies = self._detect_magnitude_anomalies(data)
        anomalies["detected"].extend(magnitude_anomalies)
        
        # Pattern anomalies
        pattern_anomalies = self._detect_pattern_anomalies(data)
        anomalies["detected"].extend(pattern_anomalies)
        
        # Business rule anomalies
        business_anomalies = self._detect_business_rule_anomalies(data)
        anomalies["detected"].extend(business_anomalies)
        
        # Statistical anomalies (if historical data available)
        statistical_anomalies = self._detect_statistical_anomalies(data)
        anomalies["detected"].extend(statistical_anomalies)
        
        # Update summary
        self._update_anomaly_summary(anomalies)
        
        # Generate analysis
        anomalies["analysis"] = self._analyze_anomaly_patterns(anomalies["detected"])
        
        return anomalies
    
    def _detect_range_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect values outside expected ranges."""
        anomalies = []
        
        # Scope 1 range checks
        if data.get("scope1"):
            scope1 = data["scope1"]
            amount = scope1.get("amount")
            
            if amount is not None:
                # Extremely high values
                if amount > 1000000:  # 1 million units
                    anomalies.append({
                        "type": "range_anomaly",
                        "severity": "high",
                        "field": "scope1.amount",
                        "value": amount,
                        "description": "Extremely high Scope 1 amount",
                        "threshold": 1000000,
                        "recommendation": "Verify unit and calculation method"
                    })
                
                # Suspiciously round numbers
                if amount > 1000 and amount % 1000 == 0:
                    anomalies.append({
                        "type": "pattern_anomaly",
                        "severity": "low",
                        "field": "scope1.amount",
                        "value": amount,
                        "description": "Suspiciously round number",
                        "recommendation": "Verify if this is an estimate or actual measurement"
                    })
        
        # Scope 2 range checks
        if data.get("scope2"):
            scope2 = data["scope2"]
            kwh = scope2.get("kwh")
            
            if kwh is not None:
                # Extremely high values
                if kwh > 100000000:  # 100 million kWh
                    anomalies.append({
                        "type": "range_anomaly",
                        "severity": "high",
                        "field": "scope2.kwh",
                        "value": kwh,
                        "description": "Extremely high kWh consumption",
                        "threshold": 100000000,
                        "recommendation": "Verify consumption data and units"
                    })
                
                # Suspiciously low values for large companies
                company = data.get("company", "").lower()
                if any(word in company for word in ["corp", "corporation", "inc"]) and kwh < 1000:
                    anomalies.append({
                        "type": "magnitude_anomaly",
                        "severity": "medium",
                        "field": "scope2.kwh",
                        "value": kwh,
                        "description": "Unusually low electricity consumption for corporation",
                        "recommendation": "Verify if this covers all facilities"
                    })
        
        return anomalies
    
    def _detect_magnitude_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect magnitude-related anomalies."""
        anomalies = []
        
        # Compare Scope 1 and Scope 2 magnitudes
        scope1_amount = 0
        scope2_kwh = 0
        
        if data.get("scope1"):
            scope1_amount = data["scope1"].get("amount", 0)
        
        if data.get("scope2"):
            scope2_kwh = data["scope2"].get("kwh", 0)
        
        if scope1_amount > 0 and scope2_kwh > 0:
            # Very rough conversion for comparison (this would be more sophisticated)
            # Convert scope1 to approximate energy equivalent
            fuel_type = data.get("scope1", {}).get("fuel_type", "")
            
            # Rough energy content estimates (BTU per unit)
            energy_content = {
                "gasoline": 120000,  # BTU per gallon
                "diesel": 138000,    # BTU per gallon
                "natural_gas": 100000  # BTU per therm (varies by unit)
            }
            
            if fuel_type in energy_content:
                scope1_energy_btu = scope1_amount * energy_content[fuel_type]
                scope2_energy_btu = scope2_kwh * 3412  # kWh to BTU conversion
                
                if scope2_energy_btu > 0:
                    ratio = scope1_energy_btu / scope2_energy_btu
                    
                    if ratio > self.thresholds["magnitude_ratio"]:
                        anomalies.append({
                            "type": "magnitude_anomaly",
                            "severity": "medium",
                            "field": "scope1_vs_scope2",
                            "value": ratio,
                            "description": f"Scope 1 energy much higher than Scope 2 (ratio: {ratio:.1f})",
                            "recommendation": "Verify if all energy sources are properly categorized"
                        })
                    elif ratio < (1 / self.thresholds["magnitude_ratio"]):
                        anomalies.append({
                            "type": "magnitude_anomaly",
                            "severity": "medium",
                            "field": "scope1_vs_scope2",
                            "value": ratio,
                            "description": f"Scope 2 energy much higher than Scope 1 (ratio: {1/ratio:.1f})",
                            "recommendation": "Verify energy consumption patterns"
                        })
        
        return anomalies
    
    def _detect_pattern_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect pattern-based anomalies."""
        anomalies = []
        
        # Check for repeated digits
        if data.get("scope1", {}).get("amount"):
            amount_str = str(data["scope1"]["amount"])
            if len(set(amount_str.replace(".", ""))) <= 2 and len(amount_str) > 3:
                anomalies.append({
                    "type": "pattern_anomaly",
                    "severity": "low",
                    "field": "scope1.amount",
                    "value": data["scope1"]["amount"],
                    "description": "Repeated digit pattern detected",
                    "recommendation": "Verify if this is actual data or placeholder"
                })
        
        # Check for sequential numbers
        if data.get("scope2", {}).get("kwh"):
            kwh_str = str(int(data["scope2"]["kwh"]))
            if len(kwh_str) >= 4:
                # Check for sequential digits
                sequential = True
                for i in range(len(kwh_str) - 1):
                    if int(kwh_str[i+1]) != (int(kwh_str[i]) + 1) % 10:
                        sequential = False
                        break
                
                if sequential:
                    anomalies.append({
                        "type": "pattern_anomaly",
                        "severity": "medium",
                        "field": "scope2.kwh",
                        "value": data["scope2"]["kwh"],
                        "description": "Sequential digit pattern detected",
                        "recommendation": "Verify if this is actual consumption data"
                    })
        
        return anomalies
    
    def _detect_business_rule_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect business rule violations."""
        anomalies = []
        
        # Check for missing complementary data
        has_scope1 = bool(data.get("scope1"))
        has_scope2 = bool(data.get("scope2"))
        
        if has_scope1 and not has_scope2:
            anomalies.append({
                "type": "business_rule_anomaly",
                "severity": "medium",
                "field": "scope2",
                "description": "Scope 1 data present but no Scope 2 data",
                "recommendation": "Most companies have both direct and indirect emissions"
            })
        
        if has_scope2 and not has_scope1:
            anomalies.append({
                "type": "business_rule_anomaly",
                "severity": "low",
                "field": "scope1",
                "description": "Scope 2 data present but no Scope 1 data",
                "recommendation": "Verify if company has any direct emissions sources"
            })
        
        # Industry-specific checks (simplified)
        company_name = data.get("company", "").lower()
        
        # Manufacturing companies should typically have both scopes
        if any(word in company_name for word in ["manufacturing", "factory", "plant"]):
            if not (has_scope1 and has_scope2):
                anomalies.append({
                    "type": "business_rule_anomaly",
                    "severity": "medium",
                    "field": "emissions_completeness",
                    "description": "Manufacturing company missing expected emission scopes",
                    "recommendation": "Manufacturing typically has both direct and indirect emissions"
                })
        
        return anomalies
    
    def _detect_statistical_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect statistical anomalies (requires historical data)."""
        # This would compare against historical data or industry benchmarks
        # For now, return empty list as we don't have historical context
        return []
    
    def _update_anomaly_summary(self, anomalies: Dict[str, Any]):
        """Update anomaly summary statistics."""
        detected = anomalies["detected"]
        summary = anomalies["summary"]
        
        summary["total_anomalies"] = len(detected)
        
        # Count by severity
        for anomaly in detected:
            severity = anomaly.get("severity", "low")
            summary["by_severity"][severity] += 1
        
        # Count by type
        for anomaly in detected:
            anomaly_type = anomaly.get("type", "unknown")
            if anomaly_type not in summary["by_type"]:
                summary["by_type"][anomaly_type] = 0
            summary["by_type"][anomaly_type] += 1
    
    def _analyze_anomaly_patterns(self, detected_anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in detected anomalies."""
        if not detected_anomalies:
            return {"status": "no_anomalies"}
        
        # Severity distribution
        severity_counts = {}
        for anomaly in detected_anomalies:
            severity = anomaly.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Field distribution
        field_counts = {}
        for anomaly in detected_anomalies:
            field = anomaly.get("field", "unknown")
            field_counts[field] = field_counts.get(field, 0) + 1
        
        # Risk assessment
        critical_count = severity_counts.get("critical", 0)
        high_count = severity_counts.get("high", 0)
        
        if critical_count > 0:
            risk_level = "critical"
            risk_message = "Critical anomalies detected - immediate attention required"
        elif high_count > 2:
            risk_level = "high"
            risk_message = "Multiple high-severity anomalies - thorough review needed"
        elif high_count > 0:
            risk_level = "medium"
            risk_message = "High-severity anomalies detected - review recommended"
        else:
            risk_level = "low"
            risk_message = "Minor anomalies detected - monitoring recommended"
        
        return {
            "severity_distribution": severity_counts,
            "field_distribution": field_counts,
            "risk_assessment": {
                "level": risk_level,
                "message": risk_message
            },
            "most_affected_field": max(field_counts.items(), key=lambda x: x[1])[0] if field_counts else None,
            "recommendations": self._generate_anomaly_recommendations(detected_anomalies)
        }
    
    def _generate_anomaly_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on detected anomalies."""
        recommendations = []
        
        # Count anomalies by type and severity
        critical_anomalies = [a for a in anomalies if a.get("severity") == "critical"]
        high_anomalies = [a for a in anomalies if a.get("severity") == "high"]
        range_anomalies = [a for a in anomalies if a.get("type") == "range_anomaly"]
        pattern_anomalies = [a for a in anomalies if a.get("type") == "pattern_anomaly"]
        
        if critical_anomalies:
            recommendations.append("🚨 Critical anomalies detected - halt processing until resolved")
        
        if high_anomalies:
            recommendations.append("⚠️ High-severity anomalies require immediate investigation")
        
        if range_anomalies:
            recommendations.append("📊 Value range anomalies detected - verify data accuracy")
        
        if pattern_anomalies:
            recommendations.append("🔍 Pattern anomalies suggest potential data quality issues")
        
        if len(anomalies) > 5:
            recommendations.append("📋 Multiple anomalies detected - comprehensive data review recommended")
        
        return recommendations