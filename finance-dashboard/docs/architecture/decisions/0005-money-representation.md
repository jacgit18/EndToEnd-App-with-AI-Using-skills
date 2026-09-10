# ADR 0005 — Money representation

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 4 of the stack
  (load-bearing — highest blast radius in the scope doc)

## Context

Python + FastAPI + PostgreSQL (ADR-0002/0003/0004) for a single-user personal finance
dashboard. This decision fixes how a dollar amount is stored and carried through the code, how
an account balance is produced, and how CSV re-imports are deduplicated — three linked
sub-questions whose answers are expensive to change later (each implies a migration + data
rewrite). The project's stated goal is learning application development, and the owner has
consistently chosen the pattern real systems use over the minimal one.

## Decision

### (a) Amount type — exact decimal, end to end

`NUMERIC(14,2)` in PostgreSQL, `decimal.Decimal` in Python, **never `float`**. Amounts
serialize to JSON as strings; JSON and CSV boundaries do explicit `Decimal(str(x))`
conversion. A lint rule + a unit test fail on any `float` in the money path. `(14,2)` ⇒ max
±999,999,999,999.99, exactly two decimal places.

### (b) Account balance — hybrid, on an append-only ledger

- Transactions are an **append-only ledger**: a posted transaction is immutable. Corrections
  are new entries, not edits. Columns added: `type` (`normal` / `reversal` / `adjustment`) and
  `reverses_transaction_id` (nullable FK to the entry being reversed).
- Account balance is a **maintained column** (`accounts.balance`), updated in the same DB
  transaction as each ledger insert, plus a **reconciliation job** that recomputes
  `starting_balance + SUM(amount)` and asserts it matches (logging any drift).
- Because the ledger is immutable, the maintenance logic only ever *adds* — it never handles
  update or delete, which is what makes a stored balance safe here.

### (c) CSV import dedupe key — content hash

`sha256(date_iso + "|" + amount(2dp) + "|" + lower(trim(collapse_ws(description))))`, stored on
the row and **unique per `(account_id, hash)`**. Import skips rows whose hash already exists and
counts them. Normalization lives in one unit-tested function. If a bank's CSV carries a stable
transaction ID, that import path uses the ID instead. The exact normalized field set stays
tunable during implementation.

## Alternatives considered

- **Integer minor units (`BIGINT` cents)** — the only option where a representation error is
  structurally impossible, not merely avoided by discipline (why payment processors use it).
  Lost on *boundary ergonomics* (÷100/×100 at every DB/JSON/CSV/display edge) and *arithmetic
  control* (integer division for splits/percentages needs manual rounding); a future sub-cent
  need would force a full rescale.
- **`float` / `DOUBLE PRECISION`** — ruled out: binary floating point cannot represent 0.10
  exactly; cents drift on accumulation.
- **Derived balance** (`SUM` on read, no column) — the initial recommendation, and correct for
  a shipping single-user app: the sum is sub-millisecond at this volume and the balance can
  never drift. Overridden deliberately for the learning value of building the maintained-column
  + reconciliation pattern that real core-banking systems use.
- **Stored balance without verification** — rejected: drift with no safety net.
- **Editable transactions** (keep backlog S4 as written; maintenance logic handles edit/delete)
  — rejected in favour of append-only. Consumer PFM apps (Mint, YNAB) allow free edit/delete
  because they are a *view*, not a system of record; real bank ledgers are append-only for
  auditability, dispute handling, downstream consistency, and point-in-time balances. Chosen
  for the transferable lesson (immutable/event-log modeling, reversing entries, pending-vs-
  posted, reconciliation).
- **CSV dedupe by composite natural key or bank ID only, or no dedupe** — content hash is
  format-independent (every export has date/amount/description) where a stable bank ID often is
  not; no-dedupe pushes the work onto the user.

## Consequences

- **Spec amendment:** backlog **S4** changes from "add, edit and delete transactions" to
  **add + void** (a void posts a reversing entry). Recorded in `docs/spec.md` drift log; S4
  text to be reworded at build time.
- Every money value in code is `Decimal`; a stray `float(amount)` is a reviewable bug and a
  test failure.
- The transactions UI must represent an entry and its reversal (e.g. strike-through the
  reversed row, or a "show voided" toggle) rather than removing rows.
- The data model gains `type` + `reverses_transaction_id` on the transaction table and a
  maintained `balance` on the account table.
- A reconciliation job (scheduled or on-demand) recomputes and checks each account balance;
  a mismatch is a bug to investigate, not to auto-correct silently.
- Double-entry (each transaction hitting two accounts) is **not** adopted now — v1 stays
  single-sided but immutable. Revisit as its own ADR if transfers between accounts become a
  first-class feature.
- Supersedes archived ADR-0001 on money type (same conclusion) and on balance (0001 chose
  derived; this chooses hybrid + append-only).
