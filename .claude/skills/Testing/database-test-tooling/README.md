# database-test-tooling skill

A gated decision (not a procedure) for what a test that touches a database actually gets as
that database: a real ephemeral instance per run (Testcontainers/docker-compose), a shared
persistent test/staging database, an in-memory or embedded substitute engine (SQLite standing
in for Postgres/MySQL), a mock/stub of the repository or driver layer, or — for a human doing
one-off manual/exploratory work, not an automated assertion — a GUI database client (Beekeeper
Studio, DBeaver, TablePlus, pgAdmin).

`test-strategy` decides *that* an integration/contract-level test exists at the database seam
and explicitly defers "which mocking library" / "framework/tool selection" as a later choice.
This skill is that later choice, specifically for the database seam.

## Where it sits

```
test-strategy               →  which test levels exist and how much effort each gets
database-test-tooling       →  once a DB-touching test level is decided, what backs it  (this skill)
data-access-layer           →  what production code itself does to read/write rows
                                (constrains what a substitute/mock can faithfully replicate)
api-tooling-selection       →  whether an agent gets a DB GUI/MCP tool to drive live
                                (a different question — an agent's own job, not a test suite)
coverage-policy             →  the % target and CI enforcement once tests exist
```

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. Step 1 places the request, Step 2 gates on test level / DB-specific features / CI capability / parallelism / automated-vs-manual, Step 3 recommends a mechanism. |
| `tool-landscape.md` | Concrete tool names per mechanism (Testcontainers, docker-compose, SQLite/pg-mem, mocking libraries, Beekeeper/DBeaver/TablePlus/pgAdmin) — kept out of `SKILL.md` so the entry point stays engine-agnostic. |

## What it produces

A short recommendation in chat: the mechanism, the isolation strategy if a shared instance is
involved, and the fidelity gap named explicitly if a substitute engine is chosen. It does not
write the test infrastructure or CI config — that's the implementer's next, separate step.

## Deliberately out of scope

- **Which test levels exist and how much effort each gets** (unit/integration/contract/E2E
  mix) → `test-strategy`, this skill's prerequisite. A test that's supposed to be a unit test
  mocking the DB entirely is already that skill's territory — this skill only starts once an
  integration/contract-level test at the DB seam is the settled premise.
- **A coverage percentage or its CI enforcement** → `coverage-policy`.
- **How production application code reads and writes rows day to day** (ORM / query builder /
  raw SQL / typed codegen) → `data-access-layer`. This skill consumes that answer (it decides
  how faithfully a substitute or mock needs to behave) but doesn't re-decide it.
- **Whether an agent should be handed a database GUI or an MCP database server as a tool it
  drives live**, as part of the agent's own job (not a test suite) → `api-tooling-selection`.
  Beekeeper Studio's own MCP integration, or "should my agent query prod via a DB tool," is
  that skill's plain-tool-vs-MCP call, not this skill's mechanism table.
- **Where the schema's source of truth lives** (database-first/code-first/contract-first) →
  `database-architecture`.

## Using it in another repo

Repo-agnostic; names no project-specific files, paths, or database engine.

```
cp -r .claude/skills/Testing/database-test-tooling /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Tested via `skill-interaction-testing` (worktree agent) at build time. See the skill's own
`SKILL.md` commit message / project memory for the scenarios run and any fixes applied — this
section is refreshed only when a later change reopens a specific pair, per that skill's own
"don't re-test without a new reason" rule.
