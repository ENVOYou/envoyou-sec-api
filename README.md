# Envoyou SEC API

Envoyou SEC API is a focused backend service for SEC Climate Disclosure compliance. It provides auditable greenhouse gas (GHG) calculation, validation, and report export features tailored for public companies required to submit climate disclosures.

## Key goals

- Single-purpose MVP: calculate Scope 1 and Scope 2 emissions, produce auditable calculation records, and export SEC-ready reporting tables.
- Forensic-grade traceability: every calculation stores inputs, emission factors, and sources in an AuditTrail.
- Cross-validation: automatic comparison against public EPA datasets to flag significant discrepancies.

## Core components

- Emissions calculation engine (Scope 1 & 2)
- AuditTrail model and repository (stores inputs, factors, source URLs, timestamps)
- Validation service that compares reported results with EPA data
- Exporter for SEC filing formats (10-K friendly tables and notes)

## Getting started (development)

1. Copy environment template:

   ```bash
   cp .env.example .env
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run database migrations (local / staging only):

   ```bash
   # set TEST_DATABASE_URL or DATABASE_URL in env before running
   alembic upgrade head
   ```

4. Start server (development):

   ```bash
   uvicorn app.api_server:app --reload --port 8000
   ```

## Tests

- Use `TEST_DATABASE_URL` to ensure tests do not touch production DB.

   ```bash
   export TEST_DATABASE_URL="sqlite:///./test.db"
   pytest -q
   ```

## Notes on production

- Do NOT commit production secrets. Store `DATABASE_URL` and other credentials in your deployment secrets manager.
- Always backup production DB before running migrations.

## Project status

- This repository is being re-focused from the original permit-API fork to a dedicated Envoyou SEC compliance API. Historical permit-API code is archived in `archive/permit-api` branch.

## Maintainer

- Husni Kusuma — https://github.com/hk-dev13
