# Index Mechanics

Reference for steps 2 and 3 of the walk in `SKILL.md` — deriving the access path for one
query, then checking the planner will actually take it.

This is the sibling of `relational-modeling`'s `indexing-and-constraints.md` "Index plan"
section. That one builds a first-cut index list from access patterns described in the
abstract, during table design. This one revises an index against a *real* query plan and
*real* column statistics on a populated table. Same b-tree fundamentals; different evidence.

---

## The b-tree access path

A composite b-tree index is a sorted list on `(c1, c2, c3, …)`. The planner can use it to
satisfy a predicate only as a **left-to-right prefix**: it seeks on `c1`, then within that
on `c2`, and so on — and it can only keep seeking while each column is pinned by an
**equality**. The first non-equality (a range, an `IN` list is a special case, an inequality,
`LIKE 'x%'`) is the last column the index can use for *seeking*; columns after it are only
useful as a **sort order** or as **covered payload**.

So the column order for one query is mechanical:

1. **All equality-predicate columns first.** Order among them barely matters for whether the
   index is used, but put the most selective first — it makes the index useful to the
   widest set of *other* queries and keeps the b-tree seeks tight.
2. **Then one range / inequality / sort column.** `WHERE created_at >= $1`, or `ORDER BY
   created_at`. Only one earns a place here — a second range column can't be seeked, only
   filtered.
3. **Then covered columns** (see "Covering indexes" below), if this query is hot enough to
   want an index-only scan.

### Worked shape

`SELECT … WHERE tenant_id = $1 AND status = $2 AND created_at >= $3 ORDER BY created_at DESC`

→ `(tenant_id, status, created_at DESC)`. The two equalities pin the prefix; `created_at`
then serves both the range seek and the `ORDER BY` (matching the index's declared direction
avoids a separate sort). Reversing to `(created_at, tenant_id, status)` breaks it — the
leading range column means the index can't seek on `tenant_id` at all.

### `ORDER BY` direction

A plain b-tree can be scanned backwards, so `(a, b)` serves `ORDER BY a, b` **and**
`ORDER BY a DESC, b DESC`. It does **not** serve `ORDER BY a, b DESC` — mixed directions need
the index declared with matching per-column direction (`(a, b DESC)`) or the planner falls
back to a sort.

---

## Composite vs. multiple single-column indexes

One `(a, b)` index serves `WHERE a = ?`, `WHERE a = ? AND b = ?`, and `ORDER BY a` — but
**not** `WHERE b = ?` alone. Two separate indexes `(a)` and `(b)` each serve their own
column and can be combined by a **bitmap AND** (Postgres) / **index intersection** (MySQL
8+, SQL Server) for `WHERE a = ? AND b = ?`, but the bitmap path is slower than a single
composite seek and costs two indexes' worth of writes.

Rule of thumb:

- Queries that **always** filter `a` and **sometimes** also `b` → one `(a, b)` composite.
- Queries that filter `a` **or** `b` independently, roughly equally often → two single-column
  indexes, accept the bitmap-AND for the combined case.
- Never build `(a, b)` **and** `(a)` — the second is a redundant prefix (see
  `audit-and-write-cost.md`). `(a, b)` and `(b, a)` are *not* redundant with each other.

---

## Covering indexes / index-only scans

If every column a query touches — `SELECT` list, `WHERE`, `ORDER BY` — is present in the
index, the engine answers it from the index alone and never visits the table heap. That's an
**index-only scan** (Postgres, needs the visibility map current — i.e. the table
`VACUUM`ed), a **covering index** (SQL Server `INCLUDE`, MySQL where the index is a
superset).

- **`INCLUDE (…)` / non-key columns** (Postgres 11+, SQL Server) attach payload columns to
  the leaf level *without* adding them to the sorted key — cheaper to maintain than widening
  the key, and they don't affect column-order rules.
- Worth it when: the query is **hot**, returns **few columns**, and currently does a lot of
  heap fetches (visible as `Heap Fetches:` in a Postgres index-only-scan plan, or a Key
  Lookup in a SQL Server plan).
- Not worth it when: the payload is wide (a `text` body, several columns), the table is
  write-hot (every `INSERT` and every `UPDATE` of an included column now maintains the wider
  leaf), or the heap fetch is already cheap because the rows are few.

State the trade explicitly — a covering index is a read win paid for in write cost and
index size, not a free lunch.

---

## Partial / filtered indexes

An index with a `WHERE` clause (`CREATE INDEX … WHERE status = 'active'` / SQL Server
filtered index) only contains — and only maintains rows for — the slice that matches. Use
when:

- Queries **always** constrain to that slice (`WHERE deleted_at IS NULL`, `WHERE status =
  'open'`, `WHERE archived = false`).
- The slice is a **small fraction** of the table — that's where the size and write-cost
  saving is real. A partial index covering 95% of rows saves almost nothing.
- You want a **conditional `UNIQUE`** — `UNIQUE (email) WHERE deleted_at IS NULL` lets
  soft-deleted rows reuse an email.

