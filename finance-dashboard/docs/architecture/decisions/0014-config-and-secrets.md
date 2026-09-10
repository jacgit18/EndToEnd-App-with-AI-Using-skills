# ADR 0014 — Config & secrets

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 12 (closeout audit;
  `config-and-secrets-management` territory)

## Context

Single VPS, Docker Compose (ADR-0012), solo maintainer, no compliance regime. Secrets:
`DATABASE_URL`, `AUTH_PASSWORD_HASH`, a session signing secret, the Sentry DSN. Non-secret
config: `SESSION_EXPIRE_MINUTES`, log level, the public domain.

## Decision

**A gitignored `.env` file on the VPS, read by Compose (`env_file:`); `.env.example` committed.**

- The production `.env` lives on the box only: `chmod 600`, root-owned, never in git.
- A separate dev `.env` (also gitignored) for local work; `.env.example` documents every key.
- `AUTH_PASSWORD_HASH` and the session secret are generated once with a documented command
  (e.g. `python -c "import secrets; print(secrets.token_urlsafe(32))"` / an argon2 hash helper).
- The `.env` is backed up **separately** from the `pg_dump` output, so a leaked DB backup is
  not also a leaked-secrets backup.
- No rotation policy at v1 beyond "regenerate the secret + redeploy if it leaks."
- Application reads config via `pydantic-settings` (ADR-0002), which validates presence/type at
  startup.

## Alternatives considered

- **Docker / Compose secrets** (`/run/secrets/*` files) — more "correct" isolation, but the
  ceremony pays off with Swarm/orchestrators, not a single Compose host. Lost on *ops ceremony*
  for no leak-resistance gain on a single-tenant box.
- **A secrets manager (Vault / AWS Secrets Manager / Doppler / Infisical)** — overkill for one
  box; real value appears with multiple environments or a team.
- **SOPS-encrypted `.env` committed to git** — the lightweight "secrets in git" option; adds a
  key-management step. Noted as an *optional learning upgrade*, not adopted now.

## Consequences

- Simplest thing that fits a single-host deploy; standard for this shape.
- The secret file is plaintext on disk — acceptable on a box the owner solely controls;
  a secrets manager (or SOPS) is the v2 move if environments or people multiply.
- Startup fails fast if a required key is missing (pydantic-settings).
