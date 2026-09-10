# ADR 0004 — Datastore

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 3 of the stack
  (load-bearing — `database-architecture` + `technical-cost-decision` lenses folded in)

## Context

Python + FastAPI backend (ADR-0002, ADR-0003) for a single-user, self-hosted personal finance
dashboard. The app owns its data outright — no other system reads or writes it. Workload:
read-heavy dashboard aggregations (income/expense/net per month, spending-by-category vs budget,
6-month cash-flow trend), modest writes (manual entry + periodic CSV import). Consistency
matters in one place: CSV import must be an atomic batch with row-level dedupe. Scope cost cap:
~$0, the owner's machine or a small VPS.

## Decision

**PostgreSQL**, run as a container (its own service in the compose file, on a named volume).
The same image is used in development and in deployment.

## Alternatives considered

- **SQLite** — lost on *money-type fidelity* (no native exact-decimal type; precision would be
  entirely the application's responsibility) and *dashboard query power* (thinner planner and
  function set for multi-table group-by / rollups). Its genuine wins — zero operational surface,
  backup by copying one file, no server — were outweighed for a finance workload. Reasonable
  future reconsideration only if the operational simplicity ever matters more than it does now.
- **Document store (MongoDB, etc.)** — wrong data shape. Accounts → transactions → categories
  and budgets keyed by (category, month) are relational, and every dashboard view is a join +
  aggregation.

## Cost perspective (Cost Surface for this decision)

- **Recurring dollars: no material difference.** Both candidates fit the same ~$5/mo 1 GB VPS;
  self-hosted Postgres-in-a-container vs in-process SQLite is a ~30–50 MB RAM delta, not a tier
  change. No per-request or per-GB charge either way. Managed Postgres ($0–25/mo entry) is out
  of scope (self-hosted requirement) unless revisited.
- **Dominant cost line: one-time engineer time.** Postgres adds ~2–4 hrs of setup (compose
  service, connection wiring, volume, `pg_dump` backup job) plus occasional container
  troubleshooting. SQLite adds ~none.
- **Offsetting:** Postgres avoids a future data-migration cost if the app ever grows past one
  user or moves to hosting, and dev/prod image parity removes a class of environment bug
  (an engineer-time saving). At this scale the setup time is accepted, and doubles as
  intentional learning.

## Consequences

- Money is stored in an exact decimal column (`NUMERIC`) — the specific precision/scale and the
  Python-side representation are ADR-0005 (money representation).
- The compose file gains a `db` service with a healthcheck and a named volume; the backend gets
  a connection string via environment configuration.
- Backups are `pg_dump` on a schedule (or volume snapshots) — a small operational task that
  SQLite would not have required.
- Migrations run against a live server — the migration tool choice is ADR-0006 (data-access
  layer + migrations).
- If single-user assumptions ever change, Postgres scales without a datastore rewrite.
