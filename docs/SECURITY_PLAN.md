# Security Plan (Early Commitment)

## Audit Access Logging → SIEM

- Target: struktur log akses audit (read/write) dapat dikirim ke SIEM (Splunk/Datadog).
- Format log terstruktur (JSON): timestamp, route, actor (user/email), action, result, latency, request_id, ip, user_agent.
- Opsi integrasi:
  - Syslog/HTTP forwarder (agent) dari host/container ke SIEM.
  - Langkah lanjut: menambah handler Python logging ke HTTPS endpoint SIEM (batasi PII).

## Rate Limiting per Tier

- Desain saat ini: per API key punya requests_per_minute (basic 30 rpm, premium 100 rpm) — configurable via API_KEYS/Master key.
- Rencana:
  - Tambah tier enterprise (≥ 300 rpm) dan burst multiplier (mis. 1.2x) via env.
  - Per‑route weights (expensive endpoints lebih ketat).

## Auth & Authorization

- Supabase JWT verification (HS256) + fallback internal JWT.
- RBAC sederhana untuk /v1/audit via ADMIN_EMAILS/INSPECTOR_EMAILS.
- Rencana: role map berbasis claim (e.g., app_role) langsung dari token.

## Secrets & Transport

- Semua secrets via env/secret manager (tanpa commit ke repo).
- TLS terminasi di edge, opsi mTLS untuk partner enterprise.

## Compliance Readiness

- AuditTrail immutable strategy (append‑only di prod, kontrol akses ketat).
- Retention policy & backup encryption.
