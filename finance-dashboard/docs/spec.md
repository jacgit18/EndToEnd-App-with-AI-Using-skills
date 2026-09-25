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
| 2026-09-24 | ADR-0012 deployment amended for a **$0 budget**: run on the owner's machine behind a Cloudflare quick tunnel (free HTTPS URL, no domain, no open ports) instead of a ~$5-7/mo VPS + ~$12/yr domain. Same Compose + Caddy stack, TLS terminated by the tunnel; adds `compose.prod.yaml`, `Caddyfile.prod`, `frontend/Dockerfile.prod`, `scripts/backup-db.sh`, `docs/deploy.md`. Sentry (ADR-0013) deferred to its own increment. Paid upgrade path documented in the files. | Amend — the hosting choice, not the architecture; VPS + domain remains the recommended serious setup. Trade-off accepted: up only while the machine is, URL changes on tunnel restart. |
| 2026-09-24 | **Phase 2 (accounts) built.** Additions beyond the S2 wording: accounts gain a required `type` (checking / savings / credit_card / cash) and an editable `starting_balance` (balance = starting_balance + SUM(transactions), ADR-0005); every writer of `balance` locks the account row; an **archived account rejects new transactions (409)**; money amounts with 13-14 integer digits are rejected with 422 (previously a JSON number reached Postgres NUMERIC(14,2) and caused a 500); reconciliation job `app/reconcile.py` (read-only, exit 0/1/2) with its cron line in `docs/deploy.md`; accounts page (list, create, edit, archive, show-archived). | Amend: `starting_balance`, `type` and the archived-409 rule are new decisions inside S2's intent; the rest is the S2 scope as written. |
| 2026-09-24 | **Phase 3 (categories) built.** Additions beyond the S3 wording: categories gain `is_archived` and a DB CHECK on `kind` (migration 0003); **`kind` is immutable** through the API (flipping it would silently re-bucket past transactions); **no delete**, archive only; an **archived category rejects new transactions (409)** and a **nonexistent `category_id` now returns 404** (was a 500 from the foreign key); the category row is read `FOR SHARE` so an archive can't slip between the check and the insert. Categories page (list, create, rename, archive, show-archived). No category picker exists on the transaction form yet, so "hidden from pickers" is enforced only by the API default and the 409 until that form lands. | Amend: `kind` immutability, archived-409 and the 404 are new decisions inside S3's intent; the rest is S3 as written. |
| 2026-09-24 | **Phase 4 (transactions: add + void) built.** S4's "edit and delete" is **add + void** per ADR-0005. Decisions inside S4's intent: a void posts a reversing row (`type=reversal`, amount negated, same account and category, **the original's date** so that month nets to zero); a row can be voided once (partial unique index `uq_transaction_one_reversal`, migration 0004, plus a router pre-check), a reversal can't be voided (re-post the entry instead); a **void on an archived account is refused (409)**, while a void of a row whose **category is archived works**; the account row is locked so a void racing a post keeps `balance == starting_balance + SUM`. Create now rejects **zero amounts**, blank/control-character descriptions and unknown fields. List filters `?month=YYYY-MM&account_id=`. Transactions page: category picker (archived hidden), month + account filters, Void with a confirm dialog, voided rows struck through. This is the first UI to use categories, so S3's "hidden from pickers" is now true end to end. | Amend: zero-amount rejection, reversal-uses-original-date and archived-account-409 are new decisions; the rest is S4 as amended by ADR-0005. |
| 2026-09-25 | **Phase 5 (CSV import) built: S5a backend + S5b mapping UI.** Decisions inside S5's intent: amounts with >2 decimals or non-thousands commas are **rejected, not rounded** ("1.234" / "1,50" could be European 1234 / 1.5); date format is **required and never guessed**; dedupe hash = sha256(date|amount|description|occurrence-index), **counted per account within the file**, amending ADR-0005's key so two identical same-day rows both import while a re-import skips all; bad rows are rejected with line numbers rather than failing the file; UTF-8 only, 2 MB, 5000 rows. **Scope change: S5's "not covered: multiple accounts in one file" is now covered** — a real export (SoFi, 16 accounts in one file) needs it. The mapping gains `account_column` + `account_map` (value → account id, or null to leave those rows out); one `import_batch` per account; every mapped account is locked in ascending id order in one DB transaction. Import stays disabled in the UI until every account value is decided. Known gap: hand-entered rows have no hash, so an import can duplicate one. | Amend: multi-account files pulled into S5; amounts/ hash/ date-format rules are new decisions inside S5. |
