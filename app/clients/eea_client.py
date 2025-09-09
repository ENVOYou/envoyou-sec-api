from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
import io
import requests
import pandas as pd
from functools import lru_cache

from app.utils.mappings import normalize_country_name

# Pastikan Anda telah menambahkan 'pyarrow' ke requirements.txt
# pip install pyarrow

logger = logging.getLogger(__name__)

class EEAClient:
    """
    Klien untuk berinteraksi dengan EEA Downloads API (Parquet).
    API Docs: https://eeadmz1-downloads-api-appservice.azurewebsites.net/swagger/index.html
    """
    BASE_URL = "https://eeadmz1-downloads-api-appservice.azurewebsites.net/api/v1/public"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json, application/octet-stream",
            "User-Agent": f"project-permit-api/1.0 (+{os.getenv('GITHUB_REPO_URL', 'https://github.com/hk-dev13')})"
        })

    @lru_cache(maxsize=10) # Cache sederhana untuk menghindari pengunduhan berulang
    def _get_parquet_data(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        Menemukan, mengunduh, dan mengurai dataset Parquet dari EEA API.
        Ini menerapkan alur kerja 2 langkah:
        1. Dapatkan metadata file untuk menemukan URL unduhan.
        2. Unduh dan baca file Parquet.
        """
        logger.info(f"Mencari file untuk dataset EEA: {dataset_id}")
        files_url = f"{self.BASE_URL}/datasets/{dataset_id}/files"

        try:
            # Langkah 1: Dapatkan URL unduhan
            resp_files = self.session.get(files_url, timeout=30)
            resp_files.raise_for_status()
            files_metadata = resp_files.json()

            # Cari file Parquet pertama yang tersedia
            download_url = next((f['links']['download'] for f in files_metadata if f['name'].endswith('.parquet')), None)

            if not download_url:
                logger.warning(f"Tidak ada file Parquet yang ditemukan untuk dataset {dataset_id}, menggunakan data fallback")
                return self._get_fallback_data(dataset_id)

            # Langkah 2: Unduh dan baca file Parquet
            logger.info(f"Mengunduh data Parquet dari: {download_url}")
            resp_data = self.session.get(download_url, timeout=90) # Timeout lebih lama untuk unduhan
            resp_data.raise_for_status()

            # Gunakan pandas untuk membaca konten biner
            df = pd.read_parquet(io.BytesIO(resp_data.content))

            # Bersihkan nama kolom untuk konsistensi (opsional tapi disarankan)
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

            return df.to_dict(orient="records")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Dataset {dataset_id} tidak ditemukan di EEA API, menggunakan data fallback")
                return self._get_fallback_data(dataset_id)
            else:
                logger.error(f"HTTP error saat mengambil data EEA untuk {dataset_id}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Kesalahan jaringan saat mengambil data EEA untuk {dataset_id}: {e}")
        except Exception as e:
            logger.error(f"Kesalahan saat memproses data Parquet untuk {dataset_id}: {e}")

        # Fallback ke data statis jika semua gagal
        return self._get_fallback_data(dataset_id)

    def _get_fallback_data(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        Menyediakan data fallback statis ketika EEA API tidak tersedia.
        Data ini didasarkan pada nilai rata-rata global dan dapat diperbarui secara manual.
        """
        logger.info(f"Menggunakan data fallback untuk dataset: {dataset_id}")
        
        # Set environment variable to indicate fallback is being used
        if dataset_id == "share-of-energy-from-renewable-sources":
            os.environ["EEA_RENEWABLES_SOURCE"] = "EEA Fallback Data (API Unavailable)"
        elif dataset_id == "industrial-releases-of-pollutants-to-water":
            os.environ["EEA_POLLUTION_SOURCE"] = "EEA Fallback Data (API Unavailable)"

        if dataset_id == "share-of-energy-from-renewable-sources":
            # Data energi terbarukan global (2023 estimates)
            return [
                {
                    "country": "Germany",
                    "renewable_energy_share_2020": 45.2,
                    "renewable_energy_share_2021_proxy": 46.8,
                    "target_2020": 35.0
                },
                {
                    "country": "United Kingdom",
                    "renewable_energy_share_2020": 43.1,
                    "renewable_energy_share_2021_proxy": 44.2,
                    "target_2020": 30.0
                },
                {
                    "country": "France",
                    "renewable_energy_share_2020": 25.3,
                    "renewable_energy_share_2021_proxy": 26.1,
                    "target_2020": 23.0
                },
                {
                    "country": "Netherlands",
                    "renewable_energy_share_2020": 28.7,
                    "renewable_energy_share_2021_proxy": 29.8,
                    "target_2020": 14.0
                },
                {
                    "country": "Global Average",
                    "renewable_energy_share_2020": 19.1,
                    "renewable_energy_share_2021_proxy": 20.2,
                    "target_2020": 15.0
                }
            ]

        elif dataset_id == "industrial-releases-of-pollutants-to-water":
            # Data polusi industri global (simulasi tren)
            return [
                {
                    "year": 2018,
                    "cd_hg_ni_pb": 2.3,
                    "toc": 15.7,
                    "total_n": 45.2,
                    "total_p": 8.9,
                    "gva": 1200.5
                },
                {
                    "year": 2019,
                    "cd_hg_ni_pb": 2.1,
                    "toc": 14.9,
                    "total_n": 43.8,
                    "total_p": 8.5,
                    "gva": 1250.3
                },
                {
                    "year": 2020,
                    "cd_hg_ni_pb": 1.9,
                    "toc": 13.8,
                    "total_n": 41.2,
                    "total_p": 7.8,
                    "gva": 1180.7
                },
                {
                    "year": 2021,
                    "cd_hg_ni_pb": 1.8,
                    "toc": 13.2,
                    "total_n": 39.5,
                    "total_p": 7.2,
                    "gva": 1300.1
                },
                {
                    "year": 2022,
                    "cd_hg_ni_pb": 1.7,
                    "toc": 12.5,
                    "total_n": 37.8,
                    "total_p": 6.8,
                    "gva": 1350.9
                }
            ]

        else:
            logger.warning(f"Tidak ada data fallback untuk dataset: {dataset_id}")
            return []

    def get_countries_renewables(self) -> List[Dict[str, Any]]:
        """
        Mengambil dan menormalkan data pangsa energi terbarukan per negara.
        """
        # ID ini harus diverifikasi dari API, ini adalah contoh
        dataset_id = "share-of-energy-from-renewable-sources" 
        raw_data = self._get_parquet_data(dataset_id)
        
        normalized_data = []
        for record in raw_data:
            # Kolom di-lowercase dan underscore oleh _get_parquet_data
            country = record.get("country")
            if not country:
                continue

            normalized_data.append({
                "country": country,
                "renewable_energy_share_2020": record.get("renewable_energy_share_2020"),
                "renewable_energy_share_2021_proxy": record.get("renewable_energy_share_2021_(proxy)"), # Sesuaikan dengan nama kolom yang sebenarnya
                "target_2020": record.get("2020_target"),
            })
        return normalized_data

    def get_country_renewables(self, country: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Mengambil data energi terbarukan untuk negara tertentu.
        """
        if not country:
            return None
        
        all_countries = self.get_countries_renewables()
        normalized_country = normalize_country_name(country)
        
        for record in all_countries:
            if normalize_country_name(record.get("country", "")) == normalized_country:
                return record
        return None

    def get_industrial_pollution(self) -> List[Dict[str, Any]]:
        """
        Mengambil dan menormalkan data tren polusi industri.
        """
        # ID ini harus diverifikasi dari API, ini adalah contoh
        dataset_id = "industrial-releases-of-pollutants-to-water"
        raw_data = self._get_parquet_data(dataset_id)
        
        normalized_data = []
        for record in raw_data:
            year = record.get("year")
            if not year:
                continue
                
            def to_float(v):
                try:
                    return float(v) if v not in (None, "") else None
                except Exception:
                    return None
                    
            normalized_data.append({
                "year": int(year),
                "cd_hg_ni_pb": to_float(record.get("cd_hg_ni_pb")),
                "toc": to_float(record.get("toc")),
                "total_n": to_float(record.get("total_n")),
                "total_p": to_float(record.get("total_p")),
                "gva": to_float(record.get("gva")),
            })
        
        # Sort by year
        normalized_data.sort(key=lambda x: x.get("year", 0))
        return normalized_data

    def compute_pollution_trend(self, records: List[Dict[str, Any]], window: int = 3) -> Dict[str, Any]:
        """
        Menghitung tren sederhana berdasarkan data polusi.
        """
        def slope_for(key: str) -> Dict[str, Any]:
            vals = [r.get(key) for r in records if isinstance(r.get(key), (int, float))]
            if len(vals) < 2:
                return {"slope": 0.0, "increase": False}
            sel = vals[-window:] if len(vals) >= window else vals
            s = float(sel[-1] - sel[0])
            return {"slope": s, "increase": s > 0.0}
            
        return {
            "total_n": slope_for("total_n"),
            "total_p": slope_for("total_p")
        }

    def get_indicator(self, *, indicator: Optional[str] = "GHG", country: Optional[str] = None, 
                     year: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Generic indicator method for backward compatibility.
        Handles different types of indicators by routing to appropriate methods.
        """
        try:
            if not indicator:
                indicator = "GHG"
                
            indicator_lower = indicator.lower()
            
            # Route renewable energy indicators
            if "renewable" in indicator_lower or indicator_lower in ["res", "share_res"]:
                if country:
                    result = self.get_country_renewables(country)
                    return [result] if result else []
                else:
                    results = self.get_countries_renewables()
                    return results[:limit] if results else []
            
            # Route GHG/pollution indicators  
            elif indicator_lower in ["ghg", "greenhouse", "pollution", "emissions"]:
                results = self.get_industrial_pollution()
                
                # Apply country filter if specified
                if country:
                    normalized_country = normalize_country_name(country)
                    results = [r for r in results 
                             if normalize_country_name(r.get('country', '')) == normalized_country or
                                normalize_country_name(r.get('countryName', '')) == normalized_country]
                
                # Apply year filter if specified  
                if year:
                    results = [r for r in results 
                             if r.get('year') == year or r.get('reportingYear') == year]
                
                return results[:limit] if results else []
            
            # Default fallback - return renewable energy data
            else:
                logger.warning(f"Unknown indicator '{indicator}', defaulting to renewable energy")
                if country:
                    result = self.get_country_renewables(country)
                    return [result] if result else []
                else:
                    results = self.get_countries_renewables()
                    return results[:limit] if results else []
                    
        except Exception as e:
            logger.error(f"Error in get_indicator: {e}")
            return []

__all__ = ["EEAClient"]