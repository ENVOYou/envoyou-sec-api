# File: app/graph.py

import uuid
from langgraph.graph import StateGraph, END

from app.agent_state import AgentState
from app.agents.acquisition_agent import run_acquisition_agent

# ==============================================================================
# == 1. DEFINISI ALUR KERJA (WORKFLOW GRAPH) ==
# ==============================================================================
# Di sinilah kita mendefinisikan "cetak biru" dari proses multi-agent kita.

# Inisialisasi graph dengan state yang telah kita definisikan.
# AgentState akan menjadi "memori bersama" yang dioper ke setiap node.
workflow = StateGraph(AgentState)

# Menambahkan node pertama kita ke dalam graph.
# - Nama node: "acquisition" (string ini akan kita gunakan untuk merujuknya)
# - Aksi node: `run_acquisition_agent` (fungsi yang kita buat sebelumnya)
workflow.add_node("acquisition", run_acquisition_agent)

# ==============================================================================
# == 2. MENENTUKAN ALUR KONTROL (CONTROL FLOW) ==
# ==============================================================================
# Di sinilah kita memberi tahu graph bagaimana cara bergerak dari satu node ke node lain.

# Menetapkan titik masuk (entry point) untuk graph.
# Saat graph dijalankan, ia akan selalu dimulai dari node "acquisition".
workflow.set_entry_point("acquisition")

# Untuk MVP (Minimum Viable Product) ini, kita hanya memiliki satu langkah.
# Jadi, setelah node "acquisition" selesai, kita langsung menuju ke akhir (END).
# Di masa depan, kita akan menambahkan logika routing yang lebih kompleks di sini.
# Misalnya: "Setelah 'acquisition', lanjutkan ke 'etl_crosswalk'".
workflow.add_edge("acquisition", END)


# ==============================================================================
# == 3. KOMPILASI GRAPH MENJADI APLIKASI YANG BISA DIJALANKAN ==
# ==============================================================================

# Mengompilasi graph menjadi objek yang bisa dieksekusi.
# Ini adalah langkah final yang mengubah definisi kita menjadi aplikasi yang berfungsi.
app = workflow.compile()

# ==============================================================================
# == 4. CONTOH EKSEKUSI (UNTUK PENGUJIAN) ==
# ==============================================================================
# Blok ini memungkinkan kita untuk menjalankan file ini secara langsung untuk menguji graph.

if __name__ == "__main__":
    print("🚀 Memulai eksekusi LangGraph untuk Envoyou...")

    # Menyiapkan input awal untuk graph, meniru permintaan API.
    # Kita menggunakan CIK "123456" yang kita tahu akan memicu logika di dalam agent.
    initial_input = {
        "request_id": f"req_{uuid.uuid4()}",
        "initial_query": {"cik": "123456"},
        "workflow_status": "STARTING",
        "errors": [],
        "raw_data_lake_entries": [],
        "processed_emissions": None,
        "crosswalk_mappings": [],
        "audit_log": [],
        "final_report_json": None
    }

    print(f"\n▶️ Input Awal: {initial_input}")

    # Menjalankan graph dengan input awal.
    # Metode `.stream()` akan menjalankan setiap node secara berurutan.
    # Kita akan mencetak state setelah setiap langkah untuk melihat bagaimana ia berevolusi.
    final_state = None
    for s in app.stream(initial_input):
        print("\n--------------------")
        print(f"🔄 State setelah node '{list(s.keys())[0]}':")
        print(s)
        final_state = s

    print("\n--------------------")
    print("✅ Eksekusi Selesai!")
    print("\n🏁 Final State:")
    # Mencetak state akhir dalam format yang lebih mudah dibaca
    import json
    print(json.dumps(final_state, indent=2))