A partial index is also the standard answer to a **low-cardinality leading column**: instead
of `(status, created_at)` where `status` barely narrows anything, build
`(created_at) WHERE status = 'open'` — smaller, and only write-taxed for the `open` rows.

Postgres caveat: the planner only uses a partial index when it can *prove* the query's
`WHERE` implies the index predicate. `WHERE status = 'open'` matches `WHERE status = 'open'`;
a parameterized `WHERE status = $1` does **not**, even at runtime with `$1 = 'open'`.

---

## Expression / functional indexes

If a query filters or sorts on a *computed* value, index the expression, not the column:

- `WHERE lower(email) = $1` → `CREATE INDEX … ON users (lower(email))`.
- `WHERE (data->>'country') = $1` on a JSON column → index `((data->>'country'))`, or a GIN
  index on `data` for general containment queries.
- `WHERE date_trunc('day', created_at) = $1` → either index the expression, or (better)
  rewrite the query to a range `created_at >= $1 AND created_at < $1 + interval '1 day'` so a
  plain `(created_at)` index works.

The index expression must match the query's expression **textually** (after parsing) for the
planner to use it.

---

## Why an index that "should" match isn't used

Run through these when the plan shows a seq scan despite a matching index:

| Cause | Tell | Fix |
|---|---|---|
| **Leading column not selective** | Planner estimates the index returns most of the table; a seq scan is genuinely cheaper | Reorder columns, or a partial index on the common value |
| **Predicate not sargable** | `WHERE lower(name) = …`, `WHERE col + 0 = …`, `WHERE col::text = …`, leading-wildcard `LIKE '%x'` — the column is wrapped in a function or cast | Expression index, or rewrite the predicate to leave the column bare |
| **Type mismatch** | `WHERE int_col = '5'` (string literal), `WHERE varchar_col = 5`, or a param bound as the wrong type — an implicit cast on the *column* side kills the index | Match the literal/param type to the column |
| **Stale statistics** | Plan's estimated rows are wildly off actual (`EXPLAIN ANALYZE` shows `rows=1` estimated, `rows=2M` actual) | `ANALYZE <table>` / update stats; if it recurs, raise the stats target. This is a `problem-solving-gates` (Optimization) statistics issue, not an index issue |
| **Small table** | A few thousand rows — a seq scan is a couple of pages, the index adds nothing | Leave it; not a problem |
| **Index just built, not `ANALYZE`d** | Postgres `CREATE INDEX` analyzes; `CREATE INDEX CONCURRENTLY` on an expression index may need a manual `ANALYZE` | `ANALYZE <table>` |
| **`OR` across columns** | `WHERE a = ? OR b = ?` can't use a single composite | Split into a `UNION`, or two indexes for a bitmap `OR` |
| **Function-based `ORDER BY` / mixed direction** | `ORDER BY a, b DESC` against a `(a, b)` index | Declare the index `(a, b DESC)` |

---

## Non-b-tree index types (know when to reach for one)

| Type | For | Engines |
|---|---|---|
| **b-tree** | Equality, range, sort, prefix `LIKE 'x%'` — the default, ~95% of cases | all |
| **hash** | Equality only, no range/sort; marginal vs. b-tree, rarely worth it | Postgres, MySQL (memory tables) |
| **GIN** | Multi-value columns — array containment, `jsonb` `@>`, full-text `tsvector`, trigram `LIKE '%x%'` (with `pg_trgm`) | Postgres |
| **GiST / SP-GiST** | Geometric, range-type overlap, nearest-neighbour (`ORDER BY point <-> $1`), exclusion constraints | Postgres |
| **BRIN** | Very large tables where the column is naturally correlated with physical order (append-only `created_at`, an event log) — tiny index, coarse; good for range scans over huge tables | Postgres |
| **Full-text / `FULLTEXT`** | Natural-language search | MySQL, SQL Server |
| **Columnstore** | Analytical aggregate scans over a large table — a different storage model, not a secondary index; if this is the answer the workload is OLAP → `data-tier-operations` / `dimensional-modeling` | SQL Server, MySQL HeatWave |

---

## Clustered index / heap implications

- **Postgres** — heap-organized; every index is secondary and stores a tuple pointer.
  `CLUSTER` is a one-time physical reorder, not maintained. No special PK-choice concern for
  index tuning beyond the usual.
- **MySQL/InnoDB & SQL Server clustered tables** — the table *is* the clustered index, keyed
  on the PK (InnoDB) or the chosen clustered key. Every secondary index stores the **clustered
  key** as its row locator, so a wide clustered key (a `UUID`, a multi-column natural key)
  inflates *every* secondary index. If secondary indexes are large and the PK is a random
  `UUID`, that's a schema issue → `relational-modeling` (surrogate `bigint` PK + `UNIQUE`
  external id).
- A secondary index lookup that isn't covering does a **key lookup** back into the clustered
  index — the covering-index calculus above matters more on these engines than on Postgres.
