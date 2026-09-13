# Access Styles — the spectrum

The reference for `selection-framework.md`. Ordered from "you write every byte of SQL" to
"you rarely see SQL". Two framing notes before the styles:

- **These are ergonomics, not source of truth.** The database-first / code-first /
  contract-first call (`database-architecture`) decides *where the authoritative definition
  lives*. This spectrum decides *what the calling code looks like*. They correlate but are
  not the same axis — schema-first typed codegen (sqlc, pgtyped) *feels* code-first (you call
  typed functions) while being database-first in truth (the `.sql` files and the live schema
  are authoritative). Say which you mean every time.
- **Combining styles is the norm, not a failure.** Almost every real data tier is a primary
  style plus an escape hatch: an ORM for CRUD with raw SQL for reports; a query builder with
  `text()` for a recursive CTE; typed codegen with one hand-written dynamic query. Picking a
  primary and naming the secondary is a finished decision.
- **The escape hatch's quality varies sharply — and it's often the deciding fact.** Every ORM
  and builder has a "drop to raw SQL" path, but they are not equal, and if a meaningful slice
  of the workload (query shapes (c)+(d)) will live in that hatch, its quality should drive the
  choice:

  | Style / library | Raw-SQL escape hatch | Result typing in the hatch |
  |---|---|---|
  | Prisma | `$queryRaw` | Untyped — you hand-annotate the row type |
  | Django ORM | `.raw()` / `connection.cursor()` | Untyped |
  | SQLAlchemy ORM/Core | `text()` / Core `select()` | Untyped `text()`; Core is typed-ish via column objects |
  | Ecto | `fragment(...)` / `Repo.query!` | Partial — `fragment` inside a typed query; `Repo.query!` raw |
  | Drizzle | `` sql`` `` tag | Hand-typed — you supply the expected shape |
  | Kysely | `` sql`` `` tag / `sql<T>` | Hand-typed, but `withRecursive` / window funcs are first-class and fully typed, so less goes to the hatch |
  | Raw driver / codegen | n/a — you're already there | n/a |

  Rule of thumb: if (c)+(d) is more than ~10–15% and the primary's hatch is untyped, either
  pick a primary whose hatch is typed, or make the secondary a *typed query builder* (Kysely,
  SQLAlchemy Core) that owns that slice — not the primary's raw hatch.

---

## Raw driver + hand-written SQL

**What it is.** The database driver (`psycopg`, `node-postgres`, `pgx`, JDBC) plus SQL you
write as strings. Rows come back as tuples / dicts / maps; you map them to objects by hand or
with a light helper.

**Fits when.** The team writes SQL fluently; the workload is analytical- or DB-feature-heavy;
the schema is DB-owned (database-first); or the data surface is small enough that an
abstraction is pure ceremony.

**Costs.** No protection against a SQL typo or a schema drift until runtime (tests permitting).
You hand-maintain every row-to-object mapping. A column rename is a grep across string
literals. Dynamic queries (optional filters) mean string assembly or a mini-builder you end
up writing anyway.

**Failure mode when misapplied.** Adopted by a team that isn't SQL-fluent "for control", then
every feature stalls on SQL nobody's sure is right; or used for a large CRUD surface, where
the manual mapping becomes most of the code.

**Representative.** `psycopg` / `asyncpg` (Python), `pg` (Node), `database/sql` + `pgx` (Go),
plain JDBC (Java), `mysql2` (Ruby).

---

## Query builder

**What it is.** A fluent API that composes SQL as data — you still think in tables, joins, and
`WHERE` clauses, but the query is built programmatically and parameterized for you. No object
identity, no change tracking, no lazy loading.

**Fits when.** You want composable, safe, dynamic queries (filters that vary per request)
without an ORM's session machinery; the team knows SQL and wants to keep thinking in it; the
workload spans CRUD and moderately complex reads.

**Costs.** You still write the row-to-object mapping (lighter than raw — the builder often
returns typed rows). Very complex SQL (window functions, deep CTEs) is often clearer written
raw than fought through the DSL. It's a genuine middle: less magic than an ORM, more assembly
than one.

**Failure mode when misapplied.** Treated as an ORM ("why doesn't it save my object graph?");
or every query is so complex the DSL is just a verbose way to write SQL and raw would be
clearer.

**Representative.** SQLAlchemy Core (Python), Knex / Kysely (Node/TS), jOOQ's DSL (Java),
`squirrel` / `goqu` (Go), Ecto's query API (Elixir).

---

## Micro-ORM / row mapper

