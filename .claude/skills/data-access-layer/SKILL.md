---
name: data-access-layer
description: Gated decision for how application code talks to an already-chosen relational database: raw SQL, query builder, micro-ORM, full ORM, typed codegen, or compile-checked SQL. Use when someone says "ORM or query builder", "should we use an ORM at all", "is Prisma the right call here". NOT `database-architecture` (its prerequisite), `relational-modeling`, or `index-tuning`.
---

# Data-Access Layer

The source-of-truth decision is made and the store is relational. Now: how does the application
code read and write rows — hand-written SQL, a query builder, an ORM, generated typed queries,
or a blend? The skill makes the user state the SQL fluency of the team, the mix of query shapes
the app actually runs, and what they're optimizing for before any approach is on the table, then
recommends one primary style (and the secondary escape hatch for the queries it fights) and
writes an ADR.

## When to use

- The source-of-truth / persistence decision is **already made** — a `database-architecture`
  ADR exists, or the user says plainly "we're on Postgres/MySQL/SQL Server, code-first,
  internal" — and now the question is how code talks to it.
- The user asks a style question directly: ORM vs query builder, ORM vs raw SQL, SQLAlchemy
  ORM vs Core, "is Prisma right", "should we adopt sqlc", "do we even need an ORM".
- The user reports a symptom that is really a style question: "the ORM N+1s on every list
  page", "we're fighting the ORM on every reporting query", "half our code is manual row
  mapping".
