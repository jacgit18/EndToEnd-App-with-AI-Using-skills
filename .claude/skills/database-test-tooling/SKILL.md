---
name: database-test-tooling
description: Gated decision for what backs a database-touching test once `test-strategy` says a DB-seam test exists: ephemeral real DB (Testcontainers), shared test DB, in-memory substitute, mocked repository, or GUI client. Triggers: "should we mock the database in our tests", "Testcontainers vs SQLite", "how do I test my repository/DAO layer". Not `test-strategy` or `data-access-layer`.
---

# Database Test Tooling

`test-strategy` decides *that* an integration or contract test exists at the database seam. It explicitly defers the mechanism — "which mocking library," "framework/tool selection" — to be named and picked later. This skill is that later: given a test that needs a database, what does it actually talk to, and does that choice still tell the truth about production.

## Step 1 — Place the request

| What's being asked | What it actually is | Owned by |
|---|---|---|
| A test needs a database, and the question is what backs it — real instance, substitute, mock, or a human's manual check | Test-DB mechanism | This skill |
| Whether integration/contract-level tests should exist at all for this seam, and how much effort they get | Test level mix | `test-strategy` — settle this first if it isn't already |
| Writing one specific DB test, or listing which cases to cover | Test rep / case list | `test-practice-gate` / `test-case-discovery` |
| A coverage percentage or whether CI blocks on it | Coverage enforcement | `coverage-policy` |
| How production application code reads/writes rows day to day | Data access layer | `data-access-layer` |
| Whether an agent should be given a database GUI or an MCP database server as a tool it drives live | Agent tool integration | `api-tooling-selection` |
| Where the schema's source of truth lives (database-first/code-first/contract-first) | Persistence architecture | `database-architecture` |

If the request lands in any row other than the first, hand off — do not build a Testcontainers-vs-mock recommendation for a question that's actually about test-level mix, coverage numbers, production access code, or agent tooling.

## Step 2 — Gate: name these before recommending a mechanism

- **What test level is this for?** If the answer is "unit" — a mocked repository interface is `test-strategy`'s unit tier and correct as-is; this skill's real decision only starts at the integration/contract level, where the point is exercising a real wiring.
- **What does production code actually do at the DB?** Plain CRUD an ORM abstracts away, or dialect-specific SQL, extensions, triggers, stored procedures, `JSONB`/array operators, `LISTEN/NOTIFY`, window functions? The more DB-specific the real code is, the less a substitute engine can be trusted to catch real bugs.
- **Can CI run a real database?** Docker-capable runners make Testcontainers/docker-compose trivial; some constrained or serverless CI environments can't, which forces either a shared instance or a substitute.
- **How many tests run against this, and in parallel?** A single suite that starts and tears down its own instance tolerates parallelism cleanly; a shared instance needs a real answer for isolation (per-test transactions rolled back, per-test schemas, or accepted serialization) or it becomes the flaky suite the user is often already complaining about.
- **Is this actually automated, or is a human doing a one-off check?** "I want to poke at the data and see what's actually in this table" or "verify this migration did what I expected" is manual/exploratory — a GUI client is the right and sufficient answer, and the rest of this gate doesn't apply. Don't force CI-mechanism questions onto a one-time manual check.

A bare "what's the difference between Testcontainers and mocking" with no real suite behind it is a definitional question — answer from Step 1/3, don't force the gate onto it.

## Step 3 — Recommendation

| Situation | Recommendation |
|---|---|
| Integration/contract test, DB-specific features genuinely in play, CI can run Docker | A real ephemeral instance per run (Testcontainers, or a docker-compose service in CI) — the only mechanism that exercises the actual engine, extensions, and SQL dialect. Slower per-run startup is the accepted cost. |
| Integration test, plain CRUD only, no dialect-specific features anywhere in the code under test, and startup speed genuinely matters | An in-memory/embedded substitute (SQLite standing in for Postgres/MySQL) can work — but name the fidelity gap explicitly (constraints, types, and concurrency behavior differ) and confirm the code under test really never touches the features that would silently diverge. Default to a real instance when in doubt; this row is the exception, not the default. |
| CI genuinely cannot run a real database (a constrained/serverless runner), and no substitute is trustworthy enough | A shared persistent test/staging database — but pair it with a stated isolation strategy (transaction-per-test rollback, per-test schema, or accepted serialization) or the suite becomes exactly the flaky-shared-DB complaint that prompted the question. |
| The seam should be isolated from the database entirely (this is really a unit test) | Mock/stub the repository or driver interface — correct at this level, per `test-strategy`'s unit tier. Flag if this mock is standing in for a test that was supposed to be integration-level; a suite of green mocked tests over a broken real query is `test-strategy`'s named over-mocking failure mode. |
| A human wants to inspect data, verify a migration, or debug a failing test's actual state | A GUI database client (Beekeeper Studio, DBeaver, TablePlus, pgAdmin) or `psql`/`mysql` directly. This is the correct and complete answer for manual/exploratory work — it is never the mechanism an automated assertion runs against. |

Concrete tool names, versions and per-engine caveats for each mechanism are in `tool-landscape.md` — read it once a mechanism is chosen and the user needs a named tool, not before the Step 2 gate is answered.

## Red flags — not done

- Recommended mocking the database for a test that was supposed to be integration-level, defeating the point of that tier
- Recommended a GUI client as what an automated/CI test actually runs against
- Recommended an in-memory/embedded substitute engine without naming the fidelity gap against the real production engine
- Recommended a shared persistent test database with no stated isolation strategy
- Answered a "what test levels do we need" question as if it were this skill's mechanism call
- Treated an agent-driven database GUI/MCP tool question as this skill's territory instead of `api-tooling-selection`'s

## Routing boundaries (full)

- Use when someone asks "can Beekeeper be used for testing a database", "should we mock the database in our tests", "in-memory DB vs a real one for tests", "our integration tests hit a shared DB and it's flaky", "how do I test my repository/DAO layer", "Testcontainers vs SQLite", "is Beekeeper part of a testing workflow", or proposes a mechanism and wants it checked.
