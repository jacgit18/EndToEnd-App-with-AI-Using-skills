# Data-Access Layer — example invocations (full)

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

