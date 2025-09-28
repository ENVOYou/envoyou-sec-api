"""
Resilient EPA Client

Advanced EPA client with multiple fallback strategies, retry logic, 
and automatic URL switching for handling EPA API instability.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import settings

logger = logging.getLogger(__name__)


class ResilientEPAClient:
    """EPA client with advanced error handling and fallback mechanisms."""
    
    def __init__(self):
        self.primary_endpoints = [
            "https://data.epa.gov/efservice",
            "https://enviro.epa.gov/efservice", 
            "https://iaspub.epa.gov/efservice"
        ]
        
        self.backup_endpoints = [
            "https://echo.epa.gov/efservice",
            "https://www3.epa.gov/efservice"
        ]
        
        self.current_endpoint_index = 0
        self.endpoint_health = {}
        self.last_health_check = {}
        
        # Setup session with retry strategy
        self.session = self._create_resilient_session()
        
    def _create_resilient_session(self) -> requests.Session:
        """Create session with advanced retry and timeout configuration."""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers
        session.headers.update({
            "Accept": "application/json",
            "User-Agent": f"Envoyou-SEC-API/1.0 (+{settings.GITHUB_REPO_URL})",
            "Cache-Control": "no-cache"
        })
        
        return session
    
    async def get_facilities_with_fallback(self, company: str, state: Optional[str] = None, 
                                         limit: int = 100) -> Tuple[List[Dict[str, Any]], str]:
        """
        Get EPA facilities with comprehensive fallback strategy.
        Returns (data, source) tuple.
        """
        
        # Strategy 1: Try primary endpoints
        for endpoint in self.primary_endpoints:
            try:
                data = await self._fetch_from_endpoint(endpoint, company, state, limit)
                if data:
                    logger.info(f"Successfully fetched data from primary endpoint: {endpoint}")
                    return data, f"EPA_PRIMARY_{endpoint}"
            except Exception as e:
                logger.warning(f"Primary endpoint {endpoint} failed: {e}")
                continue
        
        # Strategy 2: Try backup endpoints
        for endpoint in self.backup_endpoints:
            try:
                data = await self._fetch_from_endpoint(endpoint, company, state, limit)
                if data:
                    logger.info(f"Successfully fetched data from backup endpoint: {endpoint}")
                    return data, f"EPA_BACKUP_{endpoint}"
            except Exception as e:
                logger.warning(f"Backup endpoint {endpoint} failed: {e}")
                continue
        
        # Strategy 3: Try alternative EPA services
        try:
            data = await self._fetch_from_alternative_services(company, state, limit)
            if data:
                return data, "EPA_ALTERNATIVE_SERVICE"
        except Exception as e:
            logger.warning(f"Alternative EPA services failed: {e}")
        
        # Strategy 4: Use cached data if available
        cached_data = await self._get_cached_data(company, state)
        if cached_data:
            logger.info("Using cached EPA data due to API failures")
            return cached_data, "EPA_CACHED_DATA"
        
        # Strategy 5: Use high-quality sample data
        sample_data = self._get_intelligent_sample_data(company, state)
        logger.warning("All EPA endpoints failed, using intelligent sample data")
        return sample_data, "EPA_SAMPLE_DATA"
    
    async def _fetch_from_endpoint(self, base_url: str, company: str, 
                                 state: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Fetch data from specific EPA endpoint with multiple URL formats."""
        
        # Try different URL formats for the same endpoint
        url_formats = [
            f"{base_url}/tri_facility/PRIMARY_NAME/CONTAINING/{company}/JSON",
            f"{base_url}/tri_facility/FACILITY_NAME/CONTAINING/{company}/JSON",
            f"{base_url}/FRS_FACILITY_SITE/PRIMARY_NAME/CONTAINING/{company}/JSON"
        ]
        
        if state:
            url_formats.extend([
                f"{base_url}/tri_facility/STATE_ABBR/{state}/PRIMARY_NAME/CONTAINING/{company}/JSON",
                f"{base_url}/tri_facility/STATE_ABBR/{state}/rows/0:{limit-1}/JSON"
            ])
        
        for url_format in url_formats:
            try:
                response = await asyncio.to_thread(
                    self.session.get, url_format, timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and data:
                        # Filter results by company name if needed
                        filtered_data = self._filter_by_company(data, company)
                        if filtered_data:
                            return filtered_data[:limit]
                
            except Exception as e:
                logger.debug(f"URL format {url_format} failed: {e}")
                continue
        
        return []
    
    async def _fetch_from_alternative_services(self, company: str, 
                                             state: Optional[str], 
                                             limit: int) -> List[Dict[str, Any]]:
        """Try alternative EPA services and data sources."""
        
        alternative_sources = [
            self._try_epa_echo_api,
            self._try_epa_frs_api,
            self._try_epa_tri_api
        ]
        
        for source_func in alternative_sources:
            try:
                data = await source_func(company, state, limit)
                if data:
                    return data
            except Exception as e:
                logger.debug(f"Alternative source {source_func.__name__} failed: {e}")
                continue
        
        return []
    
    async def _try_epa_echo_api(self, company: str, state: Optional[str], 
                              limit: int) -> List[Dict[str, Any]]:
        """Try EPA ECHO (Enforcement and Compliance History Online) API."""
        
        echo_urls = [
            "https://echo.epa.gov/efservice/echo_rest_services.get_facilities",
            "https://echo.epa.gov/efservice/get_facilities"
        ]
        
        params = {
            "output": "JSON",
            "qcolumns": "1,2,3,4,5",
            "p_fn": company,
            "rows": limit
        }
        
        if state:
            params["p_st"] = state
        
        for url in echo_urls:
            try:
                response = await asyncio.to_thread(
                    self.session.get, url, params=params, timeout=20
                )
                
                if response.status_code == 200:
                    data = response.json()
                    facilities = data.get("Results", {}).get("Facilities", [])
                    if facilities:
                        return self._normalize_echo_data(facilities)
                        
            except Exception as e:
                logger.debug(f"ECHO API {url} failed: {e}")
                continue
        
        return []
    
    async def _try_epa_frs_api(self, company: str, state: Optional[str], 
                             limit: int) -> List[Dict[str, Any]]:
        """Try EPA Facility Registry Service (FRS) API."""
        
        frs_base = "https://data.epa.gov/efservice/FRS_FACILITY_SITE"
        
        try:
            url = f"{frs_base}/PRIMARY_NAME/CONTAINING/{company}/rows/0:{limit-1}/JSON"
            
            response = await asyncio.to_thread(
                self.session.get, url, timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and data:
                    return self._normalize_frs_data(data)
                    
        except Exception as e:
            logger.debug(f"FRS API failed: {e}")
        
        return []
    
    async def _try_epa_tri_api(self, company: str, state: Optional[str], 
                             limit: int) -> List[Dict[str, Any]]:
        """Try EPA TRI (Toxic Release Inventory) API."""
        
        tri_base = "https://data.epa.gov/efservice/tri_facility"
        
        try:
            if state:
                url = f"{tri_base}/STATE_ABBR/{state}/rows/0:{limit-1}/JSON"
            else:
                url = f"{tri_base}/FACILITY_NAME/CONTAINING/{company}/rows/0:{limit-1}/JSON"
            
            response = await asyncio.to_thread(
                self.session.get, url, timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    filtered = self._filter_by_company(data, company)
                    return filtered[:limit] if filtered else []
                    
        except Exception as e:
            logger.debug(f"TRI API failed: {e}")
        
        return []
    
    def _filter_by_company(self, data: List[Dict[str, Any]], 
                          company: str) -> List[Dict[str, Any]]:
        """Filter EPA data by company name with fuzzy matching."""
        
        company_lower = company.lower()
        company_words = set(company_lower.split())
        
        filtered = []
        for facility in data:
            facility_name = str(facility.get("facility_name", "")).lower()
            primary_name = str(facility.get("primary_name", "")).lower()
            
            # Check if company name appears in facility name
            if (company_lower in facility_name or 
                company_lower in primary_name or
                any(word in facility_name for word in company_words if len(word) > 3)):
                filtered.append(facility)
        
        return filtered
    
    def _normalize_echo_data(self, echo_facilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize ECHO API data to standard format."""
        
        normalized = []
        for facility in echo_facilities:
            normalized.append({
                "facility_name": facility.get("FacName", ""),
                "state": facility.get("FacState", ""),
                "county": facility.get("FacCounty", ""),
                "city": facility.get("FacCity", ""),
                "zip_code": facility.get("FacZip", ""),
                "source": "EPA_ECHO"
            })
        
        return normalized
    
    def _normalize_frs_data(self, frs_facilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize FRS API data to standard format."""
        
        normalized = []
        for facility in frs_facilities:
            normalized.append({
                "facility_name": facility.get("primary_name", ""),
                "state": facility.get("state_code", ""),
                "county": facility.get("county_name", ""),
                "city": facility.get("city_name", ""),
                "zip_code": facility.get("postal_code", ""),
                "source": "EPA_FRS"
            })
        
        return normalized
    
    async def _get_cached_data(self, company: str, 
                             state: Optional[str]) -> Optional[List[Dict[str, Any]]]:
        """Get cached EPA data if available and not expired."""
        
        # This would integrate with Redis or database cache
        # For now, return None (no cache implementation)
        return None
    
    def _get_intelligent_sample_data(self, company: str, 
                                   state: Optional[str]) -> List[Dict[str, Any]]:
        """Generate intelligent sample data based on company name and state."""
        
        # Generate realistic sample data based on company characteristics
        sample_facilities = []
        
        # Determine industry type from company name
        company_lower = company.lower()
        
        if any(word in company_lower for word in ["manufacturing", "factory", "plant", "corp"]):
            sample_facilities.append({
                "facility_name": f"{company} Manufacturing Plant",
                "state": state or "CA",
                "county": "Sample County",
                "city": "Sample City",
                "source": "INTELLIGENT_SAMPLE",
                "confidence_note": "Sample data - EPA APIs unavailable"
            })
        
        if any(word in company_lower for word in ["energy", "power", "electric", "gas"]):
            sample_facilities.append({
                "facility_name": f"{company} Power Generation Facility",
                "state": state or "TX", 
                "county": "Energy County",
                "city": "Power City",
                "source": "INTELLIGENT_SAMPLE",
                "confidence_note": "Sample data - EPA APIs unavailable"
            })
        
        # Default sample if no specific industry detected
        if not sample_facilities:
            sample_facilities.append({
                "facility_name": f"{company} Facility",
                "state": state or "CA",
                "county": "Default County", 
                "city": "Default City",
                "source": "INTELLIGENT_SAMPLE",
                "confidence_note": "Sample data - EPA APIs unavailable"
            })
        
        return sample_facilities
    
    async def health_check_endpoints(self) -> Dict[str, bool]:
        """Check health of all EPA endpoints."""
        
        health_status = {}
        
        all_endpoints = self.primary_endpoints + self.backup_endpoints
        
        for endpoint in all_endpoints:
            try:
                # Simple health check
                test_url = f"{endpoint}/tri_facility/rows/0:1/JSON"
                response = await asyncio.to_thread(
                    self.session.get, test_url, timeout=10
                )
                
                health_status[endpoint] = response.status_code == 200
                
            except Exception:
                health_status[endpoint] = False
        
        return health_status