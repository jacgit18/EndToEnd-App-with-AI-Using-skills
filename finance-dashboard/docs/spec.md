# Build spec — Personal Finance Dashboard

> Produced by `Skill Development/spec-drift-gate`. This is the artifact drift checks diff
> against. Anything not in the "In scope" list below is a spec amendment — write it down
> here before building it, or pull back.

## Problem framing

The owner tracks money in a spreadsheet and wants a real UI: categorized transactions,
CSV import from bank exports, and budget-vs-actual at a glance. Self-hosted, one user,
no recurring subscription.

## Tradeoffs weighed

| Decision | Chosen | Alternative & why it lost |
|---|---|---|
| Backend framework | **FastAPI** | Django + DRF — its admin is genuinely useful for eyeballing financial records, but a separate-SPA architecture, Pydantic money validation, and a lighter footprint matter more for a solo MVP. |
| Frontend | **React + Vite SPA** | Streamlit / Dash — faster to a first chart, but no real separate frontend container and little UX control; the owner wants front/back containerized separately. |
| Money type | **`Numeric(14,2)` + Python `Decimal`** | Integer cents — removes all float risk but makes every display and CSV row do conversions. `Decimal` end-to-end is safe enough and simpler. |
| Account balance | **Derived** (`starting_balance + sum(transactions)`) | Stored balance — faster but drifts and needs reconciliation; the sum is instant at single-user volume. |
| Python packaging | **`uv`** | Poetry (heavier), `pip` + `requirements.txt` (no lockfile). |
| Auth | **Single user from env vars → JWT** | A `user` table — unnecessary for one self-hosted user in v1. |

## Scope boundary

In/out are the lists in `docs/architecture/scope/finance-dashboard.md`. The **out** list is
binding. "While I'm in here I'll also add recurring-transaction detection" is a spec
amendment, not a freebie.

## Controlled-experiment slice — build this first, cheap to discard

A **walking skeleton**:

- `docker compose up` brings up Postgres + FastAPI (`/health`) + the Vite app.
- The SPA fetches `/health` and shows a connected/unreachable badge.
- One vertical slice through every layer:
  - Full data model (all five tables) in the **initial Alembic migration** + seeded categories
  - `GET/POST /api/accounts` and `GET/POST /api/transactions`
  - A transactions table + add-transaction form in the UI

This proves the container wiring, the SQLAlchemy 2.0 + Alembic setup, the money type
round-trip, and the Vite→FastAPI proxy path **before** auth, CSV import, budgets, and the
dashboard are built on top. If the stack choices are wrong, this is the cheap place to find
out.

> Note: the slice includes a minimal `accounts` router even though "accounts" is story S2.
> A transaction needs an account (FK), so the vertical slice can't be end-to-end without it.
> This is a deliberate, minimal inclusion — list + create only, no edit/archive yet.

## Build order after the skeleton

Follow `docs/backlog.md` in MoSCoW order: S1 auth → S2 accounts (finish) → S3 categories →
S4 transactions (finish) → S5 CSV import → S6 budgets → S7 dashboard.

## Drift log

| Date | Change | Amend or pull back |
|---|---|---|
| 2026-09-08 | Initial spec written. Walking skeleton scaffolded. | — |
