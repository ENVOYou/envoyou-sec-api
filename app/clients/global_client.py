"""
EPA Envirofacts Client

Implementasi klien untuk mengambil data fasilitas dari EPA Envirofacts API (tri_facility).
Data ini digunakan sebagai proksi untuk informasi emisi, dengan normalisasi tambahan.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import logging

import requests

from app.config import settings
from app.clients.base import BaseDataClient
from app.utils.schema import ensure_epa_emission_schema

logger = logging.getLogger(__name__)


class EPAClient(BaseDataClient):
	"""
	Klien untuk EPA Envirofacts API.

	Sumber: Envirofacts efservice (dikonfigurasi via env var)
	"""

	def __init__(self) -> None:
		# Envirofacts efservice base (documented)
		# Format: https://data.epa.gov/efservice/<Table>/<Column>/<Operator>/<Value>/rows/0:n/JSON
		self.env_base = settings.EPA_ENV_BASE.rstrip("/") + "/"
		self.env_table = settings.EPA_ENV_TABLE.strip("/")
		self.session = requests.Session()
		self.session.headers.update({
			"Accept": "application/json",
			"User-Agent": f"project-permit-api/1.0 (+{settings.GITHUB_REPO_URL})"
		})

	def format_emission_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		"""Normalisasi record EPA ke skema standar emisi."""
		if not data:
			return []
		return [ensure_epa_emission_schema(rec) for rec in data if isinstance(rec, dict)]

	def create_sample_data(self) -> List[Dict[str, Any]]:
		"""
		Data sample emisi EPA untuk fallback/demonstrasi.
		"""
		return [
			{
				"facility_name": "Sample Coal Plant A",
				"plant_id": "PLT1001",
				"state": "TX",
				"county": "Harris",
				"year": 2023,
				"pollutant": "CO2",
				"emissions": 1234567.89,
				"unit": "tons"
			},
			{
				"facility_name": "Sample Gas Plant B",
				"plant_id": "PLT2002",
				"state": "CA",
				"county": "Los Angeles",
				"year": 2023,
				"pollutant": "CO2",
				"emissions": 234567.0,
				"unit": "tons"
			}
		]

	# --- Implementation of BaseDataClient interface ---
	def get_emissions_data(
		self,
		*,
		region: Optional[str] = None,
		year: Optional[int] = None,
		limit: int = 100,
		**kwargs: Any,
	) -> List[Dict[str, Any]]:
		"""Mengambil data emisi dari EPA Envirofacts. `region` dipetakan ke `state`."""
		return self._get_facilities_by_state(state=region, year=year, limit=limit, **kwargs)

	def _get_facilities_by_state(
		self,
		*,
		state: Optional[str] = None,
		year: Optional[int] = None,
		limit: int = 100,
		timeout: Optional[float] = None,
	) -> List[Dict[str, Any]]:
		"""
		Ambil data fasilitas dari Envirofacts efservice, difilter berdasarkan negara bagian (state).

		Menggunakan format URL terdokumentasi: data.epa.gov/efservice
		- Default tabel: tri_facility (stabil dan publik)
		- Filter yang dipakai: state_abbr (jika diberikan)

		Catatan: Untuk dataset lain, set EPA_ENV_TABLE; sesuaikan kolom filter.
		Jika permintaan gagal, kembalikan sample data.
		"""
		# Bangun path sesuai format efservice
		segments: List[str] = [self.env_table]
		if state: # Gunakan nama kolom yang benar sesuai dokumentasi EPA (case-sensitive)
			segments.extend(["STATE_ABBR", state])
		# TRI facility tidak menyediakan kolom 'year' langsung; abaikan jika diberikan
		# Pembatasan baris (0-indexed, inclusive)
		end_row = max(0, (limit or 100) - 1)
		segments.extend(["rows", f"0:{end_row}", "JSON"])

		url = f"{self.env_base}{'/'.join(segments)}"

		try:
			req_timeout = timeout if (timeout is not None and timeout > 0) else 30
			resp = self.session.get(url, timeout=req_timeout)
			if resp.status_code == 200:
				data = resp.json()
				if not isinstance(data, list):
					raise ValueError("Unexpected EPA response shape (expected list)")
				# Jika respons live kosong, gunakan data sampel untuk pengalaman demo yang lebih baik.
				if not data:
					logger.info(f"EPA response for {url} was empty. Using sample data as fallback.")
					return self.create_sample_data()
				return data
			else:
				logger.warning(f"EPA Envirofacts HTTP {resp.status_code} for {url}, using sample data")
				return self.create_sample_data()
		except Exception as e:
			logger.error(f"Error fetching EPA data from {url}: {e}")
			return self.create_sample_data()

__all__ = ["EPAClient"]
