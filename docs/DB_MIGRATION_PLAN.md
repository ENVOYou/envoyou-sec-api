# DB Migration Plan — Envoyou SEC API (Supabase / Postgres)

This plan standardizes schema versioning and safe migrations from development to production.

## Tools

- Alembic (SQLAlchemy migrations) — primary
- Supabase (managed Postgres) — target production & staging

## Environments

- Local dev: SQLite (default) or local Postgres
- Staging: Supabase project (separate from production)
- Production: Supabase project

## Baseline

- Alembic initialized; `alembic/env.py` targets `Base.metadata`
- No hardcoded creds in `alembic.ini`; use `DATABASE_URL` env

## Workflow

1. Model changes
   - Edit SQLAlchemy models
   - Generate migration:
     - `alembic revision --autogenerate -m "<summary>"`
   - Review generated script under `alembic/versions/`

2. Local verification
   - Set `DATABASE_URL` (local Postgres/SQLite)
   - `alembic upgrade head`
   - Run tests

3. Staging rollout
   - Set `DATABASE_URL` for staging (Supabase)
   - Backup: `pg_dump` (required)
   - Preview SQL: `alembic upgrade --sql head > migration.sql`
   - Apply: `alembic upgrade head`
   - Smoke tests

4. Production rollout
   - Maintenance window
   - Backup: `pg_dump` (required)
   - Preview SQL & review
   - Apply: `alembic upgrade head`
   - Post-checks & monitoring

## Safety

- Never commit production credentials
- Use GitHub Actions secret to pass `DATABASE_URL`
- Always backup before migrate
- Keep migrations idempotent and reversible (`downgrade` implemented when feasible)

## Rollback

- `alembic downgrade -1` (step back) or pin to specific revision
- Restore from `pg_restore` if necessary
