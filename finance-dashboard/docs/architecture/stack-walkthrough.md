# Stack walkthrough — reasoning log

> Companion to the ADRs in `decisions/`. The ADRs are the terse decision records; this file
> keeps the fuller reasoning, the option comparisons, and the teaching notes from the
> `Architecture/tech-decision-walkthrough` session (started 2026-09-09). Running log — appended
> per decision. A summary sits at the bottom once all decisions are made.

Register: collaborative. Prior input (not a constraint): archived `decisions/_archived/0001-…`.

Decision list, dependency order: 1 language · 2 web framework · 3 datastore · 4 money
representation · 5 data-access layer + migrations · 6 API style · 7 frontend · 8 auth ·
9 packaging · 10 deployment · 11 observability.

---

## Decision 1 — Language / runtime → **Python ≥3.13** ([ADR 0002](decisions/0002-language-runtime.md))

**Candidates:** Python · Node/TypeScript · Go.

**Axes:** (1) the maintainer's fluency / learning runway · (2) money + migration ecosystem fit
· (3) deployment footprint · (4) type safety at the money boundary. Dropped concurrency —
1–2 users, decides nothing.

**How it scored:** Python strong on 1 (most prior exposure) and 2 (`decimal.Decimal` in the
stdlib, Alembic is the most battle-tested migration tool). Node's real win: one language +
shared types across backend and a JS frontend. Go's real win: a tiny static-binary container
and the simplest deploy.

**Call:** Python — on learning runway + money/migration maturity. Cost accepted: heaviest
container image (Go wins outright), two languages in the codebase (Node wins the one-toolchain
point).

**Objective-best aside (learning held out):** language is a near-tie between Python and
TypeScript; the deciding axis is "separate JS frontend?" — yes here, so TS-everywhere (one
language, shared types) is what many would pick. Python stays a co-best on money correctness.
The *framework* pick below is unaffected by the learning consideration.

**Python version:** annual releases, ~5-yr support each. 3.11 brought a big speedup + better
tracebacks; 3.12 better errors; 3.13 experimental no-GIL; 3.14 (Oct 2025) continues. Floor
`>=3.13`, run 3.13/3.14. Ecosystem has long since caught up to 3.14.

---

## Decision 2 — Web framework → **FastAPI** ([ADR 0003](decisions/0003-web-framework.md))

**Candidates:** FastAPI · Django + DRF · Flask.

**Axes:** (1) validation at the money/CSV boundary · (2) "see how it fits together" learning
value · (3) batteries included (ORM/migrations/auth/admin) · (4) concept load now.

**How it scored:** FastAPI strong on 1 (typed Pydantic request/response models) and 4 (small,
though `async` arrives early). Django's real win: built-in admin CRUD UI + built-in auth +
one framework does everything — weakened here by the separate-SPA architecture and its large
learning surface. Flask's real win: the most direct "wire every piece yourself" learning; loses
on 1 (no built-in validation).

**Call:** FastAPI — typed money-input validation for free + small enough to understand whole +
natural fit for a separate frontend. Cost accepted: no admin UI, no built-in auth (decision 8
becomes real work), meet `async` before strictly needed. This is also the learning-neutral pick
for "Python behind an SPA" — the learning thumb only pressed on decision 1.

---

## Decision 3 — Datastore → **PostgreSQL, containerised** ([ADR 0004](decisions/0004-datastore.md))

**Candidates:** PostgreSQL · SQLite · (document store — ruled out, wrong shape).

**`database-architecture` lens:** app owns its data outright, no other consumers · read-heavy
dashboard + modest writes · transactions matter only for atomic CSV import.

**Axes:** (1) money-type fidelity · (2) dashboard query power (joins, group-by, rollups) ·
(3) operational simplicity · (4) fit to data shape.

