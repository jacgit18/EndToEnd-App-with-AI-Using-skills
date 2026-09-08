# relational-modeling skill

The post-decision sibling to `database-architecture`. Once the source-of-truth / persistence
question is settled and the store is relational, this skill designs the actual tables:
normal form and exceptions, keys, constraints, indexes, lifecycle columns, relationship
patterns.

Built from the `Architecture/02. Backing Service Options/Databases/` notes — Normalization &
Denormalization, Database Indexing, Database Core Functionality (constraints, referential
actions, triggers), GUIDs, Record Life Cycle, Database Table Relationship Types, Self-joining
relationships.

## Where it sits

```
database-architecture   →  decides WHERE the schema lives + WHICH store (ADR)
relational-modeling      →  designs the tables for a relational store (this skill)
data-tier-operations     →  sharding / replication / pooling / txn isolation   (built)
dimensional-modeling     →  star / snowflake / fact / dimension / warehouse    (built)
```

The gate's **prerequisite** is the `database-architecture` ADR (or an explicit "we're on
Postgres and staying"). If that decision isn't made, the skill bounces the user back rather
than modeling on an assumption.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. Prerequisite check, the gate, challenge-the-framing, output contract. |
| `modeling-framework.md` | The 9-step process, worked once the gate is satisfied. |
| `normalization-and-keys.md` | 1NF→3NF in brief, when denormalization is justified, surrogate vs natural vs UUID. |
| `indexing-and-constraints.md` | Constraint placement (DB / app / trigger), referential actions, the index plan, lifecycle columns. |

## What it produces

1. A design summary in chat (store, normal form + exceptions, key strategy, DB- vs
   app-enforced rules, index list, lifecycle approach, deferred concerns).
2. An ERD sketch + table-by-table spec written to `docs/data-model/<slug>.md`.

Stops before migrations and ORM wiring.

## Deliberately out of scope

- The where-should-the-schema-live decision → `database-architecture`.
- Sharding, replication, connection pooling, transaction isolation, 2PC/Saga → a future
  `data-tier-operations`; this skill only *notes* when the design will need them.
- Tuning the index set on a schema that's already deployed and carrying traffic — column
  order against a real `EXPLAIN` plan, covering/partial-index trade-offs, redundant/unused
  audit, write-cost budgeting → `index-tuning`. This skill produces the first-cut index
  list (step 7); `index-tuning` revises it once real plans and stats exist.
- Analytical / dimensional modeling (star, snowflake, fact/dimension, grain, warehouses,
  marts, reporting materialized views) → a future skill; this one is OLTP only.
- ORM / query-builder choice and migration tooling.

## Using it in another repo

Repo-agnostic. Reads `docs/architecture/decisions/`, writes `docs/data-model/`.

```
cp -r .claude/skills/relational-modeling /path/to/other-repo/.claude/skills/
```

## Interaction with sibling skills

Runs `skill-interaction-testing` territory: it stacks *after* `database-architecture`
(beneficial chaining — the ADR is this skill's input) and must not claim the source-of-truth
decision itself. The trigger wording leans on "model / normalize / index / key / soft delete"
plus a stated relational store to avoid catching requests that belong in
`database-architecture`. Re-check overlap if either skill's description changes.
