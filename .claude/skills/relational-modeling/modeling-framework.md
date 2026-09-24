# Modeling Framework

Work these in order once the gate in `SKILL.md` is satisfied. Each step produces written output; the collected output becomes the table spec and the design summary.

## 1. Confirm the prerequisite

State which ADR (or which explicit user statement) fixes the store as relational. If you cannot point to one, stop — the user needs `database-architecture` first. Record the store technology; some choices below depend on it (clustered vs heap tables, UUID types, partial indexes, `CHECK` support).

## 2. Entities to tables

List each entity from the gate as a candidate table. For each: the columns it obviously has, and which of those are attributes of *this* entity versus attributes that belong to something it relates to. An attribute that depends on another entity's identity is a signal you have a second table or a junction.

Do not create tables for concepts that are pure enumerations with no attributes of their own — a `status` with five fixed values is a column (optionally a `CHECK` or an enum type), not a table, unless the set changes at runtime or carries metadata.

## 3. Relationships to structure

For each relationship from the gate, pick the representation:

| Cardinality | Representation |
|---|---|
| **one-to-many** | FK column on the "many" side pointing at the "one" side's key |
| **many-to-many** | a junction table holding both FKs, plus any attributes of the pairing itself (when, status, quantity, role) and a `UNIQUE` on the FK pair |
| **one-to-one** | usually the same table; split only for a real reason — optional/rarely-populated columns, different access frequency, different security |
| **self-referencing** (hierarchy, "reports to", "parent category") | a nullable FK on the table pointing at its own key; note the read pattern — recursive queries (`WITH RECURSIVE`) vs a closure table vs a materialized path, driven by how deep and how often it's traversed |

Name every junction table now. The junction is where many-to-many attributes live — resist putting them on either parent.

## 4. Normal form and exceptions

Default target is **3NF** — every non-key column depends on the key, the whole key, and nothing but the key. See `normalization-and-keys.md` for the short version of 1NF→3NF.

Then, only against the access patterns from the gate, name any denormalization:

- A column duplicated onto a child table to avoid a join on a hot read path.
- A rolled-up count or sum stored on the parent instead of aggregated each time.
- A pre-joined reporting table or materialized view.

Each denormalization gets: what is duplicated, which query justifies it, and how the copy stays correct (trigger, application write, scheduled refresh). A denormalization with no answer to "how does it stay correct" is a bug in waiting — don't record it.

If everything is under ~10k rows and reads are simple, say that 3NF with no exceptions is fine and move on; don't manufacture optimizations.

## 5. Keys

For each table, choose per `normalization-and-keys.md`:

- **Primary key**: default to a surrogate `bigint`/identity. Use a natural key as PK only when it is truly immutable, single-column, and already required unique.
- **Natural / business key**: if one exists, add it as a `UNIQUE` constraint even when the PK is surrogate — it is real integrity and the design should enforce it.
- **UUID**: only for a stated need — client-generated ids, ids exposed in URLs where enumeration is a concern, or cross-system uniqueness. If used, note the type (`uuid`, not `varchar`) and, for a clustered-index store, the write-locality cost of random UUIDs versus an ordered variant.

## 6. Constraints — what the database enforces

Per `indexing-and-constraints.md`, decide for each rule where it lives:

- **Database**: `NOT NULL`, `UNIQUE`, `FOREIGN KEY` (with an explicit referential action — `RESTRICT`/`NO ACTION`, `CASCADE`, `SET NULL`, `SET DEFAULT`), `CHECK` for value ranges and simple cross-column rules, `DEFAULT`.
- **Application**: multi-row invariants, rules that need external data, anything conditional on user role or workflow state. Name where in the code it lives.
- **Trigger**: only for things the above can't do and that must be guaranteed regardless of writer — maintaining a denormalized copy, an audit row. Note that triggers are a maintenance and performance cost; use sparingly.

Default the FK action to `RESTRICT`/`NO ACTION` unless the child rows are genuinely meaningless without the parent (`CASCADE`) or genuinely stand alone (`SET NULL`).

## 7. Indexes

Build the index plan from the access patterns, per `indexing-and-constraints.md`:

- Every FK column used in a join or filter gets an index.
- Each hot query gets an index whose leading columns match its filter, then its sort.
- Composite index column order: equality filters first, then the range/sort column.
- Add a `UNIQUE` index for every uniqueness rule from steps 3 and 5.
- Then stop. Each index is write and storage cost; low-selectivity single-column indexes (a boolean, a status with three values) usually don't earn it — a partial index may, if the store supports it.

Write one line per index: `table(col, col) — the query it serves`.

## 8. Lifecycle and audit columns

From the gate's lifecycle answer:

- **Hard delete, no history**: nothing to add beyond `created_at` / `updated_at` if useful.
- **Soft delete**: a `deleted_at timestamp NULL` (preferred over a bare `is_active` boolean — it records when) and a note that every read path must filter it; consider a partial index `WHERE deleted_at IS NULL`.
- **Active flag** distinct from deletion (a user can deactivate and reactivate): an explicit `status` or `is_active` column, separate from `deleted_at`.
- **History / audit**: a separate `<table>_history` or `<table>_audit` table written on change (trigger or app), or effective-dated rows (`valid_from` / `valid_to`) if the business queries "as of" a past date.
- **Retention / compliance driven**: note the retention target and that a deletion or anonymization job will act on these columns — that job is out of scope here but the schema must make it possible.

## 9. ERD and table specs

Produce:

- An ERD — a `mermaid erDiagram` or ASCII — showing tables, PK/FK, and cardinality.
- A spec per table: every column with type, nullability, default; PK; FKs with referential actions; UNIQUE constraints; CHECKs; indexes.
- The design summary block from `SKILL.md`.

Write it to `docs/data-model/<slug>.md`. Then stop — migrations are a separate step.