**How it scored:** Postgres strong on 1 (native `NUMERIC`), 2, 4. SQLite's real win: zero
operational surface — one file, backup by copying it, no server; loses on 1 (no true decimal —
precision becomes app code's job) and slightly on 2.

**Cost — two reads:**
- *This plan:* a wash. Both fit the same ~$5/mo 1 GB VPS; container Postgres vs in-process
  SQLite is ~30–50 MB RAM, not a tier change. The real difference is ~2–4 hrs more one-time
  setup for Postgres (compose service, volume, `pg_dump` job) — offset by dev/prod image parity
  and avoiding a future migration.
- *Realistic scale (50k MAU, ~300M transaction rows, 60–120 GB):* self-hosted Postgres
  primary+replica ≈ $250–500/mo compute + storage/backups, plus operator time; managed (RDS /
  Cloud SQL Multi-AZ) ≈ $350–650/mo, buys back the ops time; Aurora Serverless v2 / Neon scale
  ≈ $150–450/mo, flexes with load. SQLite: not viable past ~1 writer — the deferred cost is a
  data migration (days–weeks of eng time, ~$10k–50k loaded, plus cutover risk). Dominant line
  at scale: the DB instance pair + (if self-hosting) operator time.

**Call:** PostgreSQL, run as its own container/service, same image dev and deploy. Cost
accepted: a service to run and back up. Reason: exact money type in the DB + the dashboard is
exactly Postgres's join-and-aggregate strength; and the container setup is itself worthwhile
learning that transfers to bigger projects.

---

## Decision 4 — Money representation → [ADR 0005](decisions/0005-money-representation.md)

Three sub-questions: (a) type · (b) balance stored/derived/hybrid · (c) CSV dedupe key.

### (a) Type → **`NUMERIC(14,2)` in Postgres + Python `Decimal` end-to-end, never `float`**

**Candidates:** exact decimal (`NUMERIC`+`Decimal`) · integer minor units (`BIGINT` cents +
`int`) · float — ruled out (binary float can't represent 0.10 exactly; cents drift on sums).

**Axes:** (1) correctness/rounding safety · (2) boundary ergonomics (DB/JSON/CSV/display) ·
(3) arithmetic control (splits, %) · (4) stack fit.

**How it scored:** exact decimal strong on 2–4 (reads like money, `Decimal` rounding contexts,
clean `NUMERIC`↔`Decimal` driver mapping). Integer cents strongest on 1 — a representation
error is *structurally impossible*, not just avoided by discipline (why payment processors use
it) — but every boundary does ÷100/×100 and sub-cent needs (interest, FX) force a rescale.

**Cost axis:** none. Both are an 8-byte column; identical at every scale. Axis cut.

**Call:** exact decimal. `NUMERIC(14,2)` (max ±999,999,999,999.99, 2 dp), serialize to JSON as
a string, explicit `Decimal(str(x))` at the JSON/CSV edges, a lint rule + a unit test that
fails on any `float` in the money path. Matches archived ADR-0001 — re-derived, same result.

### (b) Account balance → **hybrid** (maintained column + reconciliation)

**Candidates:** derived (`SUM` on read, no column) · stored (column, no verification) · hybrid
(maintained column + periodic reconciliation job).

**Axes:** (1) drift risk · (2) read performance · (3) write complexity · (4) simplicity.

**Teaching note — what real banks do:** core-banking systems use a *stored, incrementally
maintained* balance, never derived-on-read — decades of rows, millisecond auth decisions. Key
enabler: the ledger is **immutable** (mistakes are fixed with reversing entries, never edits),
so a stored balance can't silently drift. They keep a running balance per row, split *ledger*
vs *available* balance, and run end-of-day reconciliation ("proof") — i.e. stored **+
verified** = hybrid. Event-sourced ledgers (TigerBeetle, Kafka-based) do the same: balance is
an incrementally-maintained projection of the transaction log.

**Why hybrid over derived here:** at this app's scale derived is fine and free of drift, and
was the initial recommendation. The user chose hybrid deliberately — to build the pattern real
systems use and get the reps (maintained column + reconciliation job). Accepted as a
learning-motivated call, not a performance need.

**Partner decision → append-only ledger.** Transactions are immutable; corrections are new
reversing entries. Real-world banking is append-only without exception — double-entry
bookkeeping, immutable audit trail for regulators/disputes, downstream-system consistency, and
point-in-time balances all depend on it; posted vs pending is the only "mutable" state, and it
resolves by settling into an immutable posting. Consumer PFM apps (Mint, YNAB) allow free
edit/delete because they're a *view*, not a system of record. Chosen here on the **learning
axis**: append-only teaches immutable/event-log data modeling (transfers to event sourcing,
CQRS, audit logs), reversing-entry mechanics, pending-vs-posted state, and reconciliation —
all transferable to fintech and systems design. Editable would only teach the narrower
stored-aggregate-consistency-under-mutation lesson. Cost: backlog **S4** amended from
"add/edit/delete" to **add + void**; `type` + `reverses_transaction_id` columns; the
transactions UI shows reversals rather than removing rows. The balance-maintenance logic gets
*simpler* — it only ever adds. Double-entry (two accounts per transaction) deferred to a later
ADR; v1 stays single-sided but immutable.

### (c) CSV dedupe key → **content hash**, bank-ID as an opt-in upgrade

**Candidates:** content hash (`sha256` of normalized date|amount|description) · bank-provided
txn ID · composite natural key · no dedupe.

**Axes:** (1) reliability (false negatives vs false positives) · (2) dependence on CSV format ·
(3) implementation cost.

**How it scored:** content hash independent of CSV format (every export has date/amount/
description); genuine same-day identical charges collide (rare, usually the wanted behavior).
Bank txn ID is strongest *when present* but many exports lack a stable one.

**Call:** `sha256(date_iso + "|" + amount(2dp) + "|" + lower(trim(collapse_ws(description))))`,
stored on the row, unique per `(account_id, hash)`; import skips + counts conflicts. Keep the
normalization in one unit-tested function (the test plan flags it as a priority unit). Prefer a
bank's stable ID for that import path when the CSV carries one. Exact field set stays tunable.

---

---

## Decision 5 — Data-access layer + migrations → **SQLAlchemy 2.0 ORM + Alembic** ([ADR 0006](decisions/0006-data-access-and-migrations.md))

**Candidates:** SQLAlchemy 2.0 ORM + Alembic · SQLAlchemy Core + Alembic (no ORM) · SQLModel +
Alembic. (Raw `psycopg` + hand-rolled migrations — noted and dismissed: re-solves migration
versioning.)

**Concept primer:** *ORM* = Python classes ↔ SQL, rows become objects (convenient, hides SQL,
own concepts: session/unit-of-work, lazy loading). *Core* = compose SQL in Python, get rows
(still think in SQL, get pooling/param-binding/dialects free). *Migrations* = every schema
change is a versioned, ordered, reversible script so dev/prod stay in lockstep and data
survives changes.

**Axes:** (1) learning value (SQL fluency vs ORM patterns) · (2) query power for the hard parts
(dashboard aggregations, maintained/reconciled balance, partial indexes, append-only
constraints) · (3) what real projects use · (4) boilerplate · (5) FastAPI/Pydantic fit.

**How it scored:** ORM+Alembic strong on 1 (if raw SQL is used deliberately for the hard
queries), 2 (full escape hatch to SQL), 3 (the default). Core-only is the sharpest for SQL
fluency specifically but less common alone and more row-mapping boilerplate. SQLModel is the
least code + tightest FastAPI fit but hides the most and fights triggers/constraints.

**Call:** SQLAlchemy 2.0 ORM + Alembic, with dashboard aggregations and ledger-maintenance
logic written in raw SQL / Core on purpose (learn both). Cost accepted: the ORM's own concept
load. Core-only is a valid override if pure SQL fluency were the single priority.

**Migrations — needed here?** Yes. You'll have real imported data that "drop and recreate"
would destroy; migrations are a core professional skill being relearned; the append-only
ledger's triggers/constraints/partial-indexes want versioned reversible scripts; cost is tiny
(~20 lines config + autogenerate drafts). Used from the first commit — the walking skeleton
ships the full model as the initial Alembic migration.

**Knex.js note:** Knex bundles query-builder + migrations in one lib. Python splits them:
SQLAlchemy (query layer) + Alembic (migrations), designed together. One-library analogues:
Piccolo, Peewee + playhouse, Tortoise + Aerich, Django ORM + Django migrations. Non-ORM
migration tools: yoyo, dbmate, Atlas (declarative diffing).

---

## Decision 6 — API style → **REST / HTTP-JSON + OpenAPI** ([ADR 0007](decisions/0007-api-style.md))

**`api-interface-style` lens (inputs confirmed, gate not re-run):** one surface (browser SPA ↔
FastAPI); one consumer, same repo, internal, free to churn; request→response only; fixed
resources + computed dashboard reads; no real-time need; browser must speak it over HTTP.

**Candidates:** REST/HTTP-JSON · GraphQL · gRPC-web. (WebSocket/SSE dismissed — no real-time.)

**Axes:** (1) fit to the consumer · (2) query-variability payoff · (3) framework fit · (4) operational weight.

**How it scored:** REST strong on all — native FastAPI + auto OpenAPI docs, browser speaks it
trivially, lowest weight. GraphQL's client-shaped-query flexibility is dead weight with one
known client and adds a resolver layer + N+1/depth-limiting + a second schema. gRPC needs a
browser proxy — wrong tool for a browser edge.

**Call:** REST/HTTP-JSON. Resource endpoints + a few computed dashboard read-model endpoints
(a view, not a resource — fine in REST). OpenAPI spec → generated typed TS client for the
frontend (recovers some end-to-end type safety). Deferred: versioning scheme, auth scheme
(decision 8), pagination conventions.

---

## Decision 7 — Frontend approach → **React + Vite (TypeScript)** ([ADR 0008](decisions/0008-frontend.md))

**Owner context:** prior React experience; no Vite experience; frontend is the weaker area.

**Candidates:** React + Vite · Vue + Vite · Svelte/SvelteKit. (Server-rendered + htmx — rejected,
CSV wizard needs rich local state. Next/Remix — rejected, adds a second server.)

**Axes:** (1) fit to interactive parts (CSV wizard, charts) · (2) transferability · (3) ecosystem
(charts/tables/forms) · (4) concept load.

**How it scored:** all three fit the interactive parts. React wins transferability (dominant
skill + owner already knows it) and ecosystem (deepest chart/table/form selection). Vue and
Svelte are gentler to learn and lower boilerplate — the axis React loses.

**Call:** React + Vite + TanStack Query. Cost accepted: steepest of the three learning curves,
softened by existing React exposure.

**What Vite is:** a build tool + dev server replacing CRA/webpack. Dev = instant start + hot
module replacement via native ES modules; prod = Rollup bundle to static files. Key config here:
the dev proxy forwards `/api` to FastAPI so dev is single-origin (no CORS) — the "web-app → API
path" the walking skeleton proves.

**Feeds build-time decisions** (already deferred in the scope): a component/UI library (Mantine
/ shadcn) and a charting library (Recharts) — both leaning "batteries included" given the
weaker-frontend constraint. `incremental-build-pacing` expected to go slow on the frontend.

---

## Decision 7b — Frontend state management → **no dedicated global-state library** ([ADR 0009](decisions/0009-frontend-state-management.md))

**Framing:** split state by category, decide per category — not one global store.
- Server state / cache → **TanStack Query** (already chosen). ~80% of this app's state.
- URL state (month, account filter, page) → **React Router** (URL is the state).
- Local UI state (forms, modals, wizard step) → `useState` / `useReducer`.
- Global client state (authed user, toasts, theme) → `useContext` + `useState` — and there's
  very little of it.

**Dedicated global-state lib?** Candidates: none · Zustand/Jotai (minimal) · Redux Toolkit
(full). Axes: fit to actual global-client-state need · boilerplate/concept load · weight ·
transferability.

**Call:** none. TanStack Query already removed the classic reason to reach for Redux (server
cache). Add **Zustand** only if a concrete global-client-state pain appears. Redux deferred on
purpose — bolting it onto an app without the problem teaches boilerplate, not judgement.

**Backend aside:** no equivalent decision — a well-built API keeps handlers stateless, pushes
durable state to the DB; a server-side session store (if auth picks it, ADR-0010) is the one
deliberate piece of backend state.

---

## Summary

_(filled in once decisions 8–11 are done)_