**What it is.** Maps result rows to structs/classes and parameters back, but you write the
SQL. The boilerplate of `row["col"] → obj.col` is gone; nothing else is added.

**Fits when.** You want the mapping boilerplate removed but full SQL control kept; a team that
got burned by a full ORM's generated queries and wants SQL back without hand-mapping.

**Costs.** No migrations, no relationship handling, no identity map — you build those or do
without. Still a column-name-in-a-string refactor hazard for the SQL itself.

**Failure mode when misapplied.** Expected to grow relationship loading / change tracking and
it just doesn't; the team reimplements half an ORM around it.

**Representative.** Dapper (.NET) is the archetype; `aiosql` / `records` (Python), `sqlx`'s
mapping helpers (Go — different tool from Rust's `sqlx`), `jdbi` (Java).

---

## Full ORM / data mapper

**What it is.** Objects mapped to tables, with relationships, lazy/eager loading, an identity
map, a unit-of-work/session that batches writes, and usually first-class migration tooling.

**Fits when.** CRUD-heavy app with many entities and relationships; developer velocity and one
mental model matter more than hand-tuned SQL; the team is not uniformly SQL-fluent; a single
service owns the DB (code-first).

**Costs.** The abstraction leaks under load — N+1 queries, surprising JOINs, generated SQL
that needs tuning. You will drop to the raw escape hatch for the hardest ~5–15% of queries;
plan for it rather than discover it. There's a real concept load (session lifecycle, when a
query actually executes, eager vs lazy, cascade rules) — genuine learning if that's the goal,
overhead if it isn't.

**Failure mode when misapplied.** Used for an analytics-heavy or DB-feature-heavy workload,
where the team spends its time fighting the ORM and living in `text()`; or the ORM's model
silently becomes the API's shape because no mapping boundary was set.

**Representative.** SQLAlchemy ORM / Django ORM (Python), Prisma / TypeORM / MikroORM (Node/TS),
Hibernate / JPA (Java), ActiveRecord (Rails), Entity Framework Core (.NET), GORM (Go),
Ecto (Elixir — a data mapper, no lazy loading by design).

---

## Schema-first typed query codegen

**What it is.** You write `.sql` files (queries and, in some tools, the schema); a build step
introspects the database (or parses the DDL) and generates type-safe functions in your
language, with the parameter and result types inferred from the real schema.

**Fits when.** You want hand-written SQL *and* compile-time guarantees the query matches the
schema; the team treats SQL as a first-class skill; database-first source of truth; a language
with a mature tool.

**Costs.** A codegen step in the build. Regeneration on every schema change (cheap if the
schema is stable, friction if it churns hourly). Dynamic queries are awkward — most tools
want static SQL, so optional-filter queries fall back to a builder or raw. Tool maturity
varies sharply by language.

**Failure mode when misapplied.** Adopted in a language where the tool is a half-maintained
community project; or on a schema in heavy early-stage flux, where regeneration is constant
noise.

**Representative.** `sqlc` (Go — the reference implementation), `jOOQ` in codegen mode (Java),
`pgtyped` / `kysely-codegen` (TypeScript). Thin or absent for Python, Ruby, PHP.

---

## Compile-time-checked inline SQL

**What it is.** SQL written inline in the code; a macro connects to a development database *at
compile time*, runs the query as a prepared statement, and fails the build if it's invalid or
the inferred types don't match the bindings.

**Fits when.** Rust services that want raw SQL with zero runtime mapping/typo risk and no
codegen artifact to check in.

**Costs.** Needs a reachable dev database (or a checked-in query cache) at compile time.
Effectively Rust-only. Same dynamic-query awkwardness as codegen.

**Failure mode when misapplied.** Expected outside Rust (it isn't there); CI can't reach a
database and the offline cache drifts.

**Representative.** `sqlx` (Rust). `diesel` is the ORM/query-builder alternative in the same
ecosystem for contrast.

---

## Quick map — priority to primary style

| If the priority is… | Primary lean | Secondary it implies |
|---|---|---|
| Velocity (CRUD bulk, one mental model) | Full ORM | Raw SQL / Core for reports + DB-feature queries |
| SQL transparency / control | Query builder or raw SQL | A tiny mapper, or none |
| Refactor safety above all, right language | Typed codegen (Go/Java/TS) or `sqlx` (Rust) | A query builder for the dynamic ones |
| Learning the ORM patterns real projects use | Full ORM | A *deliberate* raw-SQL slice so SQL gets exercised too |
| Getting fluent in SQL | Query builder or raw SQL | — (an ORM would defeat the purpose) |
