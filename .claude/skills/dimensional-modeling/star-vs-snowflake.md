# Star, Snowflake, Galaxy — and Fact Tables

Reference for steps 5, 6, and 8 of `modeling-framework.md`.

## The three shapes

| Shape | Dimensions | Use when | Cost |
|---|---|---|---|
| **Star** | Denormalized — one table per dimension, one join from the fact | **Default.** Simplest for BI tools, fewest joins, best scan/join performance on columnar engines | Attribute redundancy in wide dimensions (usually cheap on columnar storage) |
| **Snowflake** | A dimension normalized into sub-tables (product → category → department) | A dimension is genuinely large with heavy repeated attributes, or a sub-hierarchy is shared across dimensions, or the OLAP tool materially benefits | More joins per query, more complex SQL, friction with some BI tools, slower cube builds |
| **Galaxy / fact constellation** | Multiple fact tables sharing **conformed** dimensions | Several business processes analysed together (sales + returns + inventory over shared product/date/store) | Only works if the shared dimensions are truly identical — conformance is the whole discipline |

Default to **star**. Snowflake one named dimension for one named reason. Galaxy is the natural consequence of modelling more than one process, not a design choice you reach for.

**One Big Table (OBT / wide table)** — fact and all dimension attributes flattened into a single table. Legitimate on columnar warehouses for a single-grain mart feeding one tool: no joins, dead simple for analysts. Breaks down when: the grain isn't uniform across rows, attributes need Type 2 history (a flat row can't hold "as-of"), or multiple facts should share dimensions. Treat it as a *serving layer* built from a star, not a replacement for modelling the star.

## Fact-table types

| Type | One row = | Updated after insert? | Fits | Notes |
|---|---|---|---|---|
| **Transaction** | one event at the declared grain | No | Detailed analysis, any additive measure, the most flexible base | Largest table; the default. Everything can be derived from it |
| **Periodic snapshot** | one entity's state per fixed period | No | Balances, levels, "where did things stand each day/week" | Regular even when nothing changed; measures are often semi-additive |
| **Accumulating snapshot** | one instance of a defined pipeline | **Yes** — updated as milestones complete | Workflows with a known lifecycle (order → pick → ship → deliver); milestone lag analysis | Multiple date FKs (one per milestone) and lag measures between them; row churns until the process completes |

A model often carries a transaction fact for detail *and* an accumulating snapshot for milestone timing over the same process.

## Measure additivity

Classify every measure — it determines whether a BI tool can safely `SUM` it across a given dimension.

- **Additive** — summable across **all** dimensions including time. Sales amount, units, cost. The easy case; no special handling.
- **Semi-additive** — summable across some dimensions but **not time**. Account balance, inventory on hand, headcount. You can sum balances across accounts for a given day; summing one account's balance across days is meaningless. Record which dimension(s) it is non-additive over so the BI layer uses `LAST`/`AVG` over time instead of `SUM`.
- **Non-additive** — never summable. Ratios, percentages, unit prices, temperatures. **Store the additive components** (e.g. `revenue` and `order_count`, not `avg_order_value`) and let the query compute the ratio at the required grain. A stored ratio is only correct at the grain it was computed for.

## Degenerate dimensions

A dimension identifier with no accompanying attributes — an order number, a POS transaction ID, a shipment tracking number. It matters for grouping and drill-through but has nothing to describe, so it lives as a column **on the fact table**, not in its own one-column dimension table.

## Factless fact tables

A fact table with only dimension keys and no measures — it records that an event *happened*. Two uses: event tracking ("student X attended class Y on date Z" — count rows) and coverage/negative analysis ("which products were on promotion but sold nothing" — the promotion factless fact minus the sales fact). Worth knowing; reach for it when the "measure" is just the occurrence.
