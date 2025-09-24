# Envoyou SEC API — Goals & Key Features

Dokumen ringkas ini menjadi rujukan internal agar fokus proyek tidak melebar.

## Tujuan (Goals)

- Fokus pada kepatuhan SEC Climate Disclosure (Scope 1 & 2).
- Menyediakan kalkulasi emisi yang auditable (forensic‑grade traceability).
- Validasi silang otomatis dengan data publik (EPA) untuk mendeteksi anomali.
- Ekspor keluaran siap pengarsipan SEC (10‑K friendly, JSON/CSV).
- Aman, dapat diaudit, dan mudah dioperasikan (CI/CD, migration versioned).

## Fitur Kunci (MVP)

- Kalkulator Emisi GHG
  - Perhitungan Scope 1 & 2 (versi awal; extensible)
  - Manajemen faktor emisi & sumber (EPA/EDGAR)
- AuditTrail
  - Simpan input, versi kalkulasi, sumber faktor, timestamp, catatan
  - Terintegrasi otomatis di compute_cevs
  - Ekspor CSV/JSON untuk audit
- Validasi Silang Data
  - Perbandingan hasil internal dengan data EPA (fallback logics)
  - Penandaan deviasi signifikan untuk koreksi pra‑pelaporan
- Exporter SEC
  - Modul `sec_exporter` (JSON/CSV)
  - Struktur output konsisten untuk lampiran 10‑K (dapat dikembangkan)
- Keamanan & Akses
  - Supabase JWT middleware (verifikasi token)
  - RBAC via ADMIN_EMAILS/INSPECTOR_EMAILS untuk `/v1/audit/*`
  - API key + rate limit untuk endpoint publik/terbatas
- Operasional
  - Alembic migrations (versioned schema; staging→prod)
  - CI GitHub Actions (Envoyou‑focused tests by default; full regression opsional)

## Non‑Goals (fase awal)

- Fitur perizinan/permit (ditunda)
- Scope 3 & integrasi ERP penuh (tahap berikutnya)

## Deliverables inti (MVP)

- Endpoint kalkulasi + AuditTrail otomatis
- Validasi silang EPA + ambang deviasi
- Ekspor JSON/CSV untuk 10‑K
- Autentikasi & RBAC untuk audit endpoints
- Alembic migration siap deploy (backup/rollback)
