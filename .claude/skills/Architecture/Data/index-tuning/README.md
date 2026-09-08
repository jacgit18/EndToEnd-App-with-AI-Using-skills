# index-tuning skill

A **procedure** (not a decision-gate) for adding, revising, or auditing indexes on an
**existing, populated** database. It derives a query's access path (composite column order,
covering / partial / expression indexes), checks the planner will actually use the proposed
index (selectivity), prices it against the table's write workload, audits the current index
set for redundant and unused indexes, and handles the query that doesn't deserve a permanent
index at all.

Not built from an `Architecture/` source note — assembled from the standard b-tree indexing
model plus the boundary work against the four skills whose territory it borders.

## Where it sits

```
database-architecture   →  WHERE the schema lives + WHICH store            (ADR)
relational-modeling      →  tables for a relational store — incl. the FIRST index plan (step 7)
index-tuning             →  revise / add / audit indexes on a DEPLOYED, populated schema   (this skill)
data-tier-operations     →  sharding / replication / pooling / txn isolation / warehouse physical tuning
caching-strategy         →  keep the hot read off the database entirely
```

The dividing line with `relational-modeling`: that skill produces the initial index list
**as part of designing the tables**, from access patterns described in the abstract. This
skill takes over once the schema is **live and carrying traffic** — when there are real
`EXPLAIN` plans, real column cardinalities, a real write rate, and an existing index set to
tune against.

The dividing line with `problem-solving-gates` (Optimization): that gate owns "is this even
the bottleneck — go measure". This skill runs **after** a measurement is in hand and it
points at an index-shaped problem. If the plan's cost is a disk sort, an expensive
`SELECT`-list function, a hash aggregate, or bad row estimates, that goes **back** to
`problem-solving-gates` (Optimization).

## The shape

Not a rep gate — but it needs real inputs and asks for what's missing rather than inventing
it: the engine + version, the actual query columns (`WHERE`/`JOIN`/`ORDER BY`/`SELECT`
list), rough column selectivity, the table's write profile (including *which* columns get
updated), row counts, the existing indexes (+ usage stats for an audit), the current plan
for a reactive case, and whether each query is a hot path or a rare admin/report.

The walk:

1. Restate the workload (queries + frequency class, write profile, row counts, existing
   indexes; the current plan for a reactive case).
2. Per query, derive the access path — equality columns, then one range/sort column, then
   covered columns; partial predicate; expression index.
3. Selectivity check — will the planner actually use it?
4. Write-cost budget — index count and write rate as numbers; the Nth-index decision named.
5. Redundancy + unused pass — prefix duplicates, near-redundant pairs, dead indexes to drop.
6. Rare-query escape — accept the scan / replica / temp index / tight partial.
7. Online build path for the engine.
8. Re-measure.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. Inputs needed, the 8-step walk, the output block, red flags, worked invocations. |
| `index-mechanics.md` | The b-tree access path, composite column order, composite vs. multiple single-column, covering / partial / expression indexes, "why isn't my index used", non-b-tree index types, clustered-index implications. Steps 2–3. |
| `audit-and-write-cost.md` | What an index costs each write, the write-cost budget, the redundancy pass, unused-index detection with the actual stats queries per engine, safe dropping, the rare-query playbook, online/non-blocking builds, Postgres bloat. Steps 4–7. |

## Output

The output block in chat — store, workload, current plan, proposed changes (adds / widens /
drops), write-cost delta, rare-query plan, re-measure step, handoffs. Writes no file (same
as `reliability-math`).

## Interaction with sibling skills

- **`relational-modeling`** — owns the first index plan during table design (its
  `modeling-framework.md` step 7 / `indexing-and-constraints.md`). This skill is the
  post-deployment tuning pass; its `index-mechanics.md` deliberately re-uses the same b-tree
  fundamentals rather than contradicting them, applied to real plans and stats. A
  schema-level problem this skill surfaces (a random-UUID clustered PK inflating every
  secondary index, an over-normalized hot-path join) routes back there.
- **`problem-solving-gates` (Optimization)** — owns the measurement gate. This skill runs
  once the measurement points at an index; a non-index bottleneck the plan reveals routes
  back.
- **`data-tier-operations`** — owns partitioning, sharding, replicas, and the physical
  tuning of an analytical warehouse (sort/distribution/clustering keys). This skill names
  when the honest fix is "a replica for the reporting query" and hands the topology there.
- **`caching-strategy`** — owns keeping a cacheable hot read off the database. This skill
  points there rather than indexing around a read that shouldn't hit the DB.
- **`change-surface-audit`** — a `DROP INDEX` is a removal; its hidden-dependents lens
  applies (a query silently depending on the index, an FK-backing index, a `UNIQUE` that's
  also a constraint).
- **`deployment-strategy`** — staging the index migration (expand/contract, invisible-index
  soak).
- **`technical-cost-decision`** — the dollar cost of the extra storage / IOPS / a replica.
- **`learning-gate`** — registered in its Step 3 table (tuning/auditing indexes on an
  existing DB → bring the query + plan + write profile → here).

Run `skill-interaction-testing` after any trigger-description change here — the overlap risk
is with `relational-modeling` (design-time vs. deployed-schema index work) and
`problem-solving-gates` Optimization (the measurement gate vs. the index specialist that
runs after it).

## Using it in another repo

Repo-agnostic. Writes nothing.

```
cp -r ".claude/skills/Architecture/Data/index-tuning" /path/to/other-repo/.claude/skills/
```
