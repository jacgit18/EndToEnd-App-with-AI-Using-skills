---
name: index-tuning
description: A procedure for adding, revising, or auditing indexes on an existing, populated database — composite column order (equality then range/sort), covering / INCLUDE indexes for index-only scans, partial and expression indexes, a selectivity check that catches an index the planner will never use, a redundancy-and-unused-index audit against the current index set, and a write-cost budget so the Nth index on a write-hot table is a decision rather than a reflex. Use when someone has a real query and its plan in hand and asks "what index should this have", "why isn't my index being used", "do I have too many indexes", "which indexes are unused / redundant", "should this be one composite or two separate indexes", "will a covering index help here", or wants an index set reviewed. It needs the actual WHERE / JOIN / ORDER BY columns, rough column cardinalities, the table's write profile, the existing indexes, and whether each query is a hot path or a rare admin/report query — it asks for what's missing rather than inventing it. Not the initial index plan for a schema being designed from scratch — that is `relational-modeling` (step 7), which this skill takes over from once the schema is deployed and carrying real traffic. Not the gate that decides whether a query is even the bottleneck — bring a profile or EXPLAIN ANALYZE first; `problem-solving-gates` (Optimization) owns that, and this skill runs once its measurement points at an index-shaped problem. Not a non-index bottleneck the plan reveals (a disk sort, an expensive SELECT-list function, a hash aggregate, stale planner statistics) — back to `problem-solving-gates` (Optimization). Not partitioning, sharding, read replicas, or the shard/distribution key — `data-tier-operations`. Not physical tuning of an analytical warehouse (sort keys, distribution keys, clustering keys on Redshift / Snowflake / BigQuery) — `data-tier-operations` with `dimensional-modeling` for the model; this skill is OLTP b-tree / secondary-index territory. Not whether the read should hit the database at all — `caching-strategy`. Not the dollar cost of the extra storage or IOPS — `technical-cost-decision`.
---

# Index Tuning

Take an existing, populated table with a real query workload and decide what to index:
which columns in which order, whether a covering or partial index earns its keep, whether
an index the query "should" use will actually be picked, what each new index costs every
write, and which existing indexes are dead weight that can go. This is a procedure, not a
gate — it needs real inputs, not a user rep — but it will not invent the workload; missing
inputs get asked for.

## When to use

- A specific query is slow, a plan (`EXPLAIN ANALYZE` / actual execution plan) is in hand,
  and the plan points at a missing, wrong, or ineffective index.
- A new query is being added to a live schema and needs an index designed against the
  table's real cardinalities and existing index set.
- An index set needs review — "do we have too many", "which are unused", "are any
  redundant", "this table has 14 indexes and writes are slow".
- The planner is ignoring an index that looks like it should match, and the question is why.
- A choice between one composite index and several single-column ones, or whether to widen
  an existing index versus add a new one.

## Not this skill — hand off

- **The initial index plan for a schema being designed from scratch** → `relational-modeling`
  step 7. That skill builds the first index list from the access patterns as part of the
  table design; this skill takes over once the schema is deployed, populated, and the real
  query plans and write rates exist to tune against.
- **Whether the query is even the bottleneck** — no profile, no plan, just "it feels slow"
  → `problem-solving-gates` (Optimization) owns that gate: measure first. This skill starts
  once that measurement is in hand and it points at an index.
- **A non-index-shaped bottleneck the plan reveals** — a sort spilling to disk, an expensive
  function in the `SELECT` list, a hash aggregate over millions of rows, row-count estimates
  that are wildly off (a statistics / `ANALYZE` problem, not an index problem) → back to
  `problem-solving-gates` (Optimization). This skill names the finding and routes it.
- **Partitioning, sharding, read replicas, the shard or distribution key** →
  `data-tier-operations`. This skill will say "the honest fix for this monthly report is to
  run it on a replica" but does not design the replication topology.
- **Physical tuning of an analytical warehouse** — sort keys, distribution keys, zone maps,
  clustering keys on Redshift / Snowflake / BigQuery → `data-tier-operations` (with
  `dimensional-modeling` for the model itself). This skill is OLTP b-tree / secondary-index
  land; a columnar warehouse's physical layout is a different discipline.
- **Whether the read path should touch the database at all** — a hot read whose result is
  cacheable → `caching-strategy`.
- **The dollar cost** of the extra storage, IOPS, or a reporting replica →
  `technical-cost-decision`.
