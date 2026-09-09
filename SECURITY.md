# Security

## Scope of this document

This describes the security posture of the **CDT2 (Cybersecurity Digital Twin)
application itself** (the software you're running), not the risk-scoring
subject matter it analyzes. For how asset risk is calculated, see
`ARCHITECTURE.md`.

## What credentials this application does and does not store

**Stored:** an Argon2 hash of each user's *application login* password
(`users.hashed_password`), via `passlib`. Nothing else credential-shaped
is stored anywhere in the schema.

**Never stored, never requested:** real passwords for any modeled asset,
private keys, API secrets, session cookies, or OAuth tokens belonging to
the systems being modeled. `Asset` (see `models.py`) has fields like
`authentication_type` and `mfa_enabled` — metadata *about* an asset's
auth posture — and no field for an actual credential. This matches
Section 27/28 of the original specification.

## Authentication

- JWT bearer tokens (`python-jose`), signed with `JWT_SECRET` (must be
  overridden in production — the default in `.env.example` is a
  placeholder and is not safe to deploy with).
- Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60).
- Every non-auth route depends on `get_current_user`, which validates
  the JWT and loads the user from the database on every request.

## Authorization

A `role` field (`analyst` / `admin`) exists on `User` and a
`require_admin` dependency is implemented in `app/api/deps.py`, but no
route currently uses `require_admin` — in this build every
authenticated user can read and write all data. Restricting write
operations (asset creation/deletion, relationship changes) to `admin`
is a straightforward follow-up: swap `Depends(get_current_user)` for
`Depends(require_admin)` on the relevant routes in `app/api/routes/`.

## Input validation

All request bodies are validated by Pydantic schemas
(`app/schemas/schemas.py`) before reaching any database or business
logic code.

## What is NOT yet implemented

Being direct about gaps, per this project's own "don't fabricate"
principle:

- **Rate limiting** — not implemented. Recommended: `slowapi` or a
  reverse-proxy-level limiter in front of `/api/auth/login`.
- **Audit logging** — the `security_events` table exists for
  environment events (e.g. "unusual OAuth scope granted") but there is
  no separate audit log of *user actions* (who changed which asset,
  when). Recommended: an `audit_log` table plus a small SQLAlchemy
  event-listener or FastAPI middleware.
- **CORS** — configured via `CORS_ORIGINS` in `.env`, defaulting to
  `http://localhost:5173` only. Update this for any real deployment.
- **HTTPS/TLS** — not handled by the application itself; terminate TLS
  at a reverse proxy (nginx, Caddy, a cloud load balancer) in any real
  deployment.
- **Secrets management** — `.env` is git-ignored and `.env.example`
  contains only placeholders; no secrets manager integration (Vault,
  AWS Secrets Manager, etc.) exists yet.
- **Dependency scanning / SAST** — not configured in this repository.

## Reporting a vulnerability in this codebase

This is a project scaffold, not a maintained product with a disclosure
program. If you find a security issue while extending it, fix it
directly and note the change in your own project's changelog.
