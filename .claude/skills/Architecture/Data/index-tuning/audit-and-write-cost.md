# Audit and Write Cost

Reference for steps 4, 5, 6, and 7 of the walk in `SKILL.md` — pricing a new index against
the write workload, finding the dead indexes already on the table, handling a query that
doesn't deserve a permanent index, and building on a live table without locking it.

---

## What an index costs a write

Every index on a table is maintained synchronously inside each writing transaction:

- **`INSERT`** — one index entry added to every index on the table.
- **`DELETE`** — one index entry removed from every index (or marked dead, then vacuumed).
- **`UPDATE`** — an index is touched **only if the update changes one of its columns**
  (key or `INCLUDE`d). An `UPDATE` that sets `last_seen_at` on a row costs nothing for an
  index on `(customer_id, status)` — but costs a full delete+insert in the index for one on
  `(customer_id, last_seen_at)`. Postgres HOT updates skip *all* index maintenance when no
  indexed column changed and the page has room — another reason not to index a hot-updated
  column casually.
- **Storage & cache** — each index is more pages competing for the buffer pool / page cache.
  A table with 12 indexes may have more index than heap in RAM.
- **Planning** — more candidate paths for the planner to cost on every query.
- **`VACUUM` / index maintenance** — more indexes, longer vacuum, more bloat surface.

### The write-cost budget

State it as a number, not a vibe:

- Current index count on the table, and the write rate (`INSERT`/`DELETE`/s, and
  `UPDATE`/s broken down by whether they touch a would-be-indexed column).
- What the proposed index adds: `+1 index entry per insert/delete`, and `+1
  delete+insert per UPDATE of <col>` if a mutable column is in it.
- On a table doing thousands of writes/s with an existing handful of indexes, adding another
  is a **decision with a stated cost**, and the right move is often to *replace* an existing
  index (widen one to serve both queries) or *drop* a dead one to make room — not to
  monotonically add.

There's no universal "max indexes" number, but past ~5–6 on a write-hot OLTP table, each
new one should be justified against dropping another.

---

## Redundancy pass — before adding anything

### Exact and prefix duplicates

- **Exact duplicate** — same columns, same order, same partial predicate: drop one. (Different
  *name*, same definition — surprisingly common after years of migrations.)
- **Prefix redundancy** — `(a)` is redundant if `(a, b)` exists: any query the narrow one
  serves, the wide one serves too (slightly larger, negligible). Drop the prefix — *unless*
  the narrow one is `UNIQUE` and the wide one isn't (the constraint is doing work), or the
  narrow one is significantly smaller and serves a extremely hot equality-only query where
  every page counts.
- **Not redundant**: `(a, b)` and `(b, a)`; `(a, b)` and `(a, c)`; `(a)` and `(a) WHERE
  active` (different row sets).

### Near-redundancy worth consolidating

- `(a, b)` and `(a, c)` where a single `(a, b, c)` or `(a, b) INCLUDE (c)` would serve both
  query shapes — consolidate if the combined index isn't absurdly wide and both source
  queries lead with `a`.
- Several indexes all leading with the same low-selectivity column — a sign the column
  order is wrong (see `index-mechanics.md` selectivity) or these should be partial indexes.

---

## Unused-index detection

Usage counters are cumulative since the last stats reset — read them over a window that
includes **every** periodic job (month-end close, quarterly reports, the annual audit
export). An index with zero scans over a full business cycle is a real drop candidate; one
with zero scans over a Tuesday afternoon is not.

**Postgres**

```sql
SELECT s.relname AS table, s.indexrelname AS index,
       s.idx_scan AS scans, pg_size_pretty(pg_relation_size(s.indexrelid)) AS size,
       s.idx_tup_read, s.idx_tup_fetch
FROM pg_stat_user_indexes s
JOIN pg_index i ON i.indexrelid = s.indexrelid
WHERE NOT i.indisunique                 -- keep unique indexes; they enforce a constraint
ORDER BY s.idx_scan ASC, pg_relation_size(s.indexrelid) DESC;
```

Also check `pg_stat_user_indexes` on **replicas** — an index unused on the primary may serve
read-replica reporting traffic. Check `stats_reset` in `pg_stat_database` to know how long
the window really is.

**SQL Server**

```sql
SELECT OBJECT_NAME(i.object_id) AS table_name, i.name AS index_name,
       us.user_seeks, us.user_scans, us.user_lookups, us.user_updates
FROM sys.indexes i
LEFT JOIN sys.dm_db_index_usage_stats us
  ON us.object_id = i.object_id AND us.index_id = i.index_id
     AND us.database_id = DB_ID()
WHERE i.type_desc = 'NONCLUSTERED' AND i.is_unique = 0
ORDER BY (ISNULL(us.user_seeks,0) + ISNULL(us.user_scans,0) + ISNULL(us.user_lookups,0)) ASC;
```