- The user proposes an approach and wants it pressure-tested ("we'll just use an ORM for
  everything" / "no ORM, raw SQL only").

## Out of scope — hand these off

- **Where the schema should live** — database-first / code-first / contract-first, whether a
  formal contract is warranted, who owns the store, what gets generated → `database-architecture`.
  That is this skill's **prerequisite**. If it isn't settled, stop and send the user there
  first; do not pick an access layer on an unstated source-of-truth assumption. Note the one
  trap: `database-architecture`'s "code-first" is not a vote for an ORM, and "database-first"
  is not a vote for raw SQL — they constrain this decision (see the framework) but don't make
  it.
- **The table design** — normal form and denormalization exceptions, key strategy, constraint
  placement, lifecycle columns, the first-cut index list → `relational-modeling`. It runs in
  parallel with this skill (both downstream of the same ADR) and explicitly stops at
  "ORM / query-builder selection". Neither blocks the other.
- **Tuning or auditing an index set on a deployed, populated schema** — composite column
  order against a real `EXPLAIN` plan, covering/partial indexes, redundant/unused-index
  cleanup → `index-tuning`.
- **Why one specific query is slow** — no profile, just "the ORM is slow here" →
  `problem-solving-gates` (Optimization) to measure, then `index-tuning` if the finding is
  index-shaped. This skill only leads when the question is "should this whole class of
  queries move off the ORM", not "why is this one query slow".
- **The migration tool** — Alembic / Flyway / Liquibase / dbmate / Atlas, autogenerate vs
  hand-written, and the rollout mechanics (expand/contract, zero-downtime) → name that the
  access-layer choice largely picks it (ORM-coupled tools follow the ORM) and defer the
  detail to build time / `deployment-strategy`. Don't design the migration workflow here.
- **Skipping the application tier** — exposing the database directly as a REST/GraphQL API
  with PostgREST / Hasura / PostGraphile / Supabase, pushing authorization into row-level
  security → that is a source-of-truth shape (`database-architecture`) plus an API-surface
  choice (`api-interface-style`), not an access-layer style. If the user is weighing "write
  a backend vs generate one", send them there; this skill assumes a hand-written data tier
  exists.
- **Sharding, replication, connection pooling, transaction isolation levels** →
  `data-tier-operations`. This skill notes where the access layer controls transaction
  boundaries; it does not design the pool or the isolation strategy.
- **The analytical / warehouse model** — star vs snowflake, fact/dimension tables, grain,
  SCD → `dimensional-modeling`. This skill is about how OLTP application code reaches its
  store.
- **Whether a read should hit the database at all** rather than a cache → `caching-strategy`.
  This skill assumes the query runs against the database and decides how it's written.
- **Implementation** — writing the models, the repository classes, the query modules. The
  skill stops at the ADR.

---

## The gate

Do not name an approach until these are answered.

**Prerequisite (check first):**

- **The source-of-truth ADR exists.** Point to `docs/architecture/decisions/` or get the user
  to state the call: database-first, code-first, or contract-first, and which store. If that
  decision is open, stop — it is `database-architecture`'s job and it changes the candidate
  set here.

**From the user, in their own words** (do not invent these, do not recommend without them):

1. **Language / ecosystem** — which language the data tier is written in. This is
   load-bearing: schema-first typed codegen is mature in Go (sqlc) and Java (jOOQ), thin-to-
   absent in Python and Ruby; compile-time-checked inline SQL (sqlx) is a Rust thing. Half
   the spectrum may not exist for this build.
2. **Team SQL fluency** — does the team read and write SQL comfortably (joins, window
   functions, `EXPLAIN`), or is SQL a barrier the abstraction is there to hide? An honest
   answer, not the aspirational one.
3. **Query-shape mix** — four rough numbers that sum to ~100: (a) plain CRUD by primary key /
   foreign key; (b) variable filtered-and-sorted list queries; (c) analytical / aggregation /
   reporting queries; (d) queries that lean on DB-specific features — window functions, CTEs,
   JSON/array operators, full-text search, upserts with non-trivial conflict handling,
   recursive queries. "Mostly CRUD plus some reports" is not enough — push for the fractions,
   because the worked recommendation depends on the size of (c)+(d). An ORM is comfortable
   through (b) and fights (c) and (d).
4. **Refactor-safety bar** — how much does it matter that renaming a column or changing a
   type breaks the build at compile/generate time rather than failing in production? "It must
   be caught before deploy" points toward typed codegen, compile-checked SQL, or a typed ORM
   model; "runtime failure is acceptable, we have tests" widens the field.
5. **Priority** — the one thing this choice is optimizing for: **velocity** (ship CRUD fast,
   one mental model, minimal boilerplate), **SQL transparency / control** (the generated SQL
   is never a surprise), or **learning** (the user deliberately wants to exercise a technique,
   even at a boilerplate cost).

"Which data-access approach for X" with 1–5 absent is not valid input. Ask for what's missing
and stop.

**Pressure does not open the gate.** "Just tell me ORM or not", a deadline, or "the team
already likes Prisma" are reasons the user wants the gate skipped, not evidence it's satisfied.
The fastest correct move under time pressure is a one-sentence answer to each of 1–5.

---

## Challenge the framing

If the user opens with the approach already chosen, put their reasoning under the gate first,
then test the specific claim against `access-styles.md`:

- **"we'll use an ORM"** — for the analytical and reporting queries too (query-shape (c)/(d)),
  or is there an escape hatch for those? Who owns the generated SQL the first time it N+1s a
  list endpoint? Is the ORM's model about to become the API's shape by accident — is there a
  mapping boundary (that's the `database-architecture` ADR's call, confirm it)?
- **"raw SQL, no ORM"** — does the whole team write SQL fluently, including the next hire? Who
  maintains the row-to-object mapping the ORM would have generated? Is a query builder the
  middle ground you actually want — composable SQL without the session/identity-map machinery?
- **"no ORM, we'll generate typed queries (sqlc / jOOQ / pgtyped)"** — does your language
  have a mature tool for this, or are you about to adopt a fringe one? Is the schema stable
  enough that regenerating on every change is cheap rather than constant churn?
- **"Prisma / SQLModel / \<the popular one\>"** — reasoned or cargo-culted? What does it hide
  that you will need back — a raw-SQL escape hatch, explicit transaction control, decoupled
  migrations, multi-database support? Try to name the first query you expect to fight it on.

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `selection-framework.md` in order once the gate is satisfied. In short: restate the
source-of-truth ADR and what it already constrains → cut the spectrum to what this language
actually offers → lay the survivors against the query-shape mix and the SQL-fluency answer →
apply the refactor-safety bar and the priority → name the blend explicitly (a primary style
plus the secondary escape hatch for the query shapes the primary fights is the common, correct
outcome, not a failure to decide) → state what the choice constrains downstream (migration
tooling, transaction-boundary control, the mapping boundary) → recommend and record.

`access-styles.md` backs it: each style on the spectrum in one block — what it is, where it
fits, what it costs, its failure mode when misapplied, and representative libraries per
ecosystem — plus the note that these are **ergonomics, not source of truth** (a codegen tool
is code-first in feel over database-first in truth) and that **combining styles is normal**.

---

## Output

**1. In chat, a recommendation block:**

```
Source of truth:      <from the database-architecture ADR — database-first | code-first | contract-first, and the store>
Language / ecosystem: <and which styles it actually offers — note the ones ruled out as unavailable>
Primary style:        <raw + SQL | query builder | micro-ORM | full ORM | typed codegen | compile-checked SQL>
Secondary style:      <the escape hatch for the query shapes the primary fights — e.g. "SQLAlchemy Core + text() for the reporting endpoints and the ledger trigger maintenance" — or "none">
Query-shape fit:      <how the primary handles CRUD / variable lists / analytical / DB-specific, and exactly where the secondary takes over>
Refactor safety:      <build-time type checking | generate-time | runtime + tests only — and how schema drift is caught>
Migration tooling:    <what this choice largely picks — name it, defer the workflow detail>
Mapping boundary:     <DB row -> domain -> DTO, or "none — single internal consumer" — carried from the database-architecture ADR>
Agent legibility:     <does this choice leave an artifact an agent editing this codebase can read directly — generated types from typed codegen, a versioned migration history — or does an agent have to run the ORM to observe what it actually does>
Tradeoffs accepted:   <2-4 concrete costs of this choice>
Not chosen because:   <one line per rejected style>
```

**2. On the user's approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md`
using `database-architecture`'s `adr-template.md` (same directory and numbering — this is an
architecture decision). Reference the source-of-truth ADR. The template's **Application
access** field is exactly this skill's Primary/Secondary output; fill **Database modeling**
by reference to `relational-modeling` if that hasn't run yet. Fill "Revisit when" with the
concrete trigger that reopens this — "the reporting module's share of DB work passes ~half and
the ORM escape hatch is where all the work happens", "a second language needs the same data
tier", "schema churn makes hand-written SQL's drift risk unacceptable".

