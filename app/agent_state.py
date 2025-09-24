from typing import TypedDict, Annotated, List, Dict, Optional, Any
import operator
from datetime import datetime

# ==============================================================================
# == SUB-STRUKTUR DATA (DATA PAYLOADS) ==
# ==============================================================================
# Memecah state menjadi class-class kecil ini adalah praktik yang sangat baik.

class AuditLogEntry(TypedDict):
    """Mencatat satu langkah dalam proses untuk auditabilitas tingkat forensik."""
    agent_name: str          # Nama agent yang melakukan aksi (e.g., "ETL_Crosswalk_Agent")
    action: str              # Deskripsi aksi yang dilakukan (e.g., "Linked CIK to EPA Facility IDs")
    timestamp: str           # Waktu aksi dalam format ISO 8601
    input_refs: List[str]    # Referensi ke data input (e.g., S3 path ke raw data)
    output_refs: List[str]   # Referensi ke data output (e.g., ID tabel di PostgreSQL)
    grok_reasoning_trace: str # Penjelasan dari Grok mengapa keputusan tertentu dibuat
    status: str              # Status aksi ('SUCCESS', 'FAILURE', 'WARNING')
    error_message: Optional[str] # Pesan error jika status adalah FAILURE

class RawDataEntry(TypedDict):
    """Menyimpan satu data mentah yang diambil dari sumber eksternal."""
    source_name: str         # Sumber data (e.g., "EPA_GHGRP", "SUSTAINALYTICS_API")
    s3_path: str             # Path ke file data mentah di S3 Data Lake
    fetch_timestamp: str     # Waktu pengambilan data
    metadata: Dict[str, Any] # Metadata tambahan (e.g., URL API, versi)

class ProcessedEmissionsData(TypedDict):
    """Struktur data untuk emisi yang sudah diolah dan siap lapor."""
    scope_1_emissions_co2e: float
    scope_2_emissions_co2e: float
    calculation_methodology: str
    data_year: int

class CrosswalkMapping(TypedDict):
    """Menyimpan hasil pemetaan ID ('harta karun')."""
    sec_cik: str
    epa_facility_ids: List[str]
    duns_numbers: List[str]
    confidence_score: float
    mapping_method: str      # e.g., "Exact Match", "Fuzzy Match via Grok Reasoning"

# ==============================================================================
# ==  AGENT STATE UTAMA  ==
# ==============================================================================

class AgentState(TypedDict):
    """
    State bersama untuk alur kerja multi-agent Envoyou.
    Ini adalah memori yang dibagikan dan dimodifikasi oleh semua agent.
    """
    # --- Input & Status Workflow ---
    request_id: str                 # ID unik untuk setiap permintaan API
    initial_query: Dict[str, Any]   # Query asli dari user (e.g., {"cik": "123456"})
    workflow_status: str            # Status saat ini ('ACQUIRING', 'PROCESSING', 'AUDITING', 'COMPLETED', 'FAILED')
    errors: Annotated[List[str], operator.add] # Daftar pesan error yang terjadi

    # --- Data Payloads (Diisi oleh Agent) ---
    # Diisi oleh Data Acquisition Agent. `operator.add` akan menggabungkan list dari berbagai sumber data.
    raw_data_lake_entries: Annotated[List[RawDataEntry], operator.add]

    # Diisi oleh ETL & Crosswalk Agent
    processed_emissions: Optional[ProcessedEmissionsData]
    crosswalk_mappings: Annotated[List[CrosswalkMapping], operator.add]

    # Diisi oleh Audit Trail Agent (di-trigger oleh semua agent)
    # Ini sangat penting agar setiap agent bisa menambahkan log tanpa menghapus log sebelumnya.
    audit_log: Annotated[List[AuditLogEntry], operator.add]

    # --- Output Final ---
    # Diisi oleh API Serving Agent di akhir workflow
    final_report_json: Optional[Dict[str, Any]]