- **A schema-level problem the tuning surfaces** — a missing column forcing every query to
  filter on a computed expression, an over-normalized model forcing a six-table join on a
  hot path → `relational-modeling`.
- **Rolling out the index change** in stages, or checking whether dropping an index breaks a
  query you didn't know about → `deployment-strategy` (expand/contract) and
  `change-surface-audit` (a drop is a removal — audit its hidden dependents).

---

## Inputs it needs

Not a rep gate — but it will not model the index set without these. State what's known; ask
for the rest.

1. **Store engine and version.** Partial indexes, `INCLUDE`/covering columns, expression
   indexes, hash/GIN/GiST/BRIN types, clustered vs. heap tables, and the online-build syntax
   all vary by engine and version.
2. **The actual queries.** The real `WHERE` predicates, `JOIN ... ON` columns, `ORDER BY` /
   `GROUP BY`, and the `SELECT` list (covering-index candidacy) — not "a lookup on the
   orders table". Parameterized shapes are fine; the column list is not optional.
3. **Selectivity.** Roughly how many distinct values each candidate column has, and roughly
   what fraction a typical predicate matches. "`status` has 4 values and 95% of rows are
   `closed`" is the single most decision-changing fact and is almost never volunteered.
4. **The table's write profile.** Insert / update / delete rate, and *which columns get
   updated* — an index on a frequently-updated column is a tax every one of those updates
   pays.
5. **Row count and growth.** A tuning that's right at 100k rows can be wrong at 100M.
6. **The existing indexes** on the affected tables, and — for an audit — index usage stats
   (`pg_stat_user_indexes`, `sys.dm_db_index_usage_stats`, `sys.schema_index_statistics`).
7. **For a reactive case, the current plan.** `EXPLAIN (ANALYZE, BUFFERS)` or the actual
   execution plan showing what runs today and where the time goes.
8. **Hot path or rare admin/report?** Per query. A query that runs thousands of times a
   minute and one that runs at 2 a.m. on the first of the month get different answers — the
   second may not deserve a permanent index at all.

---

## The walk

Work `index-mechanics.md`, then `audit-and-write-cost.md`. In short:

1. **Restate the workload** — the queries with their frequency class, the tables' write
   profile and row counts, the existing indexes. For a reactive case, restate what the
   current plan does and where its time goes, and confirm that reading with the user.
2. **Per query, derive the access path** (`index-mechanics.md`) — equality predicates as
   leading columns, then one range/inequality or the sort column; covered columns as
   `INCLUDE` / trailing columns only if the query is hot and the win (an index-only scan) is
   real; a partial predicate if the query always hits one slice; an expression index if the
   filter is on a computed value.
3. **Selectivity check** — for each proposed index, would the planner actually use it? A
   leading column that matches most rows won't be. Reorder for the selective column, or scope
   a partial index to the common predicate value. Where the honest answer is "no index helps
   this predicate", say so.
4. **Write-cost budget** (`audit-and-write-cost.md`) — count the table's existing indexes;
   state what each proposed index adds to every `INSERT`/`DELETE` and to every `UPDATE` that
   touches its columns. On a write-hot table, name the Nth-index decision explicitly.
5. **Redundancy and unused pass** (`audit-and-write-cost.md`) — does an existing index
   already serve this as a leading-column prefix? Can a proposed index replace a narrower
   existing one? Are two existing indexes redundant? Is there an unused index (zero scans
   over a representative window) that should be dropped — freeing write budget for the one
   being added?
6. **The rare-query escape** — for a monthly admin/report query, weigh: accept the scan; a
   temporary index built before the batch and dropped after; run it on a read replica; a
   partial index scoped tight enough that its write cost is negligible. A permanent broad
   index maintained by every write, forever, to serve a query that runs a dozen times a
   year, is the anti-pattern this step exists to stop.
7. **Online build** — on a live populated table, name the non-blocking path for the engine
   (`CREATE INDEX CONCURRENTLY` on Postgres — cannot run inside a transaction, can leave an
   `INVALID` index on failure that must be dropped and rebuilt; `WITH (ONLINE = ON)` on SQL
   Server; native online DDL or `pt-online-schema-change` / `gh-ost` on MySQL).
8. **Re-measure** — re-run the plan after the change. Confirm the planner picks the new
   index *and* the query got faster. An index shipped without that confirmation is a guess
   with write cost attached.

