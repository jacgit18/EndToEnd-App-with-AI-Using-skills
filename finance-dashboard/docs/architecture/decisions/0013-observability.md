# ADR 0013 — Observability

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 11 (routine tier)

## Context

Single-user, self-hosted, one small VPS (ADR-0012). No SLOs, no traffic to chart. The
signal that actually matters is unnoticed exceptions in production, plus enough log detail to
debug the append-only ledger / reconciliation logic.

## Decision

- **Structured JSON logging to stdout** from uvicorn/FastAPI; the container runtime captures
  it (`docker compose logs`, journald). Caddy access logs on.
- **Sentry (free tier)** for exception tracking — ~5 lines of SDK setup, errors sent off-box,
  5k events/mo at $0.
- The existing `/health` endpoint (DB connectivity) is the liveness signal; a simple uptime
  ping (e.g. UptimeRobot free) can watch it.
- The reconciliation job logs any balance mismatch at WARN.

## Alternatives considered

- **Logging only, no error tracker** — lost on *signal you actually need*: a prod exception
  scrolls past in logs unnoticed. Sentry's free tier closes that for $0.
- **Self-hosted Loki + Grafana** — searchable logs + dashboards, but more infra to run for a
  single user with no metrics story worth a time-series DB.
- **Full Prometheus + Grafana + Loki + Tempo** — overkill; nothing to chart at one user.

## Consequences

- Near-zero cost and ops surface.
- If Prometheus/Grafana are wanted later, add them as a deliberate learning exercise, not
  load-bearing infra.
- **Scale note (~50k MAU):** add Prometheus + Grafana (metrics, SLOs), Loki (logs),
  distributed tracing; Sentry → paid (~$26+/mo). Deliberate future move.
