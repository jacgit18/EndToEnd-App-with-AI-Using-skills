# Dimensions and Slowly Changing Dimensions

Reference for steps 4 and 7 of `modeling-framework.md`.

## Dimension roles

| Role | What it is | Modelling |
|---|---|---|
| **Conformed** | The same dimension, identical keys and attributes, used by multiple fact tables | Build it **once**. `date`, `customer`, `product` shared across sales / returns / support. Conformance is what lets you compare metrics across processes — never a second copy |
| **Role-playing** | One dimension joined several times in different roles | One physical table; expose per-role views/aliases: `date` → `order_date`, `ship_date`, `due_date`; `employee` → `sales_rep`, `manager` |
| **Degenerate** | An identifier with no descriptive attributes | A column on the **fact** row (order number, invoice ID). No table |
| **Junk** | Several low-cardinality flags with no home of their own | Collapse into one small dimension holding the distinct combinations (`is_gift` × `channel` × `payment_type`), rather than many tiny tables or many fact columns |
| **Outrigger** | A dimension referenced by another dimension | Allowed sparingly (a `date` outrigger on `customer.first_order_date`); overuse is accidental snowflaking |

## The date dimension

Always a real table, never a raw timestamp on the fact. One row per day (add a time-of-day dimension separately if sub-day analysis is needed). Pre-populate years forward. Attributes: full date, day/month/quarter/year numbers and names, day-of-week, week-of-year, is-weekend, is-holiday, fiscal period, relative flags. Surrogate key is often a readable `YYYYMMDD` integer. It's conformed across every fact table with a date.

## Surrogate keys

Every dimension gets a system-generated integer/bigint **surrogate key** as its primary key, distinct from the source's natural/business key. Reasons:

- Type 2 history needs multiple rows per business key — the natural key can't be the PK.
- Insulates the warehouse from source key changes, merges, and re-use.
- Narrow integer joins are faster than compound/string natural keys.
- Lets you add a placeholder row (`-1` = "unknown / not yet arrived") for late-arriving or missing dimensions.

Keep the natural key as a **non-unique** attribute on the dimension (non-unique precisely because Type 2 repeats it across versions).

## Slowly Changing Dimensions

How a dimension attribute's change over time is handled. Decide per attribute (a single dimension often mixes types).

### Type 1 — overwrite

Update the attribute in place. No history — every fact, past and present, now reports the new value. Use for corrections, and for attributes nobody analyses historically (a fixed typo in a product name).

### Type 2 — add a new row (the workhorse)

On a tracked change, version the dimension:

1. Close the current row: set `effective_to` = change date, `is_current` = false.
2. Insert a new row: **new surrogate key**, same business key, new attribute values, `effective_from` = change date, `effective_to` = 9999-12-31, `is_current` = true.
3. Fact rows loaded after the change point at the new surrogate; fact rows already loaded keep pointing at the old one.

Result: "revenue by the region the customer was in *at the time of the sale*" is a plain join; "…by their current region" uses the `is_current` row for that business key. Costs: the dimension grows with change volume; the ETL must, for each fact, resolve the surrogate key that was `effective` at the fact's event timestamp (not "now").

Common Type 2 columns: `surrogate_key`, `business_key`, `effective_from`, `effective_to`, `is_current`, and often `version_number`.

### Type 3 — add a column

Keep a `previous_<attr>` (and maybe `previous_effective_date`) alongside the current value. Only one step of history, one attribute. Rare — use when the business explicitly wants "current vs prior" side by side and changes are infrequent (an annual territory realignment).

### Others (know they exist)

- **Type 0** — never changes (date of birth, original signup date).
- **Type 4** — current values in the main dimension, full history in a separate `*_history` mini-dimension.
- **Type 6** — hybrid (1+2+3): Type 2 rows plus a `current_<attr>` column updated everywhere, so you can report either way without choosing the join.

## Late-arriving data

- **Late-arriving fact** — the event happened days ago but arrived now. Must join to the dimension row that was `effective` at the *event* date, not today's. This is why the ETL keys on event time, not load time.
- **Late-arriving dimension** — a fact references a dimension member that hasn't loaded yet. Insert an inferred/placeholder dimension row (business key known, attributes blank, flagged inferred), point the fact at it, and back-fill the attributes when the real dimension record arrives.
- **Unknown member** — reserve a surrogate key (e.g. `-1`) for "missing / not applicable" so fact FKs are never null and joins never silently drop rows.

## Bridge tables (many-to-many)

When a fact relates to a dimension at a many-to-many grain (a bank account with several owners; a hospital visit with several diagnoses), a direct FK can't express it. Insert a **bridge table** between fact and dimension carrying an allocation/weighting factor, and decide up front whether reports sum the weighted allocation (no double-count) or the full value against each member (intentional double-count). Note the choice — it's a frequent source of wrong totals.
