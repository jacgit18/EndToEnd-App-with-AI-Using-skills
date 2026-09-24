# Indexing and Constraints

Reference for steps 6, 7, and 8 of `modeling-framework.md`.

## Constraints — where each rule lives

For every integrity rule, decide who enforces it. Push down as far as it will go: the database is the only enforcer every writer shares.

### Database enforces

- **`NOT NULL`** — the column must always have a value. Decide this per column deliberately; a nullable column is a claim that "absent" is a meaningful state.
- **`UNIQUE`** — every uniqueness rule from the relationship and key steps, including natural keys behind a surrogate PK.
- **`FOREIGN KEY`** — every reference between tables, with an explicit referential action (below). This is the cheapest integrity you get; omit it only as a conscious, recorded decision.
- **`CHECK`** — value ranges (`price >= 0`), enumerations (`status IN (...)`), simple single-row cross-column rules (`ends_at > starts_at`). Support and expressiveness vary by engine — confirm against the store from step 1.
- **`DEFAULT`** — server-side default so rows are valid even when a writer omits the column.

### Application enforces

Rules the schema structurally cannot express:

- Multi-row / aggregate invariants ("a customer may have at most 3 active subscriptions").
- Rules needing data outside the row (a call to another service, a computed entitlement).
- Rules conditional on workflow state or user role.

Name where each of these lives in the codebase. "The app handles it" without a location is not an answer.

### Trigger enforces

Only for what the above cannot do and what must hold regardless of which writer acts:

- Maintaining a denormalized column or rollup.
- Writing an audit/history row on change.

Triggers are hidden control flow and a per-write cost. Every trigger is a line in the design summary with a reason.

## Referential actions

On each FK, choose what happens when the parent row is deleted or its key changes:

| Action | Use when |
|---|---|
| **`RESTRICT` / `NO ACTION`** (default) | The child rows matter; deleting a referenced parent should fail until they're dealt with |
| **`CASCADE`** | The child rows are meaningless without the parent — order-lines under an order, and only when hard-deleting the order is itself something you do |
| **`SET NULL`** | The relationship is optional and the child stands alone without it — `employee.manager_id` when a manager leaves |
| **`SET DEFAULT`** | Rare — the child should fall back to a sentinel parent row that is guaranteed to exist |

`CASCADE` interacts badly with soft delete — if you soft-delete parents, you are not issuing SQL `DELETE`, so cascade never fires and the application must handle child lifecycle explicitly.

## Index plan

Indexes make reads fast and every write slower; each one is storage plus maintenance on every `INSERT`/`UPDATE`/`DELETE` touching its columns. Build the plan from the access patterns, then stop.

This is the *first-cut* plan, built from access patterns stated in the abstract. Once the schema is deployed and populated — real `EXPLAIN` plans, real column cardinalities, a measured write rate, an existing index set — revising it (composite column order against an actual plan, covering/partial-index trade-offs, redundant/unused-index cleanup, the write-cost budget on a hot table) is `index-tuning`, a separate procedure skill. Don't try to do deployed-schema tuning here on assumed numbers.

### What to index

- **Foreign key columns** used in joins or filters — almost always. (The database does *not* auto-index FK columns in most engines; the constraint and the index are separate.)
- **Each hot query's filter** — an index whose leading column(s) match the `WHERE` equality predicates.
- **Sort / range columns** — after the equality columns in a composite index, so the index also satisfies `ORDER BY` / `BETWEEN`.
- **Uniqueness rules** — as `UNIQUE` indexes.

### Composite index column order

Equality predicates first, then one range or sort column. An index on `(status, created_at)` serves `WHERE status = ? ORDER BY created_at`; reversed, it doesn't.

### What usually not to index

- Low-selectivity single columns — a boolean, a status with a few values, a `type` flag. The index barely narrows the scan. A **partial index** (`WHERE deleted_at IS NULL`, `WHERE status = 'active'`) can be worth it when queries always hit one slice — if the store supports it.
- Columns never used to filter, join, or sort.
- Every column "just in case." Indefinite indexes slow writes and can mislead the planner.

### Output

One line per index: `table(col, col) — the query it serves`. If an index doesn't map to a named query from the gate, cut it or justify it.

## Lifecycle and audit columns

Driven by the gate's lifecycle answer.

- **`created_at` / `updated_at`** — cheap, usually worth having; set server-side (`DEFAULT now()`, and `updated_at` via trigger or app on every update).
- **Soft delete** — `deleted_at timestamp NULL` beats a bare `is_active` boolean: it records *when*, and `NULL` = live. Every read path must filter `deleted_at IS NULL`; a partial index on that predicate keeps the common query fast. Decide up front whether `UNIQUE` constraints should still apply to soft-deleted rows (often you want `UNIQUE(email) WHERE deleted_at IS NULL`).
- **Active vs deleted** — if a row can be deactivated and reactivated, that's a separate `is_active` / `status` column; don't overload `deleted_at` for it.
- **History** — a `<table>_history` table written on change (trigger or app-side), or effective-dated rows (`valid_from` / `valid_to`) when the business asks "what did this look like on date X". Effective-dating changes every query and every unique constraint — adopt it only when that "as of" question is real.
- **Retention / compliance** — record the retention target next to the design. The job that deletes or anonymizes expired rows is out of scope for this skill, but the schema must give it something to act on (a timestamp to age off, a subject id to anonymize).
