# ADR 0001 — Stack and money representation

- **Status:** Accepted
- **Date:** 2026-09-08
- **Deciders:** the owner

## Context

Greenfield self-hosted personal budgeting dashboard, single user, Docker-composed. The
load-bearing decision (whole-data-model blast radius) is how money is represented and how
account balances are derived — changing either later needs a migration and a data rewrite.
A few stack choices are also contested enough to record.

## Decision

1. **Backend: FastAPI** (not Django + DRF). The app is an API behind a separate SPA;
   Pydantic gives strong money-input validation; the footprint stays small for a solo MVP.
   Django's admin would help inspect records but doesn't outweigh the above.
2. **Money: `Numeric(14,2)` in Postgres, `Decimal` in Python, end-to-end. Never `float`.**
   Integer cents was the alternative — it removes float risk entirely but forces a
   conversion on every read, display, and CSV row. `Decimal` is safe enough and simpler.
   JSON serializes `Decimal` as a string to preserve precision; the SPA treats `amount` as
   a string.
3. **Account balance is derived**, `starting_balance + sum(transactions)`, computed on
   read. A stored balance would be faster but drifts and needs reconciliation; at
   single-user data volumes the aggregate is instant.
4. **Transaction dedupe key:** `sha256(date_iso | amount_2dp | lower(trim(description)))`,
   stored on the row and indexed. Used to skip already-imported CSV rows.
5. **Packaging: `uv`** (not Poetry or bare `pip`). One tool for venv + install + lockfile.
6. **Auth: single user from env vars → JWT** (no `user` table in v1).
7. **Testing: no contract tests, no E2E in CI, BDD rejected.** See
   `docs/testing/finance-dashboard.md`.

## Consequences

- All money arithmetic uses `decimal.Decimal`; a stray `float` in the path is a bug to
  catch in review and unit tests.
- Balance endpoints do a `SUM` per request — fine now; if data ever grows past what that
  handles, revisit with a rollup table (a migration, tracked as a new ADR).
- Switching to multi-user later means introducing a `user` table and a real auth store —
  a deliberate v2 migration, explicitly out of scope now.