Counters reset on service restart and (per-DB) on some operations — confirm uptime.
`user_updates` high with seeks/scans/lookups at zero is the clearest "pure write cost, no
read benefit" signal.

**MySQL (8.0+)**

```sql
SELECT object_schema, object_name, index_name, count_star, count_read, count_write
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE index_name IS NOT NULL AND index_name <> 'PRIMARY'
ORDER BY count_read ASC;
```

Or `sys.schema_unused_indexes` (a prebuilt view) and `sys.schema_redundant_indexes`.

### Dropping safely

A `DROP INDEX` is a **removal** — run it through `change-surface-audit`'s hidden-dependents
lens even for an index:

- A query that *currently* seeks it will fall back to a scan or a worse index — check the
  plan of the known consumers first, not just the usage count.
- An index backing a `FOREIGN KEY` (some engines require/strongly prefer one on the child
  side) — dropping it can make cascade deletes and FK checks table-scan.
- A `UNIQUE` index is also a constraint — dropping it drops the guarantee.
- Postgres: drop with `DROP INDEX CONCURRENTLY` to avoid an `ACCESS EXCLUSIVE` lock. Consider
  making it invisible first (`ALTER INDEX … SET (…)` isn't it — Postgres has no invisible
  index; use a staged deploy). MySQL 8 and SQL Server 2019+ have **invisible / disabled**
  indexes — flip to invisible, watch for regressions for a cycle, then drop. That's the safe
  path when usage stats are ambiguous.

---

## The rare-query playbook

For a query that runs infrequently (month-end, an admin screen used twice a week, an ops
one-off), a permanent index maintained by every write forever is usually the wrong trade.
In rough order of preference:

1. **Accept the scan.** If the table is moderate and the query runs monthly off-peak, a
   30-second sequential scan is fine. Say so and stop — no index.
2. **Run it on a read replica.** Reporting and admin reads against a replica take the scan
   cost off the primary entirely and need no new index anywhere. If the query is analytical
   and recurring, this plus a replica is the answer → note the handoff to
   `data-tier-operations` for the replica itself.
3. **Temporary index around the batch.** For a scheduled heavy job: `CREATE INDEX
   CONCURRENTLY` before the run, `DROP INDEX CONCURRENTLY` after. The write cost exists only
   during the job window. Worth scripting into the job itself.
4. **A tightly-scoped partial index.** `… WHERE status = 'pending_review'` where only a few
   hundred rows ever match — the write cost is proportional to that slice, effectively
   nothing, and the admin query that always filters on `pending_review` gets a seek.
5. **Permanent index** — only if the query, though infrequent, has a **latency requirement**
   (a user waits on it) and none of the above fit.

Name which of these applies in the output block's `Rare-query plan:` line.

---

## Online / non-blocking builds on a live table

| Engine | Non-blocking build | Catch |
|---|---|---|
| **Postgres** | `CREATE INDEX CONCURRENTLY` | Cannot run inside a transaction block or with other DDL batched. Takes two table scans, slower wall-clock. On failure or interruption leaves an **`INVALID`** index that still costs writes but serves no reads — find with `pg_index.indisvalid = false`, `DROP` and retry. `DROP INDEX CONCURRENTLY` likewise. |
| **SQL Server** | `CREATE INDEX … WITH (ONLINE = ON)` | Enterprise edition (and Azure SQL); Standard is offline. Brief `Sch-M` lock at start and end. Higher tempdb and log use. |
| **MySQL / InnoDB (8.0)** | Most `CREATE INDEX` is online by default (`ALGORITHM=INPLACE, LOCK=NONE`) | A few index types/changes force `COPY` (table rebuild, blocks writes) — check `SHOW WARNINGS` after the `ALTER`. Long-running build holds a metadata lock that can queue behind/ahead of other DDL. |
| **MySQL, older / safest** | `pt-online-schema-change` or `gh-ost` | External tooling; copies the table via triggers/binlog. Needs disk headroom equal to the table and a plan for foreign keys. |

Always: build during a lower-traffic window even when "online", and watch replication lag —
the build replays on replicas too.

---

## Bloat (Postgres, briefly)

Repeated updates/deletes leave dead entries; an index can grow well past its ideal size,
slowing scans and wasting cache.

- Detect: compare `pg_relation_size(indexrelid)` to an estimate, or use the `pgstattuple`
  extension (`pgstatindex`).
- Fix: `REINDEX INDEX CONCURRENTLY <name>` (Postgres 12+). Not a tuning change — a
  maintenance action — but it's the answer when "the index exists and is used and the query
  is still slow" and the index is 3× the size it should be.
- Prevention is `autovacuum` tuned for the table's churn — an `observability-strategy` /
  ops concern, noted here so the tuning walk doesn't misread bloat as a missing index.
