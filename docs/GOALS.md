# Envoyou SEC API — Goals & Key Features

This concise document serves as an internal reference to keep the project focused.

## Goals

- Focus on SEC Climate Disclosure compliance (Scope 1 & 2).
- Provide auditable emissions calculation (forensic‑grade traceability).
- Automatic cross-validation with public data (EPA) to detect anomalies.
- Export SEC-ready outputs (10‑K friendly, JSON/CSV).
- Secure, auditable, and easy to operate (CI/CD, versioned migrations).

## Key Features (MVP)

- GHG Emissions Calculator
  - Scope 1 & 2 calculation (initial version; extensible)
  - Emission factor & source management (EPA/EDGAR)
- AuditTrail
  - Store inputs, calculation version, factor sources, timestamps, notes
  - Automatically integrated in compute_cevs
  - CSV/JSON export for auditing
- Cross-Validation Data
  - Compare internal results with EPA data (fallback logics)
  - Flag significant deviations for pre-reporting correction
- SEC Exporter
  - `sec_exporter` module (JSON/CSV)
  - Consistent output structure for 10‑K attachments (extensible)
- Security & Access
  - Supabase JWT middleware (token verification)
  - RBAC via ADMIN_EMAILS/INSPECTOR_EMAILS for `/v1/audit/*`
  - API key + rate limiting for public/restricted endpoints
- Operations
  - Alembic migrations (versioned schema; staging→prod)
  - CI GitHub Actions (Envoyou‑focused tests by default; full regression optional)

## Non‑Goals (initial phase)

- Permit/licensing features (deferred)
- Scope 3 & full ERP integration (next phase)

## Core Deliverables (MVP)

- Calculation endpoint + automatic AuditTrail
- EPA cross-validation + deviation thresholds
- JSON/CSV export for 10‑K
- Authentication & RBAC for audit endpoints
- Production-ready Alembic migration (backup/rollback)

## Repository Envoyou SEC API

[Backend](https://github.com/ENVOYou/envoyou-sec-api) Status: Deploy on Railway (phyton, Fast API)  
[Landing Page](https://github.com/ENVOYou/envoyou-landing) Status: Deploy on Netlify (React, Vite)  
[Dashboard Login/Register](https://github.com/ENVOYou/app-envoyou-sec-api) Status: Deploy on vercel (Next.js, React)  
[Documentation](https://github.com/ENVOYou/envoyou-docs) Status: Deploy on Netlify (React, Docusaurus)
