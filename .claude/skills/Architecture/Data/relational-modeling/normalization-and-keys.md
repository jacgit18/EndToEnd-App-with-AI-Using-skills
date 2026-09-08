# Normalization and Keys

Reference for steps 4 and 5 of `modeling-framework.md`.

## Normal forms, short version

Design to **3NF** by default. Higher forms (BCNF, 4NF, 5NF) matter for specific dependency shapes and are rarely worth the extra tables in an OLTP design — reach for them only when you can name the anomaly they fix.

| Form | Rule | You've violated it when |
|---|---|---|
| **1NF** | Every column holds a single atomic value; every row is unique | A column holds a comma-list, a JSON blob standing in for columns, or "phone1, phone2, phone3" |
| **2NF** | 1NF, and every non-key column depends on the *whole* primary key | On a table keyed by `(order_id, product_id)`, you store `customer_name` — it depends on `order_id` alone |
| **3NF** | 2NF, and no non-key column depends on another non-key column | You store `zip` and `city` — `city` is a function of `zip`, not of the key (transitive dependency) |

The one-line test for 3NF: **every non-key column depends on the key, the whole key, and nothing but the key.**

## When denormalization is the right call

Denormalization is deliberate, justified redundancy — not sloppiness. It is warranted when a *named* read pattern from the gate is hurt by normalization and the cost of keeping the copy correct is acceptable:

- **Read-heavy hot path with an expensive join** — duplicate the one column that removes the join. Not the whole row.
- **Aggregates queried far more than the underlying rows change** — store `comment_count` on `post` instead of `COUNT(*)` on every render.
- **Reporting / list views** — a pre-joined table or a materialized view, refreshed on a schedule the business can tolerate being stale by.

Every denormalization must answer: **what keeps the copy correct?** Options, roughly in order of preference:

1. Application code writes both places in the same transaction.
2. A database trigger maintains the copy.
3. A scheduled job / materialized-view refresh (only when staleness is acceptable).

No answer → don't do it. An out-of-sync denormalized column is worse than a slow query.

## Anti-normalization smells

- **Wide sparse table** — many columns null for any given row. Usually two or more entities crammed together; split them.
- **Repeating column groups** — `line_item_1_sku`, `line_item_2_sku`, … — that's a child table.
- **JSON column doing a table's job** — fine for genuinely schemaless payload, a smell when you find yourself querying inside it with `->>` on a hot path.

## Choosing keys

### Primary key: default to a surrogate

A surrogate `bigint` identity/serial column as PK is the default because it is small, immutable, monotonic (good for clustered-index write locality), and never needs to change when the business changes. Natural attributes that "look unique" — email, username, SKU, SSN — change, get reused, or turn out non-unique across edge cases.

Use a **natural key as PK** only when it is all of: genuinely immutable, single-column, externally assigned, and already required to be unique (e.g. an ISO country code table).

### Keep the natural key as a constraint

When the PK is surrogate but a real business key exists, add it as `UNIQUE` — `UNIQUE(email)`, `UNIQUE(student_id, course_id, term_id)`. The surrogate is for joins and stability; the `UNIQUE` is the actual integrity rule and the schema should state it.

### UUIDs — only for a reason

UUIDs earn their cost when you need:

- **client- or service-generated ids** (the id exists before the row hits the database),
- **ids in URLs / external references** where sequential integers would leak volume or invite enumeration,
- **uniqueness across databases or shards** without coordination.

Costs to note when you use them:

- Wider than `bigint` (16 bytes vs 8) — bigger PK, bigger every FK, bigger every index.
- **Random** UUIDs (v4) scatter inserts across a clustered index → page splits and fragmentation. On stores with clustered PKs (SQL Server, MySQL/InnoDB), prefer an ordered form (UUIDv7, ULID, or `NEWSEQUENTIALID()`), or keep the surrogate `bigint` PK and carry the UUID as a `UNIQUE` external id.
- Use the native `uuid` type, never `varchar(36)`.

### Composite keys

Fine as a `UNIQUE` constraint on a junction table. As a *primary* key they propagate every column into child FKs — usually a reason to give the junction its own surrogate PK and keep the composite as `UNIQUE`.
