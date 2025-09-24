# Metrics of Success (MVP)

Dokumen ini menetapkan metrik yang dipakai untuk menilai keberhasilan MVP Envoyou SEC API.

## 1) Time-to-Value (TTV)

- Definisi: Waktu rata-rata dari input data → kalkulasi → export (JSON/CSV) siap 10-K.
- Target awal: ≤ 30 detik (pada dataset standar, koneksi normal).
- Cara ukur: instrumentasi timing di service (server-side) + log agregasi (p95/p99).

## 2) Validasi Silang (EPA) — Akurasi Deviasi

- Definisi: Persentase hasil internal yang ditandai (flagged) benar saat dibandingkan dengan sumber EPA publik.
- Target awal: ≥ 90% deviasi flagged benar (precision), recall bertahap.
- Cara ukur: set ground-truth kecil dan rutin evaluasi batch.

## 3) SLA Uptime API

- Definisi: Persentase waktu API tersedia dan sehat (health = 200) per bulan.
- Target awal: 99.5% (dev/staging) dan 99.9% (production jangka menengah).
- Cara ukur: healthcheck monitoring + alerting.

## 4) Kualitas Export

- Definisi: Tingkat penerimaan (acceptance) oleh CFO/Legal (tanpa revisi besar) untuk lampiran 10-K.
- Target awal: ≥ 95% acceptance pada pilot.
- Cara ukur: feedback survey + issue tracker.

## 5) Performansi Query

- Definisi: Latensi p95 untuk endpoint kalkulasi dan export.
- Target awal: p95 ≤ 1.5s (tanpa I/O eksternal berat) di staging.

## Operasional & Pelaporan

- Dashboard metrik (Grafana/Dash, dsb.)
- Laporan mingguan: TTV, latensi p95/p99, jumlah export, error rate.
