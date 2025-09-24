# File: app/tools/acquisition_tools.py
# (Versi yang sudah ditingkatkan)

import json
from datetime import datetime
from typing import List, Dict, Any

from langchain_core.tools import tool

from app.clients.global_client import EPAClient 
from app.agent_state import RawDataEntry

# Inisialisasi klien
epa_client = EPAClient()

# ==============================================================================
# ==  DEFINISI TOOLS  ==
# ==============================================================================

@tool
def fetch_epa_ghg_data(facility_ids: List[str]) -> List[Dict[str, Any]]: # <-- PERUBAHAN DI SINI
    """
    Mengambil data Greenhouse Gas (GHG) dari API EPA untuk daftar ID fasilitas tertentu.
    Gunakan alat ini untuk mendapatkan data emisi publik dari pemerintah AS.
    Alat ini akan mengembalikan daftar (list) objek Python yang berisi hasil.
    """
    print(f"🛠️ TOOL CALLED: fetch_epa_ghg_data dengan fasilitas: {facility_ids}")
    
    all_results = []
    try:
        for facility_id in facility_ids:
            # Sesuaikan nama metode ini dengan yang ada di epa_client.py Anda
            data = epa_client.get_emissions_by_facility(facility_id)
            if data:
                all_results.extend(data)
        
        # Kembalikan objek Python secara langsung
        return all_results # <-- PERUBAHAN DI SINI
    
    except Exception as e:
        print(f"🔥 ERROR in fetch_epa_ghg_data: {e}")
        # Jika terjadi error, kembalikan list berisi objek error
        return [{"error": f"Gagal mengambil data EPA: {str(e)}"}]


@tool
def save_raw_data_to_s3(source_name: str, data_content: str) -> RawDataEntry:
    """
    Menyimpan konten data mentah (string) ke dalam Raw Data Lake di S3.
    Alat ini akan menghasilkan nama file unik berdasarkan sumber dan timestamp,
    menyimpan data, dan mengembalikan objek RawDataEntry yang berisi path S3
    dan metadata lainnya untuk dicatat dalam AgentState.
    """
    print(f"🛠️ TOOL CALLED: save_raw_data_to_s3 untuk sumber: {source_name}")

    # --- Simulasi logika S3 ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{source_name}_{timestamp}.json"
    s3_path = f"s3://envoyou-raw-data-lake/{file_name}"

    print(f"  -> Mensimulasikan penyimpanan {len(data_content)} bytes ke {s3_path}")
    
    result: RawDataEntry = {
        "source_name": source_name,
        "s3_path": s3_path,
        "fetch_timestamp": datetime.now().isoformat(),
        "metadata": {
            "file_name": file_name,
            "content_length": len(data_content)
        }
    }
    return result