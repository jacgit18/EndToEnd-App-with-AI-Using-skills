# ADR 0012 — Deployment target

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 10 (`deployment-strategy`
  lens; scope constraints mostly fix it)

## Context

Scope: self-hosted, ~$0 cost cap, single region, "a restart is acceptable" (no HA). ADR-0010
adds: **public URL over HTTPS** and **login rate limiting**. Owner goal: go through the whole
deployment process hands-on, not have it abstracted. Components: Postgres, FastAPI backend,
built React static files.

## Decision

**Single small VPS (~$5–7/mo) running Docker Compose, with Caddy as the reverse proxy and TLS
terminator.**

- Compose services: `db` (Postgres + named volume), `backend` (FastAPI via `uv`), `caddy`
  (reverse proxy).
- Caddy auto-provisions and renews a Let's Encrypt certificate; it serves the built React
  static files and proxies `/api` + `/health` to the backend — one origin, which ADR-0010's
  cookie auth needs.
- Login rate limiting: Caddy `rate_limit` (or FastAPI middleware) on `POST /api/auth/login`.
- Backups: `pg_dump` on a cron (or a volume snapshot), dumps stored off-box.
- Deploys: `docker compose pull && docker compose up -d` (rolling). A brief restart is
  acceptable per scope.
- A registered domain (~$12/yr) with an A record to the VPS.

## Alternatives considered

- **PaaS (Render / Railway / Fly.io)** — genuinely removes the ops burden (TLS, deploys, DB
  backups). Lost on *learning value* (abstracts the mechanics the owner wants to do) and
  *dev/prod parity*; free tiers sleep/throttle, ~$7–20/mo for always-on + a DB.
- **Serverless (Lambda + API Gateway + Aurora Serverless, or Cloud Run)** — lost on *fit to
  scope* (not self-hosted), plus an awkward Lambda↔Postgres connection story and heavy vendor
  surface for one user.
- **Bare metal on the VPS (systemd, no containers)** — lost on *dev/prod parity* (ADR-0004
  valued the same image both places) and *ops fiddliness*.

## Cost perspective

- **This plan:** ~$5–7/mo VPS + ~$12/yr domain. Caddy makes TLS free and automatic. The real
  cost is owner time: OS patching, the backup cron, disk monitoring — the burden a PaaS would
  absorb, accepted here because doing it is the goal.
- **Realistic scale (~50k MAU):** re-platform off a single box — PaaS or a small ECS/Kubernetes
  setup with managed Postgres + a load balancer + a CDN for the static frontend. Dominant
  lines: DB pair $250–600/mo (per ADR-0004), app compute (2–4 instances) $50–200/mo,
  CDN/egress $20–100/mo. A deliberate future migration, not provisioned now.

## Consequences

- Owner operates the box: updates, backups, disk. No HA — a reboot means a short outage
  (accepted).
- HTTPS + one origin are in place from first deploy, which ADR-0010's cookie auth requires.
- `deployment-strategy` proper (rollout mechanics, blue/green, etc.) is out of scope at one
  box / one user — revisit with the scale re-platform.
- Observability approach is ADR-0013 (decision 11).
