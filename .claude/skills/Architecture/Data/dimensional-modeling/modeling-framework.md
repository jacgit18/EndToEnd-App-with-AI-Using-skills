# Modeling Framework

Work these in order once the gate in `SKILL.md` is satisfied. Steps 2–5 are Kimball's four steps; the rest complete the design.

## 1. Confirm the analytical need is real and distinct from OLTP

Before modelling, check this is actually a dimensional problem:

- **Recurring analytical reporting over history**, sliced many ways, by more than a throwaway query → proceed.
- **One slow dashboard query on the operational database** → not this skill. A pre-aggregated rollup table or an indexed/materialized view is the fix (`relational-modeling`), or a read replica to move reporting load off the primary (`data-tier-operations`). Say so and stop.
- **"We might want analytics someday"**, no named reports → premature. The deliverable is "come back with the questions in gate item 5", not a star schema.

Also confirm the target from gate item 9. If it's a separate warehouse system whose technology/ownership isn't decided, that's `database-architecture`'s call first.

## 2. Choose the business process

One fact table per business process. Name each process as the event being measured — "orders placed", "inventory movements", "ticket state-changes" — not as a subject area ("sales").

If gate item 3 named several processes, list them and model the highest-value one first. Note which **dimensions they share** — those become conformed dimensions (step 4) and the marts become a galaxy.

## 3. Declare the grain — explicitly, first

Write one sentence: **"One row in the fact table represents ______."** The finest, most atomic level the source and the questions support — "one order line", "one ticket state-change", "one account, one day".

Rules:

- **Do not mix grains** in one fact table. Daily snapshots and individual transactions are two fact tables, not one with a `type` column.
- **Prefer the atomic grain.** You can always aggregate up; you can never split down. Pre-aggregated fact tables are additions (step 9), not replacements for the atomic one.
- Every later step is checked against this sentence. If a proposed dimension or measure doesn't fit the grain, the grain is wrong or the table is wrong.

The grain is near-irreversible once data is loaded and reports are built on it — treat it with the weight `data-tier-operations` gives a shard key.

## 4. Identify the dimensions

For the declared grain, ask who / what / when / where / why / how. Each answer is a dimension. Then classify each — see `dimensions-and-scd.md`:

- **Conformed** — shared, identical, across multiple fact tables (one `date` dimension, one `customer` dimension for orders *and* returns *and* support). Define these once; never a second `date` table.
- **Role-playing** — the same dimension joined multiple times in different roles: `date` as `order_date`, `ship_date`, `due_date`. One physical table, multiple views/aliases.
- **Degenerate** — a dimension attribute with no other attributes, kept on the fact row itself: an order number, an invoice ID. No dimension table for it.
- **Junk** — several low-cardinality flags/indicators (`is_gift`, `channel`, `payment_type`) collapsed into one small dimension instead of many tiny ones or many degenerate columns.

Every dimension gets a **surrogate key** (step 7). Give each its hierarchy levels (geography: country → region → city; date: year → quarter → month → day).

## 5. Identify the measures

The numeric facts stored on the fact row. For each, classify additivity — see `star-vs-snowflake.md`:

- **Additive** — can be summed across *every* dimension (sales amount, quantity). The easy case.
- **Semi-additive** — summable across some dimensions but not time (account balance, inventory on hand — you sum across accounts, but not across days). Note which dimension it is *not* additive over.
- **Non-additive** — cannot be summed at all (ratios, percentages, unit price). Store the **fully-additive components** (numerator and denominator) and compute the ratio at query time; don't store the ratio as the only fact.

The fact table holds: dimension foreign keys (surrogate), degenerate dimensions, and measures. Nothing else — no descriptive text, no attributes that belong in a dimension.

## 6. Pick the schema shape

From `star-vs-snowflake.md`:

