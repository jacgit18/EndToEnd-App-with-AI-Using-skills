# Build spec — Personal Finance Dashboard

> Produced by `Skill Development/spec-drift-gate`. This is the artifact drift checks diff
> against. Anything not in the "In scope" list below is a spec amendment — write it down
> here before building it, or pull back.

## Problem framing

The owner tracks money in a spreadsheet and wants a real UI: categorized transactions,
CSV import from bank exports, and budget-vs-actual at a glance. Self-hosted, one user,
no recurring subscription.

## Stack — decided (see ADRs)

Re-derived decision-by-decision via `Architecture/tech-decision-walkthrough` (2026-09-09/10).
Each row's reasoning — candidates, axes, why the alternatives lost — is in the linked ADR;
the running commentary is in `docs/architecture/stack-walkthrough.md`. The pre-walkthrough
picks are archived at `docs/architecture/decisions/_archived/0001-…`.

| Area | Decision | ADR |
|---|---|---|
| Language / runtime | Python ≥3.13 | 0002 |
| Web framework | FastAPI | 0003 |
| Datastore | PostgreSQL, containerised | 0004 |
| Money type | `NUMERIC(14,2)` + Python `Decimal`, never `float`; JSON as string | 0005 |
| Account balance | Maintained column + reconciliation job, on an **append-only ledger** (immutable rows; corrections = reversing entries; `type` + `reverses_transaction_id`) | 0005 |
| CSV dedupe key | `sha256(date_iso \| amount_2dp \| normalized description)`, unique per `(account_id, hash)`; bank-ID opt-in | 0005 |
| Data-access + migrations | SQLAlchemy 2.0 ORM + Alembic (raw SQL / Core for aggregations + ledger maintenance) | 0006 |
| API style | REST / HTTP-JSON + OpenAPI; resource endpoints + computed dashboard read-models; generated TS client | 0007 |
| Frontend | React + Vite + TypeScript + TanStack Query | 0008 |
| Frontend state | No global-state library — TanStack Query (server) + React Router (URL) + `useState`/`useContext` | 0009 |
| Auth | Server-side session + `HttpOnly; Secure; SameSite=Lax` cookie; same-origin SPA+API; `AUTH_PASSWORD_HASH` (argon2); CSRF token on writes; login rate-limited | 0010 |
| Packaging | `uv` | 0011 |
| Deployment | Single small VPS + Docker Compose + Caddy (auto Let's Encrypt, serves the SPA, proxies `/api`); `pg_dump` cron backups | 0012 |
| Observability | Structured JSON logs to stdout + Caddy access logs + Sentry free tier + `/health` + uptime ping | 0013 |
| Config & secrets | Gitignored `.env` on the VPS (`chmod 600`, root) + committed `.env.example`; secrets backed up separately from DB dumps | 0014 |
| Frontend test tooling | Vitest + React Testing Library; Playwright for the one E2E smoke | 0015 |
| CI | GitHub Actions — lint + `pytest` (unit + integration w/ Postgres service) + `alembic upgrade head` + FE typecheck/vitest/build; Playwright local-only | 0016 |

**Deferred to build-time:** component/UI library (lean Mantine/shadcn), charting library (lean
Recharts), CSV column-mapping UX, exact dedupe-hash field set, `SESSION_EXPIRE_MINUTES` value,
transactions-list pagination, dashboard aggregation query shapes, date/time & timezone policy
(transaction `date` = SQL `DATE`; audit timestamps `timestamptz` UTC; `Intl` formatting on the
FE), container base images (`python:3.13-slim`; multi-stage node build → static files via Caddy).
**Deferred to v2:** multi-user + a real `users` table, double-entry bookkeeping, the scale
re-platform (managed Postgres, CDN, metrics stack).

## Scope boundary

In/out are the lists in `docs/architecture/scope/finance-dashboard.md`. The **out** list is
binding. "While I'm in here I'll also add recurring-transaction detection" is a spec
amendment, not a freebie.

## Controlled-experiment slice — build this first, cheap to discard

A **walking skeleton** (Phase 0 below):

- `docker compose up` brings up Postgres + the FastAPI backend (`/health`, checks the DB) +
  the Vite dev server; Caddy config present but TLS not required until Phase 1.
- The React app calls `/health` and shows a connected/unreachable badge, via the Vite `/api`
  dev proxy.
- Alembic `0001_initial` migration creates the **full data model**: the five tables
  (account, category, transaction, budget, import_batch) with the append-only ledger columns
  (`transaction.type`, `transaction.reverses_transaction_id`), the `sessions` table, and
  ~15 seeded categories.
- One vertical slice: `GET/POST /api/accounts` and `GET/POST /api/transactions`
  (append-only insert only), a transactions table + add-transaction form in the UI.
- Money round-trips as `NUMERIC(14,2)` ↔ `Decimal` ↔ JSON string; a unit test fails on any
  `float` in the money path.

This proves the container wiring, SQLAlchemy 2.0 + Alembic, the `Decimal`/`NUMERIC` round-trip,
and the Vite→FastAPI proxy path **before** auth, CSV import, budgets, and the dashboard are
built on top. If a stack choice is wrong, this is the cheap place to find out.

> Note: the slice includes a minimal accounts endpoint even though "accounts" is story S2.
> A transaction needs an account (FK), so the vertical slice can't be end-to-end without it.
> Deliberate, minimal — list + create only, no edit/archive yet.

## Build order

Phases, from `tech-decision-walkthrough`'s closeout. Rationale: dependency order → risk-first
(walking skeleton) → MoSCoW → value → learning → cross-cutting concerns slotted to first need.

| Phase | Work | Why here |
|---|---|---|
| **0** | Walking skeleton (above) | Risk-first — prove the wiring |
| **1** | **S1 auth** — session login, `AUTH_PASSWORD_HASH`, auth dependency on all routes but `/health`+login, logout, CSRF token, login rate-limit, FE login page + 401→redirect. **First real deploy:** domain + DNS + Caddy TLS (needed for `Secure` cookies), Sentry, `pg_dump` cron. | Unblocks protected routes for everything after; highest-learning; HTTPS must be real now |
| **2** | **S2 accounts finish** — edit/archive; the maintained `balance` column + insert-time maintenance + the **reconciliation job**; archived hidden from pickers; accounts CRUD UI | Transactions + dashboard need accounts and balances |
| **3** | **S3 categories** — management UI (seed already shipped) | Transactions, budgets, dashboard need categories |
| **4** | **S4 transactions finish** — **void via reversing entry** (not edit/delete); list filterable by month+account; UI shows reversals | Core interaction; app is usable after this |
| **5** | **S5 CSV import** — S5a fixed-column import (unit-tested parser, content-hash dedupe, `import_batch`, skip+count) → S5b column-mapping preview UI | MoSCoW + its stated split |
| **6** | **S6 budgets** — set/edit `(category, month)` amount; copy-forward | **Dependency beats MoSCoW rank** — S7's budget-vs-actual widget needs it |
| **7** | **S7 dashboard** — aggregation endpoints (raw SQL) + FE month picker, tiles, category-vs-budget bar, 6-month trend, recent list. **Component + charting library picked here.** | Consumes every other story's data |

**Cross-cutting, slotted (not a phase):** CI (ADR-0016) — end of Phase 0, once there are tests.
Playwright E2E smoke — after Phase 7. Backup *restore* test — after the first backup.

## Drift log

| Date | Change | Amend or pull back |
|---|---|---|
| 2026-09-08 | Initial spec written. Walking skeleton scaffolded. | — |
| 2026-09-09 | Skeleton implementation discarded. Stack decisions reopened: "Tradeoffs weighed" superseded, walking-skeleton section made stack-neutral, ADR-0001 archived. Stack to be re-derived via `tech-decision-walkthrough`, then folded back here. | Amend — deliberate restart to build slower and reason through each technology choice. Scope (in/out), stories, and test strategy unchanged. |
| 2026-09-10 | ADR-0005: transactions are an **append-only ledger** (immutable; corrections are reversing entries). Backlog **S4** changes from "add, edit and delete transactions" to **add + void**. Account balance is a maintained column + reconciliation job (hybrid). | Amend — chosen for learning value (immutable-ledger / reversing-entry / reconciliation patterns). Reword S4 at build time; no change to what the app is *for*. |
| 2026-09-10 | ADR-0010: auth is **server-side session + `HttpOnly` cookie**, not JWT. Backlog **S1**: "signed JWT" → session cookie; `JWT_EXPIRE_MINUTES` → `SESSION_EXPIRE_MINUTES`; `AUTH_PASSWORD` → `AUTH_PASSWORD_HASH`. Adds a `sessions` table; forces HTTPS + login rate-limiting into deployment ADRs. | Amend — mechanism choice; the app is still single-user env-configured login. Reword S1 at build time. |
| 2026-09-10 | Walkthrough complete (ADRs 0002–0016). Spec refreshed: "Stack — decided" table replaces the superseded "Tradeoffs weighed" banner; walking-skeleton section made concrete against the decided stack; "Build order" replaced with the phased plan (dependency → risk-first → MoSCoW → value → learning → slot cross-cutting). S6 sequenced before S7 (dependency beats MoSCoW rank). | Not an amendment — folds the settled ADRs into the spec. Scope (in/out) and stories unchanged except the S1/S4 amendments already logged. Ready for the paced build. |
