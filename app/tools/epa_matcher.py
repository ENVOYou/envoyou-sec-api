"""
EPA Matcher Tool

Advanced EPA facility matching and validation.
"""

from typing import Dict, Any, List, Optional
import re
from difflib import SequenceMatcher


class EPAMatcher:
    """Advanced EPA facility matching and validation."""
    
    def __init__(self):
        self.version = "1.0.0"
        self.similarity_threshold = 0.6
    
    async def find_advanced_matches(self, company_name: str, 
                                  state: Optional[str] = None) -> Dict[str, Any]:
        """Find advanced EPA matches using multiple strategies."""
        
        # Normalize company name
        normalized_name = self._normalize_company_name(company_name)
        
        # Multiple matching strategies
        strategies = {
            "exact_match": await self._exact_match_strategy(normalized_name, state),
            "fuzzy_match": await self._fuzzy_match_strategy(normalized_name, state),
            "keyword_match": await self._keyword_match_strategy(normalized_name, state),
            "subsidiary_match": await self._subsidiary_match_strategy(normalized_name, state)
        }
        
        # Combine and rank results
        combined_matches = self._combine_match_results(strategies)
        
        return {
            "company_name": company_name,
            "normalized_name": normalized_name,
            "state_filter": state,
            "strategies": strategies,
            "matches": combined_matches,
            "match_summary": self._create_match_summary(combined_matches)
        }
    
    def _normalize_company_name(self, company_name: str) -> str:
        """Normalize company name for better matching."""
        # Convert to lowercase
        normalized = company_name.lower()
        
        # Remove common suffixes
        suffixes = [
            r'\s+(inc\.?|incorporated)$',
            r'\s+(llc\.?)$', 
            r'\s+(corp\.?|corporation)$',
            r'\s+(ltd\.?|limited)$',
            r'\s+(co\.?)$',
            r'\s+company$'
        ]
        
        for suffix in suffixes:
            normalized = re.sub(suffix, '', normalized)
        
        # Remove special characters
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Normalize whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    async def _exact_match_strategy(self, normalized_name: str, 
                                  state: Optional[str]) -> Dict[str, Any]:
        """Exact match strategy."""
        # This would integrate with actual EPA client
        # For now, return mock structure
        return {
            "strategy": "exact_match",
            "matches": [],
            "confidence": 0.0,
            "notes": "Exact match strategy - highest confidence when found"
        }
    
    async def _fuzzy_match_strategy(self, normalized_name: str, 
                                  state: Optional[str]) -> Dict[str, Any]:
        """Fuzzy matching strategy using string similarity."""
        # Mock EPA data for demonstration
        mock_facilities = [
            {"facility_name": "demo manufacturing corp", "state": "CA", "facility_id": "12345"},
            {"facility_name": "example energy llc", "state": "TX", "facility_id": "67890"}
        ]
        
        matches = []
        for facility in mock_facilities:
            facility_name = self._normalize_company_name(facility["facility_name"])
            similarity = SequenceMatcher(None, normalized_name, facility_name).ratio()
            
            if similarity >= self.similarity_threshold:
                if not state or facility.get("state", "").upper() == state.upper():
                    matches.append({
                        **facility,
                        "similarity_score": similarity,
                        "match_type": "fuzzy"
                    })
        
        # Sort by similarity
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return {
            "strategy": "fuzzy_match",
            "matches": matches,
            "confidence": max([m["similarity_score"] for m in matches]) if matches else 0.0,
            "threshold_used": self.similarity_threshold
        }
    
    async def _keyword_match_strategy(self, normalized_name: str, 
                                    state: Optional[str]) -> Dict[str, Any]:
        """Keyword-based matching strategy."""
        # Extract keywords from company name
        keywords = self._extract_keywords(normalized_name)
        
        # This would search EPA data by keywords
        # Mock implementation
        matches = []
        
        return {
            "strategy": "keyword_match",
            "keywords_used": keywords,
            "matches": matches,
            "confidence": 0.0
        }
    
    async def _subsidiary_match_strategy(self, normalized_name: str, 
                                       state: Optional[str]) -> Dict[str, Any]:
        """Match against known subsidiaries and parent companies."""
        # This would use a database of corporate relationships
        # Mock implementation
        return {
            "strategy": "subsidiary_match",
            "matches": [],
            "confidence": 0.0,
            "notes": "Searches parent companies and subsidiaries"
        }
    
    def _extract_keywords(self, normalized_name: str) -> List[str]:
        """Extract meaningful keywords from company name."""
        # Common stop words to exclude
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
        }
        
        words = normalized_name.split()
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords
    
    def _combine_match_results(self, strategies: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine results from multiple matching strategies."""
        all_matches = []
        
        for strategy_name, strategy_result in strategies.items():
            matches = strategy_result.get("matches", [])
            for match in matches:
                match["strategy"] = strategy_name
                all_matches.append(match)
        
        # Remove duplicates based on facility_id
        unique_matches = {}
        for match in all_matches:
            facility_id = match.get("facility_id")
            if facility_id:
                if facility_id not in unique_matches:
                    unique_matches[facility_id] = match
                else:
                    # Keep the match with higher confidence
                    existing = unique_matches[facility_id]
                    if match.get("similarity_score", 0) > existing.get("similarity_score", 0):
                        unique_matches[facility_id] = match
        
        # Convert back to list and sort by confidence
        final_matches = list(unique_matches.values())
        final_matches.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
        
        return final_matches
    
    def _create_match_summary(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary of matching results."""
        if not matches:
            return {
                "total_matches": 0,
                "confidence_level": "none",
                "recommendation": "No EPA matches found - verify company name"
            }
        
        total_matches = len(matches)
        best_confidence = max(match.get("similarity_score", 0) for match in matches)
        avg_confidence = sum(match.get("similarity_score", 0) for match in matches) / total_matches
        
        # Determine confidence level
        if best_confidence >= 0.9:
            confidence_level = "very_high"
            recommendation = "Excellent EPA matches found - high validation confidence"
        elif best_confidence >= 0.8:
            confidence_level = "high"
            recommendation = "Good EPA matches found - proceed with validation"
        elif best_confidence >= 0.6:
            confidence_level = "medium"
            recommendation = "Moderate EPA matches - review for accuracy"
        else:
            confidence_level = "low"
            recommendation = "Weak EPA matches - manual verification recommended"
        
        # Strategy breakdown
        strategy_counts = {}
        for match in matches:
            strategy = match.get("strategy", "unknown")
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            "total_matches": total_matches,
            "best_confidence": best_confidence,
            "average_confidence": avg_confidence,
            "confidence_level": confidence_level,
            "recommendation": recommendation,
            "strategy_breakdown": strategy_counts,
            "top_match": matches[0] if matches else None
        }