"""
Fallback Data Sources

Multiple data source strategies when primary EPA APIs fail.
Ensures agents always have data to work with for continuous operation.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)


class FallbackDataManager:
    """Manages fallback data sources when EPA APIs are unavailable."""
    
    def __init__(self):
        self.cache_dir = "data/cache"
        self.backup_data_dir = "data/backup"
        self.ensure_directories()
        
    def ensure_directories(self):
        """Ensure cache and backup directories exist."""
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.backup_data_dir, exist_ok=True)
    
    async def get_fallback_facilities(self, company: str, 
                                    state: Optional[str] = None) -> Dict[str, Any]:
        """
        Get facility data using fallback strategies when EPA APIs fail.
        
        Fallback order:
        1. Recent cache (< 24 hours)
        2. Older cache (< 7 days) 
        3. Backup static data
        4. Intelligent sample generation
        """
        
        # Strategy 1: Recent cache
        recent_cache = await self._get_recent_cache(company, state)
        if recent_cache:
            logger.info("Using recent cached EPA data")
            return {
                "facilities": recent_cache,
                "source": "RECENT_CACHE",
                "confidence_impact": 0,  # No confidence penalty
                "note": "Recent cached EPA data (< 24 hours)"
            }
        
        # Strategy 2: Older cache
        older_cache = await self._get_older_cache(company, state)
        if older_cache:
            logger.info("Using older cached EPA data")
            return {
                "facilities": older_cache,
                "source": "OLDER_CACHE", 
                "confidence_impact": -5,  # Small confidence penalty
                "note": "Older cached EPA data (< 7 days)"
            }
        
        # Strategy 3: Backup static data
        backup_data = await self._get_backup_data(company, state)
        if backup_data:
            logger.info("Using backup static EPA data")
            return {
                "facilities": backup_data,
                "source": "BACKUP_DATA",
                "confidence_impact": -10,  # Medium confidence penalty
                "note": "Backup EPA data from static sources"
            }
        
        # Strategy 4: Intelligent sample generation
        sample_data = await self._generate_intelligent_sample(company, state)
        logger.warning("All fallback sources exhausted, using intelligent sample")
        return {
            "facilities": sample_data,
            "source": "INTELLIGENT_SAMPLE",
            "confidence_impact": -20,  # Higher confidence penalty
            "note": "Intelligent sample data - EPA APIs unavailable"
        }
    
    async def _get_recent_cache(self, company: str, 
                              state: Optional[str]) -> Optional[List[Dict[str, Any]]]:
        """Get recently cached EPA data (< 24 hours)."""
        
        cache_key = self._generate_cache_key(company, state)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        # Check if cache is recent (< 24 hours)
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if file_age > timedelta(hours=24):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                return cached_data.get("facilities", [])
        except Exception as e:
            logger.error(f"Error reading recent cache: {e}")
            return None
    
    async def _get_older_cache(self, company: str, 
                             state: Optional[str]) -> Optional[List[Dict[str, Any]]]:
        """Get older cached EPA data (< 7 days)."""
        
        cache_key = self._generate_cache_key(company, state)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        # Check if cache is not too old (< 7 days)
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if file_age > timedelta(days=7):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                return cached_data.get("facilities", [])
        except Exception as e:
            logger.error(f"Error reading older cache: {e}")
            return None
    
    async def _get_backup_data(self, company: str, 
                             state: Optional[str]) -> Optional[List[Dict[str, Any]]]:
        """Get backup static EPA data."""
        
        # Load backup data by state or general backup
        backup_files = [
            f"epa_facilities_{state.lower()}.json" if state else None,
            "epa_facilities_major.json",
            "epa_facilities_backup.json"
        ]
        
        for backup_file in backup_files:
            if not backup_file:
                continue
                
            backup_path = os.path.join(self.backup_data_dir, backup_file)
            if not os.path.exists(backup_path):
                continue
            
            try:
                with open(backup_path, 'r') as f:
                    backup_data = json.load(f)
                    facilities = backup_data.get("facilities", [])
                    
                    # Filter by company name
                    filtered = self._filter_facilities_by_company(facilities, company)
                    if filtered:
                        return filtered
                        
            except Exception as e:
                logger.error(f"Error reading backup data {backup_file}: {e}")
                continue
        
        return None
    
    async def _generate_intelligent_sample(self, company: str, 
                                         state: Optional[str]) -> List[Dict[str, Any]]:
        """Generate intelligent sample data based on company characteristics."""
        
        company_lower = company.lower()
        
        # Industry classification
        industry_keywords = {
            "manufacturing": ["manufacturing", "factory", "plant", "production", "assembly"],
            "energy": ["energy", "power", "electric", "utility", "generation"],
            "chemical": ["chemical", "petrochemical", "refinery", "oil", "gas"],
            "automotive": ["automotive", "auto", "motor", "vehicle", "car"],
            "aerospace": ["aerospace", "aircraft", "aviation", "boeing", "airbus"],
            "technology": ["tech", "technology", "software", "data", "computer"]
        }
        
        detected_industry = "general"
        for industry, keywords in industry_keywords.items():
            if any(keyword in company_lower for keyword in keywords):
                detected_industry = industry
                break
        
        # Generate sample facilities based on industry
        sample_facilities = []
        
        if detected_industry == "manufacturing":
            sample_facilities = [
                {
                    "facility_name": f"{company} Manufacturing Plant",
                    "state": state or "OH",
                    "county": "Manufacturing County",
                    "city": "Industrial City",
                    "industry_type": "Manufacturing",
                    "estimated_emissions": "Medium",
                    "source": "INTELLIGENT_SAMPLE"
                },
                {
                    "facility_name": f"{company} Assembly Facility",
                    "state": state or "MI", 
                    "county": "Assembly County",
                    "city": "Production City",
                    "industry_type": "Manufacturing",
                    "estimated_emissions": "Medium",
                    "source": "INTELLIGENT_SAMPLE"
                }
            ]
        
        elif detected_industry == "energy":
            sample_facilities = [
                {
                    "facility_name": f"{company} Power Plant",
                    "state": state or "TX",
                    "county": "Energy County", 
                    "city": "Power City",
                    "industry_type": "Energy Generation",
                    "estimated_emissions": "High",
                    "source": "INTELLIGENT_SAMPLE"
                }
            ]
        
        elif detected_industry == "chemical":
            sample_facilities = [
                {
                    "facility_name": f"{company} Chemical Plant",
                    "state": state or "LA",
                    "county": "Chemical County",
                    "city": "Refinery City", 
                    "industry_type": "Chemical Processing",
                    "estimated_emissions": "High",
                    "source": "INTELLIGENT_SAMPLE"
                }
            ]
        
        else:
            # General/unknown industry
            sample_facilities = [
                {
                    "facility_name": f"{company} Facility",
                    "state": state or "CA",
                    "county": "Business County",
                    "city": "Corporate City",
                    "industry_type": "General Business",
                    "estimated_emissions": "Low",
                    "source": "INTELLIGENT_SAMPLE"
                }
            ]
        
        # Add metadata to all facilities
        for facility in sample_facilities:
            facility.update({
                "confidence_note": "Sample data generated due to EPA API unavailability",
                "generated_at": datetime.now().isoformat(),
                "company_matched": company,
                "fallback_reason": "EPA APIs unavailable"
            })
        
        return sample_facilities
    
    def _generate_cache_key(self, company: str, state: Optional[str]) -> str:
        """Generate cache key for company and state combination."""
        
        company_clean = "".join(c.lower() for c in company if c.isalnum())
        state_part = f"_{state.lower()}" if state else ""
        return f"epa_{company_clean}{state_part}"
    
    def _filter_facilities_by_company(self, facilities: List[Dict[str, Any]], 
                                    company: str) -> List[Dict[str, Any]]:
        """Filter facilities by company name with fuzzy matching."""
        
        company_lower = company.lower()
        company_words = set(word for word in company_lower.split() if len(word) > 2)
        
        filtered = []
        for facility in facilities:
            facility_name = str(facility.get("facility_name", "")).lower()
            
            # Exact match
            if company_lower in facility_name:
                filtered.append(facility)
                continue
            
            # Word matching
            facility_words = set(facility_name.split())
            if len(company_words.intersection(facility_words)) >= 2:
                filtered.append(facility)
        
        return filtered
    
    async def cache_epa_data(self, company: str, state: Optional[str], 
                           facilities: List[Dict[str, Any]]) -> bool:
        """Cache EPA data for future fallback use."""
        
        cache_key = self._generate_cache_key(company, state)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        cache_data = {
            "company": company,
            "state": state,
            "facilities": facilities,
            "cached_at": datetime.now().isoformat(),
            "source": "EPA_API"
        }
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error caching EPA data: {e}")
            return False
    
    async def get_fallback_status(self) -> Dict[str, Any]:
        """Get status of fallback data sources."""
        
        cache_files = len([f for f in os.listdir(self.cache_dir) if f.endswith('.json')])
        backup_files = len([f for f in os.listdir(self.backup_data_dir) if f.endswith('.json')])
        
        return {
            "cache_files_available": cache_files,
            "backup_files_available": backup_files,
            "cache_directory": self.cache_dir,
            "backup_directory": self.backup_data_dir,
            "fallback_strategies": [
                "Recent cache (< 24 hours)",
                "Older cache (< 7 days)", 
                "Backup static data",
                "Intelligent sample generation"
            ]
        }


def fetch_us_emissions_data(source: Optional[str] = None, state: Optional[str] = None,
                            year: Optional[int] = None, pollutant: Optional[str] = None,
                            limit: int = 100) -> Dict[str, Any]:
    """Compatibility wrapper expected by routes.global_data.

    This function provides a synchronous interface that returns a dict with keys:
      - data: List[records]
      - source: string identifying which fallback was used

    It leverages FallbackDataManager's async methods internally but exposes a sync API
    because some routes import and call it synchronously during module import / request handling.
    """
    manager = FallbackDataManager()

    # Use a new event loop to run the async fallback lookup synchronously
    import asyncio

    async def _fetch():
        # Attempt to get fallback facilities (this returns structured data with 'facilities')
        result = await manager.get_fallback_facilities(company=state or "unknown", state=state)
        # Normalize to a simple list under 'data'
        facilities = result.get('facilities', [])
        return {
            'data': facilities[:limit],
            'source': result.get('source', 'fallback')
        }

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_fetch())
    finally:
        try:
            loop.close()
        except Exception:
            pass

    return result