- **Star** — default. Denormalized dimensions, each one join from the fact. Fewer joins, simplest for BI tools, best query performance. Choose this unless there's a concrete reason not to.
- **Snowflake** — normalize a specific dimension into sub-tables. Only when a dimension is genuinely large with heavy attribute redundancy, or a sub-hierarchy is reused across dimensions, or the BI/OLAP tool specifically benefits. Name the dimension and the reason; don't snowflake wholesale.
- **Galaxy / fact constellation** — multiple fact tables sharing conformed dimensions. The natural result of step 2 having several processes. Not a choice so much as a consequence — make sure the shared dimensions are truly conformed.

## 7. SCD strategy per dimension

For each dimension, from gate item 7 and `dimensions-and-scd.md`:

- **Type 1 — overwrite.** No history; the attribute always shows its current value. Fine for corrections and attributes nobody reports historically.
- **Type 2 — new row.** Preserves history: on change, close the old row (`effective_to`, `is_current = false`) and insert a new one with a new surrogate key, `effective_from`, `is_current = true`. Fact rows point at the surrogate that was current when the fact occurred, so "who owned this then" works. Costs: dimension grows, and the load must resolve the right surrogate key at fact-load time.
- **Type 3 — add a column** (`previous_region`). Rare; only when exactly one prior value matters and the change is infrequent.

Produce an **SCD map**: dimension → type, and for Type 2 the trigger attributes. Mixed within a dimension (some attributes Type 1, some Type 2) is normal — call it out.

All dimensions get a surrogate integer/bigint key as PK. Retain the source natural/business key as a non-unique attribute (non-unique because Type 2 repeats it across versions).

## 8. Fact-table type

From the grain and the questions, per `star-vs-snowflake.md`:

- **Transaction** — one row per event, inserted once, never updated. The default and most flexible. "One order line", "one click".
- **Periodic snapshot** — one row per entity per period, capturing state at that time. "One account, end of each day". For trend/balance reporting where transaction-level replay is expensive.
- **Accumulating snapshot** — one row per pipeline instance, *updated* as it moves through milestones (order placed → picked → shipped → delivered, each with its own date FK and a lag measure). For process/workflow analytics with a defined lifecycle.

A model often needs more than one — a transaction fact for detail and an accumulating snapshot for milestone lags.

## 9. Rollups and aggregates

For the heavy recurring reports in gate item 5, define pre-aggregated fact tables or materialized views at coarser grain ("sales by product by day" over the atomic "sales by line"). Each rollup records: its grain, which base fact it derives from, and its refresh (rebuilt each load, incrementally maintained, or on a schedule tolerable-stale by N hours). The atomic fact table stays; rollups are performance additions layered on it.

## 10. Load plan

Not the pipeline code — the shape of it:

- **Source** — which tables/streams from gate item 1/8.
- **ELT vs ETL** — on a columnar warehouse, ELT (load raw, transform in-warehouse with dbt/SQL) is the common default; note if there's a reason for ETL.
- **Cadence** — from gate item 8 (daily batch, hourly, streaming). Match it to the decision latency, not to "as fresh as possible".
- **Type 2 handling** — how the load detects changed dimension attributes and versions the rows; how fact loads look up the surrogate key that was current at the event time.
- **Late-arriving data** — late facts (event arrives days after it happened — needs the historically-correct dimension key) and late dimensions (fact arrives before its dimension row — needs an inferred/placeholder member). State the policy.
- **Idempotency / reload** — how a re-run of a batch avoids double-counting (delete-and-reload a partition, merge on a natural key).

## 11. ERD and specs

Produce:

- A dimensional ERD — fact table centre, dimensions around it, `mermaid erDiagram` or ASCII — showing surrogate FKs and hierarchies.
- The **grain statement** at the top of the doc, verbatim from step 3.
- A spec per table: dimensions (surrogate key, business key, attributes, hierarchy levels, SCD type, effective-date columns for Type 2); fact (grain, FKs, degenerate dimensions, measures with additivity, fact-table type).
- The SCD map and the load plan.
- The design summary block from `SKILL.md`.

Write to `docs/data-model/analytics/<slug>.md`. Then stop — ETL/ELT is a separate step.