Then stop. Writing the models, repositories, and query modules is a separate step the user
starts explicitly.

---

## Escape hatch

If the user has genuinely worked the decision — the source-of-truth ADR in hand, the styles
weighed against their real query mix, a position held with reasons — and wants a review or a
tie-break rather than a Socratic pass, they say so and you give a direct recommendation with
reasoning. Opt-in, not a default you slide into because the gate is tedious.

When `tech-decision-walkthrough` routes the data-access decision here mid-walkthrough, it
hands over the build's assembled scope and the constraints already gathered (language, team,
existing systems, deadline, the source-of-truth ADR, the user's lean). Take those as the gate
inputs — surface them for confirmation, don't re-run items 1–5 from zero — then return the
recommendation block for the walkthrough to fold into its ADR.

---

## Example invocations

> "We have the source-of-truth ADR — Postgres, code-first, one internal API. Python / FastAPI.
> The work is a mix: plenty of plain CRUD, a set of dashboard aggregation queries, and an
> append-only ledger that needs triggers, `CHECK` constraints, and partial indexes. The team
> writes SQL fine. Part of the point of this project is relearning this area properly. Which
> data-access approach?"

Gate satisfied (prerequisite ADR, language, SQL fluency, query-shape mix, priority — learning
plus real SQL). Work `selection-framework.md`: ecosystem is Python, so typed codegen (sqlc-
class) is thin and compile-checked SQL (sqlx) is absent — candidates narrow to full ORM
(SQLAlchemy 2.0), query builder (SQLAlchemy Core), SQLModel, raw `psycopg`. Primary **full ORM
(SQLAlchemy 2.0)** — covers the CRUD, matches "what real projects use", and the ORM's own
concept load (session/unit-of-work, lazy vs eager) is genuine learning here rather than
incidental. Secondary **Core + `text()`** for the aggregations and the ledger/trigger
maintenance, used deliberately so the project exercises real SQL too. Refactor safety: typed
2.0 declarative models plus migration autogenerate diffing against them. Migration tooling:
Alembic follows the ORM. Mapping boundary: kept — Pydantic API schemas stay separate from the
SQLAlchemy models (from the ADR). Write the ADR; revisit if the aggregation layer grows to
dominate.

> "Should we use an ORM?"

Gate not satisfied — items 1–5 absent, and it's unclear the source-of-truth ADR exists.
Response: confirm `database-architecture` has been run, then name the missing gate items. Do
not answer "yes, use an ORM" or list ORMs to react to.

> "Our Django ORM generates a horrible query on the analytics page — 4 seconds."

One slow query with no profile → not this skill yet. `problem-solving-gates` (Optimization)
to get the plan; if it's an index, `index-tuning`. This skill leads only if the conclusion is
"the whole analytics module should be raw SQL, not the ORM" — a class-of-queries decision, not
one endpoint.

---

## Portability

Repo-agnostic. Reads `docs/architecture/decisions/` for the prerequisite source-of-truth ADR,
writes new ADRs there, reusing `database-architecture`'s `adr-template.md`. Copy the
`data-access-layer/` directory into another repo's `.claude/skills/` to use it there. See
`README.md` for where it sits among the sibling `Architecture/Data` skills.

## Routing boundaries (full)

- A gated decision for how application code talks to an already-chosen relational database — the access-layer style: raw driver + hand-written SQL, query builder (SQLAlchemy Core, Knex, Kysely, jOOQ DSL), micro-ORM / row mapper (Dapper, aiosql), full ORM / data mapper (SQLAlchemy ORM, Django ORM, Prisma, Hibernate, ActiveRecord), schema-first typed query codegen (sqlc, jOOQ, pgtyped, Kysely codegen), or compile-time-checked inline SQL (sqlx).
- Use after the source-of-truth / persistence decision is settled (a `database-architecture` ADR, or a relational store already in place) and someone is choosing or reconsidering how the app reads and writes rows: "ORM or query builder", "should we use an ORM at all", "SQLAlchemy ORM vs Core", "is Prisma the right call here", "raw SQL vs an ORM for this", "which data-access approach", "our ORM generates terrible queries, what else is there".
- NOT how an AI agent should integrate with an *external HTTP API* — Postman/OpenAPI validation, a plain tool function, or MCP — that's `api-tooling-selection`; this skill owns the access style even when the question is phrased as "MCP vs direct" for the database itself (an MCP database server vs a driver call).
- NOT the table design itself — normal form, keys, constraint placement, the first-cut index list — that is `relational-modeling`, which runs in parallel and stops explicitly at "ORM / query-builder choice".
