"""
Forensic Analyzer Tool

Forensic-grade data analysis and integrity verification.
"""

import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class ForensicAnalyzer:
    """Forensic-grade analysis for audit trail integrity."""
    
    def __init__(self):
        self.version = "1.0.0"
        self.hash_algorithm = "sha256"
    
    async def analyze_data_lineage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data lineage and create forensic hash."""
        
        # Create deterministic hash of input data
        data_hash = self._create_data_hash(data)
        
        # Analyze data lineage
        lineage = self._trace_data_lineage(data)
        
        # Integrity verification
        integrity = self._verify_data_integrity(data)
        
        return {
            "hash": data_hash,
            "lineage": lineage,
            "integrity": integrity,
            "timestamp": datetime.utcnow().isoformat(),
            "analyzer_version": self.version
        }
    
    async def analyze_audit_integrity(self, audit_entries: List[Any]) -> Dict[str, Any]:
        """Analyze integrity of audit trail entries."""
        
        if not audit_entries:
            return {
                "status": "no_data",
                "integrity_score": 0,
                "issues": ["No audit entries to analyze"]
            }
        
        integrity_checks = []
        issues = []
        
        for entry in audit_entries:
            check_result = self._verify_audit_entry_integrity(entry)
            integrity_checks.append(check_result)
            
            if not check_result["valid"]:
                issues.extend(check_result["issues"])
        
        # Calculate overall integrity score
        valid_entries = sum(1 for check in integrity_checks if check["valid"])
        integrity_score = (valid_entries / len(integrity_checks)) * 100
        
        # Temporal consistency check
        temporal_analysis = self._analyze_temporal_consistency(audit_entries)
        
        return {
            "total_entries": len(audit_entries),
            "valid_entries": valid_entries,
            "integrity_score": round(integrity_score, 2),
            "issues": issues,
            "temporal_analysis": temporal_analysis,
            "detailed_checks": integrity_checks,
            "recommendation": self._get_integrity_recommendation(integrity_score, issues)
        }
    
    def _create_data_hash(self, data: Dict[str, Any]) -> str:
        """Create deterministic hash of data for forensic tracking."""
        # Create a normalized JSON representation
        normalized_data = self._normalize_for_hashing(data)
        json_str = json.dumps(normalized_data, sort_keys=True, separators=(',', ':'))
        
        # Create hash
        hash_obj = hashlib.new(self.hash_algorithm)
        hash_obj.update(json_str.encode('utf-8'))
        
        return hash_obj.hexdigest()
    
    def _normalize_for_hashing(self, data: Any) -> Any:
        """Normalize data structure for consistent hashing."""
        if isinstance(data, dict):
            # Sort keys and recursively normalize values
            return {k: self._normalize_for_hashing(v) for k, v in sorted(data.items())}
        elif isinstance(data, list):
            # Sort lists if they contain comparable items
            try:
                if all(isinstance(item, (str, int, float)) for item in data):
                    return sorted(data)
                else:
                    return [self._normalize_for_hashing(item) for item in data]
            except TypeError:
                return [self._normalize_for_hashing(item) for item in data]
        elif isinstance(data, float):
            # Round floats to avoid precision issues
            return round(data, 6)
        else:
            return data
    
    def _trace_data_lineage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Trace the lineage of data sources and transformations."""
        lineage = {
            "sources": [],
            "transformations": [],
            "dependencies": []
        }
        
        # Identify data sources
        if "scope1" in data:
            lineage["sources"].append({
                "type": "scope1_emissions",
                "fields": list(data["scope1"].keys()) if isinstance(data["scope1"], dict) else []
            })
        
        if "scope2" in data:
            lineage["sources"].append({
                "type": "scope2_emissions", 
                "fields": list(data["scope2"].keys()) if isinstance(data["scope2"], dict) else []
            })
        
        # Identify transformations
        if "calculation_version" in data:
            lineage["transformations"].append({
                "type": "emissions_calculation",
                "version": data["calculation_version"]
            })
        
        # Identify dependencies
        if "emission_factors_source" in data:
            lineage["dependencies"].append({
                "type": "emission_factors",
                "source": data["emission_factors_source"]
            })
        
        return lineage
    
    def _verify_data_integrity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify data integrity and completeness."""
        integrity = {
            "valid": True,
            "issues": [],
            "checks": {}
        }
        
        # Required field checks
        required_fields = ["company"]
        for field in required_fields:
            if field not in data or not data[field]:
                integrity["valid"] = False
                integrity["issues"].append(f"Missing required field: {field}")
        
        integrity["checks"]["required_fields"] = len(integrity["issues"]) == 0
        
        # Data type validation
        type_issues = []
        if "scope1" in data and not isinstance(data["scope1"], dict):
            type_issues.append("scope1 must be a dictionary")
        
        if "scope2" in data and not isinstance(data["scope2"], dict):
            type_issues.append("scope2 must be a dictionary")
        
        if type_issues:
            integrity["valid"] = False
            integrity["issues"].extend(type_issues)
        
        integrity["checks"]["data_types"] = len(type_issues) == 0
        
        # Value range validation
        range_issues = []
        if "scope1" in data and isinstance(data["scope1"], dict):
            amount = data["scope1"].get("amount")
            if amount is not None and (not isinstance(amount, (int, float)) or amount < 0):
                range_issues.append("scope1 amount must be non-negative number")
        
        if "scope2" in data and isinstance(data["scope2"], dict):
            kwh = data["scope2"].get("kwh")
            if kwh is not None and (not isinstance(kwh, (int, float)) or kwh < 0):
                range_issues.append("scope2 kwh must be non-negative number")
        
        if range_issues:
            integrity["valid"] = False
            integrity["issues"].extend(range_issues)
        
        integrity["checks"]["value_ranges"] = len(range_issues) == 0
        
        return integrity
    
    def _verify_audit_entry_integrity(self, entry: Any) -> Dict[str, Any]:
        """Verify integrity of individual audit entry."""
        check_result = {
            "entry_id": getattr(entry, 'id', 'unknown'),
            "valid": True,
            "issues": []
        }
        
        # Check required fields
        required_attrs = ['company', 'timestamp', 'inputs', 'outputs']
        for attr in required_attrs:
            if not hasattr(entry, attr) or getattr(entry, attr) is None:
                check_result["valid"] = False
                check_result["issues"].append(f"Missing {attr}")
        
        # Check data consistency
        if hasattr(entry, 'inputs') and hasattr(entry, 'outputs'):
            inputs = entry.inputs
            outputs = entry.outputs
            
            if inputs and outputs:
                # Verify company consistency
                input_company = inputs.get("company") if isinstance(inputs, dict) else None
                output_company = outputs.get("company") if isinstance(outputs, dict) else None
                
                if input_company and output_company and input_company != output_company:
                    check_result["valid"] = False
                    check_result["issues"].append("Company mismatch between inputs and outputs")
        
        # Check timestamp validity
        if hasattr(entry, 'timestamp'):
            try:
                timestamp = entry.timestamp
                if timestamp > datetime.utcnow():
                    check_result["valid"] = False
                    check_result["issues"].append("Future timestamp detected")
            except Exception:
                check_result["valid"] = False
                check_result["issues"].append("Invalid timestamp format")
        
        return check_result
    
    def _analyze_temporal_consistency(self, audit_entries: List[Any]) -> Dict[str, Any]:
        """Analyze temporal consistency of audit entries."""
        if len(audit_entries) < 2:
            return {"status": "insufficient_data"}
        
        timestamps = []
        for entry in audit_entries:
            if hasattr(entry, 'timestamp'):
                timestamps.append(entry.timestamp)
        
        if not timestamps:
            return {"status": "no_timestamps"}
        
        # Sort timestamps
        timestamps.sort()
        
        # Check for temporal anomalies
        anomalies = []
        for i in range(1, len(timestamps)):
            time_diff = (timestamps[i] - timestamps[i-1]).total_seconds()
            
            # Flag very rapid entries (less than 1 second apart)
            if time_diff < 1:
                anomalies.append({
                    "type": "rapid_entries",
                    "time_diff": time_diff,
                    "entries": [i-1, i]
                })
            
            # Flag very large gaps (more than 30 days)
            if time_diff > 30 * 24 * 3600:
                anomalies.append({
                    "type": "large_gap",
                    "time_diff": time_diff,
                    "entries": [i-1, i]
                })
        
        return {
            "total_entries": len(timestamps),
            "time_span": {
                "start": timestamps[0].isoformat(),
                "end": timestamps[-1].isoformat(),
                "duration_days": (timestamps[-1] - timestamps[0]).days
            },
            "anomalies": anomalies,
            "consistency_score": max(0, 100 - len(anomalies) * 10)
        }
    
    def _get_integrity_recommendation(self, integrity_score: float, 
                                    issues: List[str]) -> str:
        """Get recommendation based on integrity analysis."""
        if integrity_score >= 95:
            return "Excellent integrity - audit trail is forensically sound"
        elif integrity_score >= 85:
            return "Good integrity - minor issues detected but acceptable for SEC filing"
        elif integrity_score >= 70:
            return "Fair integrity - address issues before SEC filing"
        else:
            return "Poor integrity - significant remediation required before SEC filing"