---

## Output block

```
Store:             <engine + version>
Workload:          <each query, tagged hot / warm / rare-admin; table write profile; row counts>
Current plan:      <what EXPLAIN shows today — seq scan / wrong index chosen / sort spill — or
                   "n/a, design-time on a live schema">
Proposed:
  + <table>(<cols>) [INCLUDE (...)] [WHERE <partial predicate>]  — serves <query>;
    est. selectivity <x>; build CONCURRENTLY/ONLINE
  ~ widen <existing index> to (<cols>)  — <why, and which query it now also serves>
  - drop <index>  — unused (0 scans / <window>) | redundant with <other> | superseded by a
    proposed index above
Write-cost delta:  <table>: <N> → <M> indexes; <proposed index> includes hot-updated column
                   <col> — every UPDATE to <col> now maintains it
Rare-query plan:   <accept scan | temp index around the batch | run on replica | tight
                   partial index>  — for <query>
Re-measure:        re-run EXPLAIN (ANALYZE) on <queries>; confirm the new index is chosen and
                   cost drops
Handoff:           <problem-solving-gates (Optimization) — the plan's bottleneck isn't
                   index-shaped (<what it is>) | data-tier-operations — the fix is a replica /
                   partitioning | relational-modeling — the schema forces this query shape |
                   caching-strategy — this hot read shouldn't hit the DB |
                   technical-cost-decision — the storage/IOPS/replica cost | none>
```

---

## Red flags — the tuning isn't done

- An index proposed with no selectivity estimate for its leading column.
- "Add a covering index" with no check that the row is narrow enough or the query hot enough
  to justify the extra write cost.
- A new index added to a table without stating its current index count or the write rate it
  now taxes.
- A composite index whose column order wasn't derived from the query's equality-then-range
  structure.
- A permanent index proposed to serve a query that runs a handful of times a year, with no
  consideration of a temp index or a replica.
- A `DROP INDEX` recommended without checking usage stats *and* without a
  `change-surface-audit` on what else might rely on it.
- The walk stops at "this needs an index on `(a, b)`" without the re-measure step.

---

## Escape hatch

If the user has already designed the index — column order derived, selectivity checked,
write cost weighed, redundancy against the existing set considered — and wants a review or a
tie-break rather than the walk, they say so and get a direct assessment. Opt-in, not the
default.

---

## Example invocations

> "Postgres 15. This query got slow as the table grew to 40M rows: `SELECT id, total,
> created_at FROM orders WHERE customer_id = $1 AND status = 'open' ORDER BY created_at DESC
> LIMIT 20`. `EXPLAIN ANALYZE` shows a bitmap heap scan on `orders_customer_id_idx` then a
> sort. `customer_id` has ~2M distinct values; `status` is 6 values, ~3% are `open`. The
> table takes ~5k inserts/min and `status` is updated once or twice per row's life. Existing
> indexes: PK on `id`, btree on `customer_id`, btree on `created_at`."

Inputs satisfied. Work the walk: equality on `customer_id` + `status` → leading columns;
`created_at DESC` → trailing sort column, so `(customer_id, status, created_at DESC)` serves
the filter *and* the `ORDER BY ... LIMIT` without a sort. `INCLUDE (total)` makes it
index-only for this query — weigh the extra column against the 5k/min write rate. `status`
is updated occasionally → each such update now maintains the new index; acceptable at 1–2
per row lifetime. The standalone `(created_at)` index stays (other queries); the standalone
`(customer_id)` index is now a leading-column prefix of the new one — drop it after the new
one is live and verified. Build `CONCURRENTLY`. Re-measure.

> "We have a table with 14 indexes and writes are getting slow. Which ones can I drop?"

Inputs missing — need the engine, `pg_stat_user_indexes`-style usage counts over a
representative window, the index definitions, and the query workload the kept indexes serve.
Ask for those; then run the redundancy-and-unused pass in `audit-and-write-cost.md`. Don't
guess from the count alone.

> "My API endpoint is slow, what index do I need?"

No query, no plan, no measurement. This is `problem-solving-gates` (Optimization)'s gate
first — profile the endpoint, get the plan for the query that dominates. Come back with that.

---

## Portability

Repo-agnostic. Writes nothing; produces the output block in chat. Copy the `index-tuning/`
directory into another repo's `.claude/skills/` to use it there.
