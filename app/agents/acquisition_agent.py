# File: app/agents/acquisition_agent.py
# (Versi final dengan koneksi ke Google Gemini API)

import os
import json
from typing import Dict, Any, List

# PENTING: Kita ganti impornya ke langchain_google_genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
# from langgraph.prebuilt import ToolExecutor
# ToolExecutor removed in newer versions, we'll execute tools manually
from dotenv import load_dotenv

from app.agent_state import AgentState, RawDataEntry
from app.tools.acquisition_tools import fetch_epa_ghg_data, save_raw_data_to_s3

# Muat environment variables dari file .env
load_dotenv()

# ==============================================================================
# == 1. INISIALISASI KOMPONEN AGENT (BAGIAN YANG DIUBAH) ==
# ==============================================================================

tools = [fetch_epa_ghg_data, save_raw_data_to_s3]
# tool_executor = ToolExecutor(tools)

# Manual tool executor replacement
def execute_tools(tool_calls, tools_dict):
    """Execute tools manually since ToolExecutor was removed"""
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        
        if tool_name in tools_dict:
            tool_func = tools_dict[tool_name]
            try:
                result = tool_func.invoke(tool_args)
                results.append(result)
            except Exception as e:
                results.append(f"Error executing {tool_name}: {str(e)}")
        else:
            results.append(f"Tool {tool_name} not found")
    
    return results

# Create tools dictionary for lookup
tools_dict = {tool.name: tool for tool in tools}

# --- MULAI PERUBAHAN ---

# Validasi API key Gemini
if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

# Inisialisasi model untuk terhubung ke Google Gemini API
# Kita menggunakan integrasi resmi dari LangChain.
model = ChatGoogleGenerativeAI(
    # Gunakan environment variable yang benar untuk Google
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
    temperature=0,
    # Pilih model Gemini yang mendukung tool calling (Gemini 1.5 Pro adalah pilihan terbaik)
    model="gemini-1.5-pro-latest"
)

# --- SELESAI PERUBAHAN ---

model_with_tools = model.bind_tools(tools)


# ==============================================================================
# == 2. DEFINISI NODE DENGAN LOOP (TIDAK ADA YANG BERUBAH!) ==
# ==============================================================================
# Sisa dari file ini sama persis, karena logikanya model-agnostik.

def run_acquisition_agent(state: AgentState) -> Dict[str, Any]:
    """
    Menjalankan Data Acquisition Agent dalam sebuah loop.
    Agent ini akan terus berinteraksi dengan tools sampai tugasnya selesai.
    """
    print("--- AGENT: Memulai Data Acquisition Agent (menggunakan Google Gemini) ---")
    
    initial_query = state.get("initial_query", {})
    cik = initial_query.get("cik")
    
    # TODO: Logika ini akan digantikan oleh Crosswalk Agent di masa depan
    if cik == "123456":
        facility_ids_to_fetch = ["1000121", "1000122"]
    else:
        facility_ids_to_fetch = []

    if not facility_ids_to_fetch:
        print(" -> Tidak ada facility ID untuk CIK ini. Melewati.")
        return {}

    prompt = f"""
    Anda adalah seorang analis data lingkungan yang ahli.
    Tugas Anda adalah mengambil data emisi GHG dari EPA untuk ID fasilitas berikut, lalu menyimpannya ke S3.
    ID Fasilitas: {facility_ids_to_fetch}
    """
    messages: List = [HumanMessage(content=prompt)]

    # Loop interaksi AI <-> Tool
    for _ in range(5):
        print(f"\n -> Iterasi Loop, histori pesan saat ini: {len(messages)}")
        
        ai_response: AIMessage = model_with_tools.invoke(messages)
        
        if not ai_response.tool_calls:
            print(" -> AI tidak memanggil tool. Menganggap tugas selesai.")
            break

        messages.append(ai_response)
        
        print(f" -> AI meminta tool: {[tc['name'] for tc in ai_response.tool_calls]}")
        tool_outputs = execute_tools(ai_response.tool_calls, tools_dict)
        
        for tool_call, output in zip(ai_response.tool_calls, tool_outputs):
            content = json.dumps(output) if not isinstance(output, str) else output
            messages.append(ToolMessage(content=content, tool_call_id=tool_call['id']))

    # Kumpulkan hasil dari histori pesan
    final_raw_data_entries: List[RawDataEntry] = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            try:
                data = json.loads(msg.content)
                if isinstance(data, dict) and "s3_path" in data:
                    final_raw_data_entries.append(data)
            except (json.JSONDecodeError, TypeError):
                continue

    print("--- AGENT: Data Acquisition Agent Selesai ---")
    return {"raw_data_lake_entries": final_raw_data_entries}