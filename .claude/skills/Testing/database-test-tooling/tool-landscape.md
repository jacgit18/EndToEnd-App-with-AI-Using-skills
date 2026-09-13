# Tool landscape

Concrete options per mechanism, kept out of `SKILL.md` so the entry point stays engine- and
language-agnostic. Use this once Step 3 has already named the mechanism — it doesn't change
the decision, only names what to reach for.

## Real ephemeral instance per run

- **Testcontainers** (Java, Node, Python, Go, .NET, others) — starts the real database image
  (`postgres`, `mysql`, `mongo`, …) in Docker for the duration of a test run, then tears it
  down. The default answer when CI can run Docker and fidelity matters.
- **A docker-compose service in CI** — simpler than Testcontainers when the whole suite (not
  per-test-file) shares one instance for the run; less isolation between test files, more
  setup control.
- **Ephemeral managed-DB branches** (e.g. a branch-per-test-run feature some managed Postgres
  providers offer) — same fidelity goal as Testcontainers without local Docker, at the cost of
  network latency and a dependency on that provider's branching feature existing and being
  fast enough for CI.

## Shared persistent test/staging database

- Isolation mechanisms to pair with it: a transaction per test rolled back at teardown (fast,
  but breaks for code that itself manages transactions or runs DDL mid-test), a schema or
  database-per-test-worker, or nightly/pre-suite reset scripts. Naming *which* of these is the
  point of Step 2's isolation question — "shared DB" with no isolation answer is the flaky
  suite, not a decision.

## In-memory / embedded substitute engine

- **SQLite** standing in for Postgres/MySQL — fast, zero infra, but diverges on `JSONB`/array
  operators, window-function edge cases, strictness of typing, and concurrent-write behavior.
  Libraries like `pg-mem` (Node, partial Postgres emulation) sit in the same family: useful for
  plain-CRUD logic, not a substitute for exercising a real engine's specific behavior.
- Framework-provided in-memory fakes (e.g. an ORM's own "sqlite memory" test mode) inherit the
  same fidelity gap — they test the ORM's own portable subset, not the database.

## Mock / stub the repository or driver layer

- Hand-written fakes implementing the same repository interface (an in-memory dict standing in
  for a `UserRepository`), or a mocking library (`unittest.mock`, `jest.mock`, `Mockito`,
  `sinon`) patched onto the driver/client. Correct at the unit tier; per `test-strategy`, a seam
  is a candidate for a mock *or* a real integration test, not both pretending to be the other.

## GUI database clients (manual/exploratory — not automated)

- **Beekeeper Studio**, **DBeaver**, **TablePlus**, **pgAdmin** (Postgres-specific), **psql** /
  **mysql** CLIs. All are for a human looking at real data, verifying a migration's effect,
  or debugging what a failing automated test actually left behind. None of them is the thing an
  automated assertion runs against — if a GUI client is in the loop of a CI pipeline at all,
  that is a red flag per `SKILL.md`, not a valid mechanism.
