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

## Decision 4 — Money representation ([ADR 0005](decisions/0005-money-representation.md) — in progress)

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

**Open partner decision:** transactions **editable** (maintenance logic handles edit/delete)
vs **append-only ledger** (reversing entries; changes backlog S4's edit/delete UX but is the
real banking pattern). — *pending*

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

## Summary

_(filled in once decisions 5–11 are done)_
