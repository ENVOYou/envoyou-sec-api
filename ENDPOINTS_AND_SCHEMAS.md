# Envoyou API — Endpoints & Schemas (Backend)

This document inventories FastAPI endpoints and Pydantic/ORM schemas defined in `api-envoyou/app` as of 2025-09-18. Paths reflect the prefixes mounted in `app/main.py`.

Notes:
- Auth has migrated to Supabase. Several legacy endpoints are deprecated (410 Gone) but kept for reference.
- Authentication for user endpoints uses Supabase JWT via middleware/depends in `routes/user.py`. Some other modules still use internal JWT for historical reasons.
- Global data endpoints require API Keys (Bearer, `X-API-Key`, or `api_key` query) and are subject to rate limiting.

## Health (`/v1/health`)
- GET `/v1/health` — Health Check
- GET `/v1/health/ready` — Readiness
- GET `/v1/health/live` — Liveness
- GET `/v1/health/test-sentry` — Throw test error
- POST `/v1/health/test-email` — Send test email (body: `email: string`)
- GET `/v1/health/redis` — Redis metrics and health

## Auth (`/v1/auth`)
Deprecated flows (now handled by Supabase):
- POST `/v1/auth/register` — 410 Gone
- POST `/v1/auth/send-verification` — 410 Gone
- POST `/v1/auth/verify-email` — 410 Gone
- GET `/v1/auth/verify-email?token=...` — Static HTML notice
- POST `/v1/auth/forgot-password` — 410 Gone
- POST `/v1/auth/reset-password` — 410 Gone

Active (legacy internal JWT for non-Supabase flows):
- POST `/v1/auth/login` — Email/password login (internal JWT). Returns `{access_token, refresh_token, user}`
- POST `/v1/auth/refresh` — Refresh token
- POST `/v1/auth/logout` — No-op server-side
- POST `/v1/auth/change-password` — Change password (Authorization: Bearer access)
- 2FA: POST `/v1/auth/2fa/setup`, `/verify`, `/disable`
- OAuth helpers (legacy, not Supabase):
  - GET `/v1/auth/google/login`
  - POST `/v1/auth/google/callback`
  - POST `/v1/auth/google/token`
  - GET `/v1/auth/github/login`
  - POST `/v1/auth/github/callback`
  - POST `/v1/auth/github/token`
- Supabase helpers:
  - POST `/v1/auth/supabase/verify` — Verify Supabase token, create/update user, mint internal tokens
  - GET `/v1/auth/supabase/me` — Echo user info from Supabase JWT

## User (`/v1/user`)
Uses Supabase JWT dependency `get_db_user` to map Supabase user → DB user.
- GET `/v1/user/profile` — Get profile (Redis cached)
- PUT `/v1/user/profile` — Update profile `{name?, company?, job_title?, timezone?}`
- POST `/v1/user/avatar` — Upload avatar (image; <5MB)
- GET `/v1/user/api-keys` — List active API keys
- POST `/v1/user/api-keys` — Create API key; returns full `key` once
- DELETE `/v1/user/api-keys/{key_id}` — Delete (soft)
- GET `/v1/user/api-token` — Personal token info (no full key)
- POST `/v1/user/api-token` — Create personal token (409 if exists)
- POST `/v1/user/api-token/regenerate` — Rotate token; returns new full key
- GET `/v1/user/sessions` — List sessions
- DELETE `/v1/user/sessions/{session_id}` — Delete session
- GET `/v1/user/plan` — Current plan
- GET `/v1/user/stats` — Usage stats summary

## Global (`/v1/global`) — requires API Key
- GET `/v1/global/emissions` — EPA/EIA fallback data with filters: `state?`, `year?`, `pollutant?`, paging `page`, `limit`, `source?`
- GET `/v1/global/emissions/stats` — Aggregated stats
- GET `/v1/global/iso` — ISO 14001 certifications `country?`, `limit`
- GET `/v1/global/eea` — EEA indicators `country?`, `indicator=GHG`, `year?`, `limit`
- GET `/v1/global/edgar` — EDGAR series/trend `country`, `pollutant=PM2.5`, `window=3`
- GET `/v1/global/cevs/{company_name}` — CEVS score `country?`
- GET `/v1/global/campd` — CAMD emissions and compliance `facility_id`

## Environmental (`/v1/environmental`) — requires API Key
- GET `/v1/environmental/us/facilities/{facility_name}` — Search facilities, `source?`

## External (`/v1/external`) — requires API Key
- GET `/v1/external/air_quality/{zip_code}` — AQI list, `use_mock?`

## Permits (`/v1/permits`)
- GET `/v1/permits` — All permits
- GET `/v1/permits/active` — Active permits
- GET `/v1/permits/stats` — Summary counts
- GET `/v1/permits/search` — Search. Depends: `PermitSearchParams` (query fields `nama`, `jenis`, `status`) and optional `q`
- GET `/v1/permits/company/{company_name}` — By company
- GET `/v1/permits/type/{permit_type}` — By type
- GET `/v1/permits/{permit_id}` — By id

## Cloudflare (`/v1/cloudflare`)
- GET `/v1/cloudflare/health` — API health
- GET `/v1/cloudflare/analytics` — Zone analytics (API key required)
- GET `/v1/cloudflare/dns` — DNS records (API key required)
- POST `/v1/cloudflare/dns` — Create DNS record
- PUT `/v1/cloudflare/dns/{record_id}` — Update DNS record
- DELETE `/v1/cloudflare/dns/{record_id}` — Delete DNS record
- GET `/v1/cloudflare/firewall` — Firewall rules
- POST `/v1/cloudflare/firewall` — Create firewall rule
- GET `/v1/cloudflare/rate-limits` — Rate limit rules
- POST `/v1/cloudflare/rate-limits` — Create rate limit
- POST `/v1/cloudflare/cache/purge` — Purge cache (all or urls)
- GET `/v1/cloudflare/ssl` — SSL/TLS status
- GET `/v1/cloudflare/page-rules` — Page rules
- POST `/v1/cloudflare/page-rules` — Create page rule

