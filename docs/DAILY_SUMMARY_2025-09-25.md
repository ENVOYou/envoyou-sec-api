# Daily Summary — Envoyou SEC API (2025-09-25)

## Apa yang sudah diimplementasikan

- Pondasi & CI
  - Pisahkan repo dari project-permit-api, bersihkan docs lama, arsipkan artefak ke `archive_removed/`.
  - Alembic aktif; `target_metadata` terset; environment CI dilengkapi `JWT_SECRET_KEY`, `SUPABASE_JWT_SECRET`.
  - Pytest difokuskan (skip legacy tests); filter deprecation warnings; guard call async EEA di fungsi sync.
  - GitHub Actions: Envoyou-focused tests default; full regression opsional.
  - Tag rilis `v0.1.0` dibuat.

- Audit & Model
  - AuditTrail (model, repo, service, routes):
    - `/v1/audit` (POST/GET) — diamankan Supabase JWT + RBAC (`ADMIN_EMAILS`/`INSPECTOR_EMAILS`).
  - Tests integrasi AuditTrail lulus.

- Emissions (MVP v0.1)
  - Kalkulator Scope 1 & 2 (faktor sederhana + konversi unit dasar).
  - Endpoint: `POST /v1/emissions/calculate` — otomatis simpan AuditTrail.
  - Tests lulus.

- Validasi Silang EPA (enriched)
  - Service: `cross_validate_epa` — thresholds dari env:
    - `VALIDATION_MIN_MATCHES`, `VALIDATION_LOW_DENSITY_THRESHOLD`, `VALIDATION_REQUIRE_STATE_MATCH`.
  - Flags detail: `no_epa_match`, `low_match_density`, `state_mismatch`/`state_required_no_match` + suggestions.
  - Endpoint: `POST /v1/validation/epa` (API key).
  - Tests lulus.

- Exporter SEC
  - Endpoints:
    - `GET /v1/export/sec/cevs` (json/csv)
    - `GET /v1/export/sec/audit` (csv)
  - Paket SEC (zip) + upload:
    - `POST /v1/export/sec/package` → zip berisi `validation.json`, `audit.csv`, `README.txt`; upload via storage pluggable (local/S3/GCS); AuditTrail mencatat URL.
  - Storage service (local default, stubs S3/GCS).
  - Tests lulus.

- Admin Mapping (manual)
  - Model: `company_facility_map`.
  - Endpoints (premium):
    - `POST /v1/admin/mappings` (upsert)
    - `GET /v1/admin/mappings/{company}`
    - `GET /v1/admin/mappings`
  - Tests lulus.

- Dokumentasi
  - `docs/GOALS.md`, `METRICS.md`, `SECURITY_PLAN.md`, `PARTNERING.md`, `SEC_EXPORT_SAMPLES.md`, `DB_MIGRATION_PLAN.md`, `ADMIN_MAPPING.md`.
  - README ditautkan ke dokumen-dokumen di atas dan daftar endpoint baru.

## Workflow kerja (kode → commit → push)

- Semua pekerjaan dilakukan di branch: `envoyou/initial`.
- Rangkaian commit utama:
  - Cleanup docs/artefak, tambah AuditTrail, emissions v0.1, validasi (thresholds & flags), exporter package + storage, admin mapping.
- PR draft awal dibuat dari `envoyou/initial` → `main`; CI hijau dengan konfigurasi baru.

## TODO Next (untuk besok)

1. Integrasi mapping manual ke validasi/CEVS

- Jika mapping tersedia, gunakan `facility_id` untuk data kuantitatif (CAMPD/EIA) dan hitung deviasi numerik.
- Tambah threshold deviasi kuantitatif per pollutant/aktivitas.

1. Lengkapi export package

- Sertakan `cevs.json` (hasil komputasi CEVS) dan ringkasan human-readable (`summary.txt`).
- Tambah opsi upload S3/GCS produksi + kebijakan retensi; catat URL di AuditTrail.

1. Faktor emisi & unit

- Endpoint `GET /v1/emissions/factors` dan `/v1/emissions/units`.
- Kelola versi faktor dan persist faktor versi di DB (untuk audit granular).

1. Keamanan & rate limiting

- RBAC berbasis JWT claims (role), bukan sekadar email list.
- Rate limiting per tier (env-driven) per route (weighted endpoints).

1. Observability

- Ekspos `/metrics`; SIEM logging handler untuk akses audit.
- Tambahkan workflow nightly `full_regression` di CI.

1. Staging Supabase migration

- Jalankan Alembic sesuai `docs/DB_MIGRATION_PLAN.md`; backup & preview SQL.
- Seed data minimal (admin emails, demo key, mapping contoh).

1. Dokumentasi

- Tambah E2E demo (input → calculate → validate → export) dengan contoh curl & respons.
- Perbarui README untuk endpoint baru (validation, export package, admin mapping) dengan contoh request/response lengkap.
