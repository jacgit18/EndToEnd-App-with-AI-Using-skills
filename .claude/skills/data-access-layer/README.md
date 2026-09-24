# data-access-layer skill

The other post-decision sibling to `database-architecture` (alongside `relational-modeling`).
Once the source-of-truth / persistence question is settled and the store is relational, this
skill decides **how application code reads and writes rows** — raw SQL, a query builder, a
micro-ORM, a full ORM, schema-first typed codegen, or compile-checked inline SQL — and the
blend of a primary style plus an escape hatch.

Fills the gap where `tech-decision-walkthrough` classes "data-access layer" as a *structural*
decision to walk but has no specialist to route it to, and where `relational-modeling` and
`database-architecture` both explicitly stop at "ORM / query-builder selection".

## Where it sits

```
database-architecture  →  decides WHERE truth lives + WHICH store (ADR)      [prerequisite]
relational-modeling    →  designs the tables for a relational store          (parallel sibling)
data-access-layer      →  how app code talks to the store — this skill       (parallel sibling)
data-tier-operations   →  sharding / replication / pooling / txn isolation
index-tuning           →  revising/auditing indexes on a deployed schema
```

`relational-modeling` and `data-access-layer` are independent branches off the same
`database-architecture` ADR — a build usually runs both, and neither is a prerequisite of the
other. But run them **one gate at a time**: `relational-modeling`'s
entities/relationships/access-patterns/volume questions and this skill's
source-of-truth/language/SQL-fluency/query-shape/refactor-safety/priority questions are two
precondition walls, and asking both in one turn is the stacking failure. Finish one, then
start the other.

The gate's **prerequisite** is the `database-architecture` ADR (or an explicit "we're on
Postgres, code-first, staying"). Without it the skill bounces the user back — the source-of-
truth call changes the candidate set here.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. Prerequisite check, the 5-item gate, challenge-the-framing, output contract. |
| `selection-framework.md` | The 7-step process, worked once the gate is satisfied. |
| `access-styles.md` | The spectrum reference — each style's fit / cost / failure mode / representative libraries, plus the ergonomics-vs-source-of-truth and combining-styles notes. |

## What it produces

1. A recommendation block in chat (source of truth, ecosystem, primary + secondary style,
   query-shape fit, refactor safety, migration tooling, mapping boundary, tradeoffs).
2. On approval: an ADR in `docs/architecture/decisions/`, reusing `database-architecture`'s
   `adr-template.md` — the **Application access** field is this skill's output.

Stops before the models, repositories, and query modules.

## Deliberately out of scope

- The where-should-the-schema-live decision → `database-architecture` (prerequisite).
- Table design — normal form, keys, constraints, first-cut index list → `relational-modeling`.
- Index tuning on a deployed, populated schema → `index-tuning`.
- Why one query is slow → `problem-solving-gates` (Optimization), then `index-tuning`.
- The migration tool's workflow (autogenerate, expand/contract, zero-downtime) → build time /
  `deployment-strategy`. This skill only names which tool the access-layer choice picks.
- Skipping the app tier — PostgREST / Hasura / PostGraphile / Supabase exposing the DB
  directly → `database-architecture` (source-of-truth shape) + `api-interface-style` (surface).
- Pooling, replication, isolation levels → `data-tier-operations`.

## Interaction with sibling skills

Stacks *after* `database-architecture` (beneficial chaining — the source-of-truth ADR is this
skill's prerequisite input) and *beside* `relational-modeling` (independent, same parent ADR).
`tech-decision-walkthrough` routes its "data-access layer" decision here and folds the block
into that decision's ADR. `learning-gate`'s "Database design" row lists it. Trigger wording
leans on "ORM / query builder / raw SQL / access approach" plus a settled source-of-truth call,
to avoid catching requests that belong in `database-architecture` (source of truth) or
`relational-modeling` (tables). Re-check overlap if any of those descriptions change.

## Using it in another repo

Repo-agnostic. Reads `docs/architecture/decisions/` for the prerequisite ADR, writes new ADRs
there.

```
cp -r .claude/skills/data-access-layer /path/to/other-repo/.claude/skills/
```