## Notifications (`/v1/notifications`)
- POST `/v1/notifications/` — Create notification
- GET `/v1/notifications/` — List user notifications (query: `user_id`, `limit`, `offset`, `unread_only`, `category?`)
- GET `/v1/notifications/count` — Count user notifications (query: `user_id`, `unread_only`)
- PUT `/v1/notifications/{notification_id}/read` — Mark read
- PUT `/v1/notifications/read-all` — Mark all read (query: `user_id`)
- DELETE `/v1/notifications/{notification_id}` — Delete
- GET `/v1/notifications/templates` — List templates
- POST `/v1/notifications/send-template` — Send by template (query: `template_key`, `user_id`; body `data` optional)
- GET `/v1/notifications/preferences/{user_id}` — Get preferences
- PUT `/v1/notifications/preferences/{user_id}` — Update preferences
- DELETE `/v1/notifications/preferences/{user_id}` — Delete preferences
- Events: POST `/v1/notifications/events/welcome`, `/events/verification`, `/events/password-reset`, `/events/security-alert`, `/events/billing`

## Payments (`/v1/payments`)
- POST `/v1/payments/create-subscription` — Create subscription (requires Authorization; body: `{price_id, custom_data?}`)
- GET `/v1/payments/subscription/{subscription_id}` — Get subscription (requires Authorization)
- POST `/v1/payments/webhook` — Paddle webhook (signature validated)

## Developer (`/v1/developer`)
- GET `/v1/developer/stats` — Usage stats (Authorization required via legacy `get_current_user`)
- GET `/v1/developer/usage-analytics?hours=24` — Recent activity window
- GET `/v1/developer/rate-limits` — Current rate limit (requires API Key)

## Contact (`/v1/contact`)
- POST `/v1/contact` — Submit contact form, triggers email to support and auto-reply

---

# Schemas

Pydantic request/response models and SQLAlchemy models used by endpoints.

## Pydantic (requests/responses)
- Auth: `UserRegister`, `UserLogin`, `TokenResponse`, `RefreshTokenRequest`, `MessageResponse`,
  `TwoFASetupResponse`, `TwoFAVerifyRequest`, `FreeAPIKeyRequest`, `FreeAPIKeyResponse`,
  `OAuthCallbackRequest`, `OAuthURLResponse`, `RegistrationResponse`, `SetPasswordRequest`, `SetPasswordResponse`.
- Supabase Auth: `SupabaseAuthRequest`, `SupabaseAuthResponse`.
- User: `UserProfileResponse`, `UserProfileUpdate`, `APIKeyResponse`, `APIKeyListResponse`,
  `APIKeyCreate`, `APIKeyCreateResponse`, `APITokenInfoResponse`, `APITokenCreateResponse`,
  `SessionResponse`, `SessionListResponse`, `UserStatsResponse`.
- External Data: `AirQualityCategory`, `AirQualityData`.
- Notifications: `NotificationCreate`, `NotificationResponse`, `NotificationPreferenceUpdate`, `NotificationPreferenceResponse`.
- Payments: `CreateSubscriptionRequest`, `SubscriptionResponse`, `WebhookEvent`.
- Permits: `PermitSearchParams` (query model).
- Contact: `ContactForm`.

## SQLAlchemy Models (database)
- `User` — users table
  - Fields: `id`, `email`, `password_hash`, `name`, `company`, `job_title`, `avatar_url`, `timezone`, `email_verified`,
    `email_verification_token`, `email_verification_expires`, `password_reset_token`, `password_reset_expires`,
    `last_login`, `two_factor_secret`, `two_factor_enabled`, `auth_provider`, `auth_provider_id`, `plan`,
    `paddle_customer_id`, `created_at`, `updated_at`.
- `APIKey` — api_keys table
  - Fields: `id`, `user_id`, `name`, `key_hash`, `prefix`, `permissions`, `is_active`, `last_used`, `usage_count`, `created_at`, `updated_at`.
  - Methods: `_generate_key()`, `verify_key()`, `update_usage()`, `to_dict()`.
- `Session` — sessions table
  - Fields: `id`, `user_id`, `token_hash`, `device_info`, `ip_address`, `location`, `expires_at`, `created_at`, `last_active`.
  - Methods: `update_activity()`, `is_expired()`, `verify_token()`, `get_device_info()`, `to_dict()`.
- Other models present but not directly used above: `external_data.AirQuality*` (Pydantic), permit models.

---

# Security & Dependencies
- Supabase JWT: `routes/user.py` uses `middleware.supabase_auth.get_current_user` mapped to DB via `get_db_user`.
- Legacy JWT: `routes/dependencies.py.get_current_user` verifies internal access tokens.
- API Key enforcement for Global/Cloudflare endpoints via `utils.security.require_api_key` and middleware in `api_server.py`.

# Deprecations
- Legacy auth flows (`register`, `send-verification`, `verify-email`, `forgot-password`, `reset-password`) are deprecated; use Supabase via frontend.

# Notes for Clients
- For `/v1/global/*` and Cloudflare routes: include API key as Bearer token, `X-API-Key`, or `api_key` query.
- For `/v1/user/*`: send Supabase access token as Bearer if backend expects Supabase JWT. Some endpoints may accept legacy internal tokens when using `/v1/auth/*` login.

