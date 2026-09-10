# Selection Framework

Work these in order once the hard gate in `SKILL.md` is satisfied. Each step produces a written
line; the collected lines become the ADR's Context and Decision.

## 1. Restate the source-of-truth ADR and what it constrains

Read the `database-architecture` ADR. State its call in one line, then state what it *already*
narrows here — without letting it make the decision:

| ADR says | Leans toward | But does not mean |
|---|---|---|
| **Database-first** (SQL migrations are authoritative, app types derived) | raw SQL, a query builder, or schema-first typed codegen (sqlc / jOOQ / pgtyped) — the app follows the schema | "no ORM ever" — a thin ORM reading a DB-owned schema is still database-first if the migrations, not the models, are the truth |
| **Code-first** (schema defined in app code, DB migrated from it) | a full ORM or a code-defined query builder — the models are authoritative | "you must use a heavy ORM" — a query builder with code-defined schema, or SQLModel-style, is also code-first |
| **Contract-first** (an OpenAPI / GraphQL / protobuf contract is authoritative) | orthogonal — the contract governs the wire, not the rows; pick the access layer on the other four gate items | anything about ORM vs raw — contract-first constrains the mapping boundary, not this |

If the ADR's **Mapping boundary** field says a `DB row → domain → DTO` translation exists,
carry that forward — it means the access layer's output types are allowed to be internal and
ugly, which widens the field (a raw-row `dict` behind a mapper is fine). If it says "none —
single internal consumer", the access layer's types *are* the app's types, which raises the
value of a typed approach.

If the user paraphrased the ADR rather than pointing at the file ("we have an ADR that says
code-first, one service owns the DB"), you have the source-of-truth call but not necessarily
the **Mapping boundary** field. Don't guess it — carry it as an open item in the output block
("Mapping boundary: unconfirmed in the paraphrased ADR — recommend DB row → domain → DTO
kept") and note that confirming it may shift the typed-vs-loose weighting in step 4.

## 2. Cut the spectrum to what this language offers

From gate item 1. The full spectrum is in `access-styles.md`; not all of it exists everywhere:

- **Schema-first typed codegen** — mature: Go (`sqlc`), Java/Kotlin (`jOOQ`). Usable: TypeScript
  (`pgtyped`, `kysely-codegen`). Thin / community-only: Python, Ruby, PHP. If it's thin for
  this language, drop it from the candidate set rather than recommend a fringe tool.
- **Compile-time-checked inline SQL** — effectively Rust-only (`sqlx`). Drop it elsewhere.
- **Full ORM, query builder, micro-ORM, raw driver** — available in every mainstream server
  language; always in the set.

Write the surviving candidate list. 2–4 is the target; if the language cut leaves only "ORM
or raw", say so plainly.

## 3. Lay the survivors against the query-shape mix and SQL fluency

From gate items 2 and 3. Build a small table: rows = the surviving styles, columns = the
query-shape buckets the user gave a non-trivial fraction to (CRUD / variable lists /
analytical / DB-specific). Fill each cell with "comfortable", "workable", or "fights it".

The pattern that almost always emerges:

- CRUD and variable lists: every style handles these; an ORM or query builder handles them
  with the least code.
- Analytical / aggregation and DB-specific features: an ORM *fights* these — you end up in
  its raw-SQL escape hatch, its query builder, or a `text()` call. A query builder is
  workable. Raw SQL and typed codegen are comfortable.

Cross-reference SQL fluency: if the team does **not** write SQL comfortably, "fights it" in an
analytical-heavy app is a real cost and pushes toward a style that keeps them in a typed API
as long as possible — but note that the analytical queries will still need *someone* who can
write them, and no abstraction removes that.

## 4. Apply the refactor-safety bar and the priority

From gate items 4 and 5.

- **Refactor safety "must be caught before deploy"** — rank the survivors by when schema drift
  is caught: compile-checked SQL and typed codegen (generate/compile time) > typed ORM models
  with migration autogenerate diffing (migration-review time) > query builder with a
  code-defined schema (partial) > raw SQL strings (runtime only, tests permitting). Let this
  break a tie; don't let it override a strong query-shape fit on its own.
- **Priority = velocity** — favor the full ORM (or SQLModel-class) for the CRUD bulk; accept
  the escape hatch for the rest.
- **Priority = SQL transparency / control** — favor raw SQL or a query builder; the generated
  SQL is never a surprise, at a boilerplate cost.
- **Priority = learning** — pick the style that exercises the technique the user named. If
  that's "learn the ORM patterns real projects use", that's the full ORM *with* a deliberate
  raw-SQL secondary so both get exercised. If it's "get fluent in SQL", that's the query
  builder or raw SQL, and an ORM would defeat the purpose.

## 5. Name the blend explicitly

A single style rarely wins outright. State the **primary** (what the bulk of the data tier
uses) and the **secondary** (the explicit escape hatch for the query shapes the primary
fights, named concretely — "Core + `text()` for the three reporting endpoints and the balance
trigger", not "raw SQL where needed"). Picking a primary and a secondary is the expected
outcome, not indecision. If there genuinely is no secondary — the app is all CRUD, or all
hand-written SQL — say "none" and why.

## 6. State what the choice constrains downstream

- **Migration tooling** — an ORM-coupled tool usually follows the ORM (SQLAlchemy → Alembic,
  Django ORM → Django migrations, Prisma → Prisma Migrate, Ecto → Ecto migrations). A
  raw/query-builder/codegen choice leaves it open (plain-SQL tools like dbmate / Flyway /
  `yoyo`, or declarative diffing like Atlas). Name the likely tool; defer the workflow
  (autogenerate vs hand-written, expand/contract, zero-downtime) to build time and
  `deployment-strategy`.
- **Transaction-boundary control** — an ORM's session/unit-of-work owns transaction scope by
  default; a raw/query-builder approach makes you place `BEGIN`/`COMMIT` explicitly. Note
  which, because it shapes the repository/service layer.
- **The mapping boundary** — restate it from the ADR (step 1). If none exists and the priority
  is velocity, flag that the access-layer types will leak into the app's core — acceptable
  for a solo internal tool, a latent cost otherwise.

## 7. Recommend and record

Produce the recommendation block from `SKILL.md`. On approval, write the ADR from
`database-architecture`'s `adr-template.md`, referencing the source-of-truth ADR.
