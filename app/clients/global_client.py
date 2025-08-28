"""
EPA Envirofacts Client

Implementasi klien untuk mengambil data fasilitas dari EPA Envirofacts API.
Data ini digunakan sebagai proksi untuk informasi emisi.
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional

import requests

from app.utils.schema import ensure_epa_emission_schema

logger = logging.getLogger(__name__)


class EPAClient:
	"""
	Klien untuk EPA Envirofacts API.

	Sumber: Envirofacts efservice (dikonfigurasi via env var)
	"""

	def __init__(self) -> None:
		# Envirofacts efservice base (documented)
		# Format: https://data.epa.gov/efservice/<Table>/<Column>/<Operator>/<Value>/rows/0:n/JSON
		self.env_base = os.getenv("EPA_ENV_BASE", "https://data.epa.gov/efservice/").rstrip("/") + "/"
		# Default table: use TRI facility for a stable, public dataset
		# You can override with EPA_ENV_TABLE (e.g., tri_facility, tri_release)
		self.env_table = os.getenv("EPA_ENV_TABLE", "tri_facility").strip("/")
		self.session = requests.Session()
		self.session.headers.update({
			"Accept": "application/json",
			"User-Agent": "project-permit-api/1.0 (+https://github.com/hk-dev13)"
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

	# --- EPA-specific helpers ---
	def get_facilities_by_state(
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
		if state:
			segments.extend(["state_abbr", state])
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
				return data
			else:
				logger.warning(f"EPA Envirofacts HTTP {resp.status_code} for {url}, using sample data")
				return self.create_sample_data()
		except Exception as e:
			logger.error(f"Error fetching EPA data from {url}: {e}")
			return self.create_sample_data()


__all__ = ["EPAClient"]
