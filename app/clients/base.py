from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseDataClient(ABC):
    """
    Antarmuka (Interface) dasar untuk semua klien sumber data lingkungan.

    Setiap klien yang mengambil data dari sumber eksternal (API, scraper, dll.)
    harus mengimplementasikan metode-metode yang didefinisikan di sini.
    Ini memastikan konsistensi dan memungkinkan API untuk berinteraksi
    dengan berbagai sumber data secara seragam.
    """

    @abstractmethod
    def get_emissions_data(
        self,
        *,
        region: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 100,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Mengambil data emisi umum dari sumber data.
        Parameter `region` bisa berupa negara, negara bagian, dll.
        """
        pass