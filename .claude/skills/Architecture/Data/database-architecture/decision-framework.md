# Decision Framework

Work these in order once the hard gate in `SKILL.md` is satisfied. Each step produces a written line; the collected lines become the ADR's Context and Decision.

## 1. Fix the boundaries

State, in one sentence each:

- What data this is (the concept, not the table).
- Every consumer of it: name them. "Our web app", "the mobile client", "the reporting service", "third-party API customers", "an internal admin tool".
- Which of those consumers you control the release cycle of, and which you don't.
- Its regulatory class: PII, PHI, financial/PCI, or none — and whether that forces audit trails, retention limits, or residency rules.

A consumer you don't control the release of is a **boundary**. Boundaries are where contracts earn their cost. No such consumer → a contract is likely overhead right now.

A regulated class pushes toward the store enforcing constraints itself (DB-checked `NOT NULL`/`CHECK`, append-only audit tables, retention jobs) rather than trusting application code to — factor it into steps 3 and 5.

## 2. Decide who owns the store

- **Exclusive**: only this service reads/writes the database. You are free to let code or a contract be the source of truth; the DB can be an implementation detail.
- **Shared**: other services hit the same database directly. The **database** is now a de facto contract whether you like it or not — database-first (or at least DB-constraints-as-truth) gets much more attractive, because the constraints are the only thing all writers share.
- **External / managed**: you don't own the schema. You're a consumer; model defensively and validate on read.

## 3. Decide where the source of truth lives

Ask the one question that matters: **where should the authoritative definition of this data live?**

| Source of truth | Shape | Fits when |
|---|---|---|
| **Database-first** | SQL migrations define tables + constraints; app code derives types/models from that | DB integrity matters, complex SQL, shared database, multiple writers, strong referential-integrity needs |
| **Code-first** | Schema defined in app code (ORM schema, or a schema library + query builder); DB is generated or migrated from it | Single owner, domain still moving, one application, speed of iteration matters more than a formal boundary |
| **Contract-first** | A formal contract (OpenAPI / GraphQL / protobuf) is authoritative; app and DB are both implementations behind it | A real boundary exists — external consumers, multiple independent services, published API — and the domain is stable enough that the contract won't thrash |

"Code-first" does not mean "ORM". It also covers query builders (Knex, Kysely, SQLAlchemy Core) and schema libraries (Zod, Yup, io-ts) with hand-written SQL, and codegen-from-SQL (sqlc, pgtyped) which is code-first in ergonomics but database-first in truth — call that out if it fits.

## 4. Weigh against this project's stage

The gate captured evolution/stage. Apply it:

- **Exploration / discovery**: bias to code-first with an ORM or query builder. Do not stand up a contract for a domain you can't describe yet.
- **Stabilizing**: keep iterating in code, but start naming the external boundary. Identify what the contract *would* cover.
- **Stable + a real boundary**: introduce the contract. Make it authoritative. Push the database behind it.

The usual path is `ORM/query builder → domain clarifies → define a stable contract → contract becomes the boundary → database becomes an implementation detail`. You are picking a point on that path, not a religion.

## 5. Name the mapping boundary

Whatever the source of truth, decide explicitly whether the persistence representation is allowed to *be* the public representation. Default answer: **no**. Put a translation step (`DB row → domain model → API DTO`) wherever a boundary exists. That step is where you control field exposure, naming, security, backward compatibility, and API evolution. It is not wasted code.

The translation also runs the other way: it's where you add fields the table doesn't have. Example — a JWT payload carries `is_admin`, computed from a role join, that is never a column on the users table. The mapping layer is where that composition happens, so business logic reads one shape and the schema stays clean.

If there's genuinely no boundary (solo app, internal tool, one consumer you control), it's fine to skip the mapping — say so, don't cargo-cult it.

## 6. List generated artifacts

From the chosen source of truth, what is derived rather than hand-maintained:

- database-first → app types/models, maybe query types (sqlc/pgtyped)
- code-first → the migration / DB schema, TS or Python types, sometimes validators
- contract-first → server types, client SDKs, request/response validation, API docs

Write the list. It tells the implementer what they must *not* hand-write.

## 7. Recommend and record

Produce the recommendation block from `SKILL.md`. On approval, write the ADR from `adr-template.md`.
