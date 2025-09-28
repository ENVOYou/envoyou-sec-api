"""
Deviation Detector Tool

Advanced deviation detection for emissions data validation.
"""

from typing import Dict, Any, List, Optional
import statistics
import math
from datetime import datetime


class DeviationDetector:
    """Advanced deviation detection for emissions validation."""
    
    def __init__(self):
        self.version = "1.0.0"
        self.thresholds = {
            "minor": 5.0,      # 5% deviation
            "moderate": 15.0,   # 15% deviation
            "significant": 25.0, # 25% deviation
            "critical": 50.0    # 50% deviation
        }
    
    async def detect_deviations(self, emissions_result: Dict[str, Any], 
                              validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Detect and analyze deviations in emissions data."""
        
        deviations = {
            "quantitative_deviations": [],
            "qualitative_deviations": [],
            "statistical_analysis": {},
            "severity_summary": {"critical": 0, "significant": 0, "moderate": 0, "minor": 0},
            "recommendations": []
        }
        
        # Quantitative deviations from validation
        if validation_result.get("quantitative_deviation"):
            quant_devs = self._analyze_quantitative_deviations(
                validation_result["quantitative_deviation"]
            )
            deviations["quantitative_deviations"] = quant_devs
        
        # Qualitative deviations from flags
        qual_devs = self._analyze_qualitative_deviations(
            validation_result.get("flags", [])
        )
        deviations["qualitative_deviations"] = qual_devs
        
        # Statistical analysis
        stats = self._perform_statistical_analysis(emissions_result, validation_result)
        deviations["statistical_analysis"] = stats
        
        # Update severity summary
        all_deviations = deviations["quantitative_deviations"] + deviations["qualitative_deviations"]
        for dev in all_deviations:
            severity = dev.get("severity", "minor")
            deviations["severity_summary"][severity] += 1
        
        # Generate recommendations
        deviations["recommendations"] = self._generate_deviation_recommendations(deviations)
        
        return deviations
    
    def _analyze_quantitative_deviations(self, quantitative_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze quantitative deviations from external data sources."""
        deviations = []
        
        for deviation in quantitative_data.get("deviations", []):
            deviation_pct = deviation.get("deviation_pct", 0)
            severity = self._classify_deviation_severity(deviation_pct)
            
            dev_analysis = {
                "type": "quantitative",
                "pollutant": deviation.get("pollutant"),
                "reported_value": deviation.get("reported"),
                "reference_value": deviation.get("reference"),
                "deviation_percent": deviation_pct,
                "severity": severity,
                "source": deviation.get("source"),
                "threshold_exceeded": deviation_pct > deviation.get("threshold", 15),
                "analysis": {
                    "absolute_difference": abs(deviation.get("reported", 0) - deviation.get("reference", 0)),
                    "relative_magnitude": self._calculate_relative_magnitude(
                        deviation.get("reported", 0), deviation.get("reference", 0)
                    ),
                    "confidence_impact": self._calculate_confidence_impact(deviation_pct, severity)
                }
            }
            
            deviations.append(dev_analysis)
        
        return deviations
    
    def _analyze_qualitative_deviations(self, flags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze qualitative deviations from validation flags."""
        deviations = []
        
        for flag in flags:
            severity = flag.get("severity", "low")
            
            dev_analysis = {
                "type": "qualitative",
                "flag_code": flag.get("code"),
                "message": flag.get("message"),
                "severity": severity,
                "details": flag.get("details", {}),
                "analysis": {
                    "category": self._categorize_flag(flag.get("code", "")),
                    "actionability": self._assess_flag_actionability(flag),
                    "confidence_impact": self._calculate_flag_confidence_impact(severity)
                }
            }
            
            deviations.append(dev_analysis)
        
        return deviations
    
    def _perform_statistical_analysis(self, emissions_result: Dict[str, Any], 
                                    validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical analysis on deviations."""
        
        # Extract quantitative deviations for analysis
        quant_data = validation_result.get("quantitative_deviation", {})
        deviations_pct = [
            dev.get("deviation_pct", 0) 
            for dev in quant_data.get("deviations", [])
        ]
        
        if not deviations_pct:
            return {"status": "no_quantitative_data"}
        
        # Statistical measures
        stats = {
            "count": len(deviations_pct),
            "mean_deviation": statistics.mean(deviations_pct),
            "median_deviation": statistics.median(deviations_pct),
            "max_deviation": max(deviations_pct),
            "min_deviation": min(deviations_pct),
            "std_deviation": statistics.stdev(deviations_pct) if len(deviations_pct) > 1 else 0,
            "outliers": self._detect_statistical_outliers(deviations_pct),
            "distribution_analysis": self._analyze_deviation_distribution(deviations_pct)
        }
        
        return stats
    
    def _classify_deviation_severity(self, deviation_pct: float) -> str:
        """Classify deviation severity based on percentage."""
        if deviation_pct >= self.thresholds["critical"]:
            return "critical"
        elif deviation_pct >= self.thresholds["significant"]:
            return "significant"
        elif deviation_pct >= self.thresholds["moderate"]:
            return "moderate"
        else:
            return "minor"
    
    def _calculate_relative_magnitude(self, reported: float, reference: float) -> str:
        """Calculate relative magnitude of deviation."""
        if reference == 0:
            return "undefined"
        
        ratio = reported / reference
        
        if ratio > 2.0:
            return "much_higher"
        elif ratio > 1.5:
            return "higher"
        elif ratio > 1.1:
            return "slightly_higher"
        elif ratio > 0.9:
            return "similar"
        elif ratio > 0.5:
            return "lower"
        else:
            return "much_lower"
    
    def _calculate_confidence_impact(self, deviation_pct: float, severity: str) -> Dict[str, Any]:
        """Calculate impact on confidence score."""
        impact_scores = {
            "critical": -30,
            "significant": -20,
            "moderate": -10,
            "minor": -5
        }
        
        base_impact = impact_scores.get(severity, -5)
        
        # Additional impact based on deviation percentage
        if deviation_pct > 100:
            additional_impact = -10
        elif deviation_pct > 75:
            additional_impact = -5
        else:
            additional_impact = 0
        
        return {
            "base_impact": base_impact,
            "additional_impact": additional_impact,
            "total_impact": base_impact + additional_impact,
            "description": f"Confidence reduced by {abs(base_impact + additional_impact)} points"
        }
    
    def _categorize_flag(self, flag_code: str) -> str:
        """Categorize validation flag by type."""
        categories = {
            "no_epa_match": "data_availability",
            "low_match_density": "data_quality",
            "state_mismatch": "geographic_consistency",
            "quantitative_deviation": "numerical_accuracy"
        }
        return categories.get(flag_code, "general")
    
    def _assess_flag_actionability(self, flag: Dict[str, Any]) -> Dict[str, Any]:
        """Assess how actionable a flag is."""
        code = flag.get("code", "")
        
        actionability_map = {
            "no_epa_match": {
                "level": "high",
                "actions": ["Verify company name", "Check for subsidiaries", "Manual facility search"]
            },
            "low_match_density": {
                "level": "medium", 
                "actions": ["Expand search criteria", "Check operational locations"]
            },
            "state_mismatch": {
                "level": "high",
                "actions": ["Verify operational state", "Check facility addresses"]
            },
            "quantitative_deviation": {
                "level": "high",
                "actions": ["Verify inputs", "Check calculation method", "Review emission factors"]
            }
        }
        
        return actionability_map.get(code, {
            "level": "medium",
            "actions": ["Review data quality"]
        })
    
    def _calculate_flag_confidence_impact(self, severity: str) -> int:
        """Calculate confidence impact of validation flags."""
        impacts = {
            "critical": -25,
            "high": -15,
            "medium": -10,
            "low": -5
        }
        return impacts.get(severity, -5)
    
    def _detect_statistical_outliers(self, values: List[float]) -> List[Dict[str, Any]]:
        """Detect statistical outliers in deviation data."""
        if len(values) < 3:
            return []
        
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)
        
        outliers = []
        for i, value in enumerate(values):
            z_score = abs(value - mean_val) / std_val if std_val > 0 else 0
            
            if z_score > 2.0:  # 2 standard deviations
                outliers.append({
                    "index": i,
                    "value": value,
                    "z_score": z_score,
                    "severity": "high" if z_score > 3.0 else "medium"
                })
        
        return outliers
    
    def _analyze_deviation_distribution(self, values: List[float]) -> Dict[str, Any]:
        """Analyze the distribution of deviations."""
        if not values:
            return {}
        
        # Categorize deviations by severity
        distribution = {
            "critical": sum(1 for v in values if v >= self.thresholds["critical"]),
            "significant": sum(1 for v in values if self.thresholds["significant"] <= v < self.thresholds["critical"]),
            "moderate": sum(1 for v in values if self.thresholds["moderate"] <= v < self.thresholds["significant"]),
            "minor": sum(1 for v in values if v < self.thresholds["moderate"])
        }
        
        total = len(values)
        distribution_pct = {k: (v/total)*100 for k, v in distribution.items()}
        
        return {
            "counts": distribution,
            "percentages": distribution_pct,
            "pattern": self._identify_deviation_pattern(distribution_pct)
        }
    
    def _identify_deviation_pattern(self, distribution_pct: Dict[str, float]) -> str:
        """Identify the pattern in deviation distribution."""
        critical_pct = distribution_pct.get("critical", 0)
        significant_pct = distribution_pct.get("significant", 0)
        moderate_pct = distribution_pct.get("moderate", 0)
        
        if critical_pct > 50:
            return "critical_dominant"
        elif significant_pct + critical_pct > 60:
            return "high_severity_dominant"
        elif moderate_pct > 50:
            return "moderate_dominant"
        else:
            return "low_severity_dominant"
    
    def _generate_deviation_recommendations(self, deviations: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on deviation analysis."""
        recommendations = []
        
        severity_summary = deviations.get("severity_summary", {})
        stats = deviations.get("statistical_analysis", {})
        
        # Critical deviations
        if severity_summary.get("critical", 0) > 0:
            recommendations.append("🚨 Critical deviations detected - immediate investigation required")
            recommendations.append("Halt SEC filing process until critical issues are resolved")
        
        # Significant deviations
        if severity_summary.get("significant", 0) > 0:
            recommendations.append("⚠️ Significant deviations found - thorough review needed")
        
        # Statistical patterns
        if stats.get("mean_deviation", 0) > 20:
            recommendations.append("📊 High average deviation - review calculation methodology")
        
        if len(stats.get("outliers", [])) > 0:
            recommendations.append("🎯 Statistical outliers detected - investigate anomalous data points")
        
        # Pattern-based recommendations
        pattern = stats.get("distribution_analysis", {}).get("pattern")
        if pattern == "critical_dominant":
            recommendations.append("🔴 Critical deviation pattern - comprehensive data review required")
        elif pattern == "high_severity_dominant":
            recommendations.append("🟡 High-severity deviation pattern - enhanced validation needed")
        
        return recommendations