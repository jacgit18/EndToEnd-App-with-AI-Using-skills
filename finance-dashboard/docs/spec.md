# Build spec — Personal Finance Dashboard

> Produced by `Skill Development/spec-drift-gate`. This is the artifact drift checks diff
> against. Anything not in the "In scope" list below is a spec amendment — write it down
> here before building it, or pull back.

## Problem framing

The owner tracks money in a spreadsheet and wants a real UI: categorized transactions,
CSV import from bank exports, and budget-vs-actual at a glance. Self-hosted, one user,
no recurring subscription.

## Tradeoffs weighed

> **Superseded 2026-09-09.** The stack is being re-derived from scratch, decision-by-decision,
> through `Architecture/tech-decision-walkthrough` — one ADR per decision under
> `docs/architecture/decisions/`. This table's earlier choices (FastAPI · React/Vite ·
> `Numeric(14,2)`/`Decimal` · derived balance · `uv` · env-var JWT) are archived at
> `docs/architecture/decisions/_archived/0001-…` as prior input, not decisions. Fill this
> section back in from the ADRs once the walkthrough is done.

## Scope boundary

In/out are the lists in `docs/architecture/scope/finance-dashboard.md`. The **out** list is
binding. "While I'm in here I'll also add recurring-transaction detection" is a spec
amendment, not a freebie.

## Controlled-experiment slice — build this first, cheap to discard

A **walking skeleton** (concrete technologies come from the `tech-decision-walkthrough` ADRs;
described here in stack-neutral terms):

- One command brings up the datastore + the API (with a `/health` endpoint) + the web app.
- The web app calls `/health` and shows a connected/unreachable badge.
- One vertical slice through every layer:
  - Full data model (all five tables) in the **initial migration** + seeded categories
  - List + create for accounts and for transactions
  - A transactions table + add-transaction form in the UI

This proves the process/container wiring, the schema + migration setup, the money-representation
round-trip, and the web-app→API path **before** auth, CSV import, budgets, and the dashboard are
built on top. If the stack choices are wrong, this is the cheap place to find out.

> Note: the slice includes a minimal accounts endpoint even though "accounts" is story S2.
> A transaction needs an account (FK), so the vertical slice can't be end-to-end without it.
> This is a deliberate, minimal inclusion — list + create only, no edit/archive yet.

## Build order after the skeleton

Follow `docs/backlog.md` in MoSCoW order: S1 auth → S2 accounts (finish) → S3 categories →
S4 transactions (finish) → S5 CSV import → S6 budgets → S7 dashboard.

## Drift log

| Date | Change | Amend or pull back |
|---|---|---|
| 2026-09-08 | Initial spec written. Walking skeleton scaffolded. | — |
| 2026-09-09 | Skeleton implementation discarded. Stack decisions reopened: "Tradeoffs weighed" superseded, walking-skeleton section made stack-neutral, ADR-0001 archived. Stack to be re-derived via `tech-decision-walkthrough`, then folded back here. | Amend — deliberate restart to build slower and reason through each technology choice. Scope (in/out), stories, and test strategy unchanged. |
| 2026-09-10 | ADR-0005: transactions are an **append-only ledger** (immutable; corrections are reversing entries). Backlog **S4** changes from "add, edit and delete transactions" to **add + void**. Account balance is a maintained column + reconciliation job (hybrid). | Amend — chosen for learning value (immutable-ledger / reversing-entry / reconciliation patterns). Reword S4 at build time; no change to what the app is *for*. |
| 2026-09-10 | ADR-0010: auth is **server-side session + `HttpOnly` cookie**, not JWT. Backlog **S1**: "signed JWT" → session cookie; `JWT_EXPIRE_MINUTES` → `SESSION_EXPIRE_MINUTES`; `AUTH_PASSWORD` → `AUTH_PASSWORD_HASH`. Adds a `sessions` table; forces HTTPS + login rate-limiting into deployment ADRs. | Amend — mechanism choice; the app is still single-user env-configured login. Reword S1 at build time. |
