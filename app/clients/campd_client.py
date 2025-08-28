from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class CAMDClient:
    """
    Klien untuk API EPA Clean Air Markets Program Data (CAMPD).
    API ini menyediakan data emisi dan kepatuhan untuk pembangkit listrik.
    
    Dokumentasi API: https://www.epa.gov/airmarkets/cam-api-portal
    """

    def __init__(self) -> None:
        self.base_url = os.getenv("CAMPD_API_BASE_URL", "https://api.epa.gov/easey")
        # Kunci API CAMPD didapatkan dari environment variable.
        # Anda bisa mendapatkannya di: https://www.epa.gov/airmarkets/cam-api-portal
        self.api_key = os.getenv("CAMPD_API_KEY")
        
        if not self.api_key:
            logger.warning("CAMPD_API_KEY tidak diset. Permintaan ke CAMD API akan gagal.")

        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "x-api-key": self.api_key or "",
            "User-Agent": "project-permit-api/1.0 (+https://github.com/hk-dev13)"
        })

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[List[Dict[str, Any]]]:
        """Helper untuk membuat permintaan ke API CAMPD."""
        if not self.api_key:
            return None

        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error saat meminta data dari CAMPD endpoint {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error umum saat memproses permintaan CAMPD: {e}")
            return None

    def get_emissions_data(self, facility_id: int, year: int = 2022) -> Optional[List[Dict[str, Any]]]:
        """
        Mengambil data emisi tahunan (CO2, SO2, NOx) untuk fasilitas tertentu.
        
        Endpoint: /apportioned/annual
        """
        endpoint = "/apportioned/annual"
        params = {
            "facilityId": facility_id,
            "year": year,
        }
        return self._make_request(endpoint, params)

    def get_compliance_data(self, facility_id: int, year: int = 2022) -> Optional[List[Dict[str, Any]]]:
        """
        Mengambil data kepatuhan tahunan untuk fasilitas tertentu.
        
        Endpoint: /compliance/annual
        """
        endpoint = "/compliance/annual"
        params = {
            "facilityId": facility_id,
            "year": year,
        }
        return self._make_request(endpoint, params)

__all__ = ["CAMDClient"]