# ADR 0006 — Data-access layer + migrations

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** the owner
- **Derived via:** `Architecture/tech-decision-walkthrough`, decision 5 of the stack

## Context

Python + FastAPI + PostgreSQL (ADR-0002/0003/0004), append-only ledger with a maintained
balance column + reconciliation (ADR-0005). Two linked choices: how Python reads/writes rows,
and how the schema evolves in a versioned, reversible way. The project's goal is relearning
this area, and the ledger design needs triggers, `CHECK` constraints, and partial indexes —
not just plain CRUD.

## Decision

**SQLAlchemy 2.0 (ORM) + Alembic.**

- Models are SQLAlchemy 2.0 declarative classes.
- The dashboard aggregations and the ledger-maintenance / reconciliation logic are written in
  **raw SQL / SQLAlchemy Core** deliberately, not forced through the ORM — so the project
  exercises both ORM patterns and real SQL.
- Alembic manages migrations: `--autogenerate` drafts each schema change from model diffs; the
  draft is reviewed and edited; append-only constraints, the balance trigger, and partial
  indexes are hand-written via `op.execute(...)`.
- The walking skeleton ships the full data model as the initial Alembic migration (per
  `docs/spec.md`), not `create_all()`.

## Alternatives considered

- **SQLAlchemy Core + Alembic (no ORM)** — the sharpest choice for SQL fluency specifically,
  and no ORM concepts (session lifecycle, lazy loading, identity map) to learn. Lost on
  *"what real projects use"* and on boilerplate (manual row↔object mapping). Reasonable
  override if pure SQL fluency were the single top priority.
- **SQLModel + Alembic** — least code, tightest FastAPI/Pydantic integration (one class is both
  table and schema). Lost on *learning value* (hides the most) and *query power for the hard
  parts* (awkward around triggers / append-only constraints); younger.
- **Raw `psycopg` + hand-rolled migrations** — maximum SQL transparency, but re-solves
  migration versioning/ordering, which is a solved problem not worth relearning the hard way.

## Migration tooling note

Alembic is the near-universal choice for SQLAlchemy; it is not separately contested. Coming
from Knex.js (query-builder + migrations in one library), the Python split is SQLAlchemy (query
layer) + Alembic (migrations) — two packages, designed together. Alternatives if ORM-coupled
migrations were unwanted: `yoyo-migrations` or `dbmate` (plain SQL files), or Atlas
(declarative schema diffing). Not chosen — Alembic's autogenerate + tight SQLAlchemy
integration wins here.

## Consequences

- Migrations are used from the first commit — data survives schema changes (important once real
  bank CSVs are imported), and schema changes are reviewed, versioned, and reversible.
- Autogenerate drafts most changes but every migration is reviewed by hand; trigger/constraint/
  partial-index changes are written manually.
- The ORM's own concept load (session/unit-of-work, when queries hit the DB, eager vs lazy
  loading) is accepted as real learning, not incidental complexity.
- Persistence models (SQLAlchemy) and API schemas (Pydantic, per ADR-0003) stay separate —
  a deliberate boundary, slightly more code than SQLModel's single model.
- Actual table design + first-cut index list is a build-time step (`relational-modeling`),
  not fixed here.
