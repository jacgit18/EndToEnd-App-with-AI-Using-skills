---
name: dimensional-modeling
description: Designs an analytical (OLAP) data model — the business process and the fact-table grain, the dimensions and which are conformed / role-playing / degenerate / junk, additive vs semi-additive measures, star vs snowflake vs galaxy shape, slowly-changing-dimension strategy per dimension, fact-table type (transaction / periodic snapshot / accumulating snapshot), and pre-aggregated rollups plus a refresh plan. Use this skill when someone needs a warehouse or data-mart model, asks "star or snowflake", "what's the grain", "how do I handle a dimension that changes over time / SCD", "fact and dimension tables for X", "how do I model this for reporting / BI / dashboards", or is designing a reporting layer over historical data. It produces a dimensional ERD, table specs, a grain statement, an SCD map and a load plan — not ETL/pipeline code, not OLTP table design (that is `relational-modeling`), and not the where-does-the-warehouse-live decision (that is `database-architecture`).
---

# Dimensional Modeling

Design the analytical model: pick the business process, nail the grain, build the star. The skill makes the user state the process, the grain, and the actual questions the business asks before any fact or dimension table is drawn, recommends a shape with the tradeoffs named, and produces a spec.

## When to use

- Someone needs a **data-mart or warehouse model** for reporting, BI, dashboards, or historical trend analysis.
- The question is dimensional: **star vs snowflake vs galaxy**, what the **grain** is, **fact vs dimension**, additive vs semi-additive measures, **conformed dimensions** across marts.
- A **dimension changes over time** and the business needs history — SCD Type 1 / 2 / 3.
- An OLTP schema needs a **reporting counterpart** because analytical queries are contorting the transactional model.

## Out of scope — hand these off

- **OLTP / transactional table design** — normalization, keys, indexes, constraints on the operational database → `relational-modeling`. This skill is the analytical (OLAP) counterpart; the two are different disciplines with opposite defaults (normalize vs denormalize).
- **Whether a warehouse is warranted at all**, and **where it lives / which technology** — Redshift vs BigQuery vs Snowflake vs "just a schema in Postgres", who owns it, source-of-truth → `database-architecture`. The "one slow dashboard query, should we build a warehouse?" case in particular is not this skill — that's a rollup (`relational-modeling`) or a replica (`data-tier-operations`); see "Challenge the framing". If the warehouse is a real separate system whose platform isn't settled, settle it there first.
- **Scaling an existing warehouse** (distribution keys, sort keys, cluster sizing, slow-query tuning on the warehouse) → `data-tier-operations`. **The warehouse bill** → `technical-cost-decision`.
- **The ETL/ELT pipeline itself** — extraction, transformation code, orchestration (Airflow/dbt/Dagster), CDC. The skill produces a *load plan* (what must happen, cadence, how Type 2 changes land) but not the implementation.
- **BI tool / dashboard / report layout**, and **ML feature stores**.

---

## The gate

Before drawing any fact or dimension table, these must be answered.

**Facts you may surface from the repo** (state for confirmation):

1. **Source system(s)** — the OLTP schema or event stream this model derives from.
2. **Existing analytical assets** — a warehouse, other marts, conformed dimensions already defined, the BI tool in use.

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not model without them. If any is missing, name it and stop:

3. **Business process** — the activity being measured, named as a verb-ish event: "orders placed", "support tickets resolved", "shipments delivered", "ad impressions served". Not "sales data" — the *process*. One fact table per process; if there are several, list them.
4. **Grain** — one row of the fact table will represent *what*, at the finest level: "one order line", "one ticket state-change", "one daily account balance". This is the load-bearing decision; everything downstream derives from it. A vague grain ("order stuff") is not an answer.
5. **The questions** — the actual reports and metrics the business asks for: "revenue by region by month", "median resolution time by agent by week", "impressions and CTR by campaign by day". A real list, not "we want insights".
6. **Dimensions** — how they need to slice those questions: by time, customer, product, geography, channel, agent, campaign, …
7. **History** — do dimension attributes change (a customer moves region, a product changes category), and does the business need to see the value **as it was** at the time of the fact (SCD Type 2), or is the **current** value always fine (Type 1)? Per dimension if it varies.
8. **Source & refresh** — where the data comes from, and how fresh it must be for the decisions it drives: real-time, hourly, daily batch, weekly.
9. **Scale & target** — rough fact-row volume and growth, and where this lands: a columnar warehouse (Redshift / BigQuery / Snowflake), a smaller mart, or a set of reporting tables in the existing operational database.

"Model our data for reporting" with 3–9 absent is not valid input.

---

## Challenge the framing

If the user opens with the design half-made, put their reasoning under the gate, then test it against `star-vs-snowflake.md` / `dimensions-and-scd.md`:

- **"we need a data warehouse"** — how many business processes, how many consuming teams, is this org-wide integration or one team's reporting? A single team reporting on one process is a **mart** (or even a few rollup tables), not a warehouse. And if the "analytics" is one slow dashboard query on the app database, this is the wrong skill — that's an indexed rollup (`relational-modeling`) or a read replica (`data-tier-operations`).
- **"snowflake it for a clean design"** — snowflaking costs join complexity and friction with most BI tools; **star is the default**. Which specific dimension is genuinely large or deeply hierarchical enough to justify normalizing it?
- **"one big flat table"** — legitimate for a single-grain mart on a columnar engine; the risk is mixed grain and lost history. Is every row truly the same grain? Do any attributes need Type 2 history that a flat table can't hold?
- **"real-time warehouse"** — which decision actually needs sub-hour data? Streaming ingestion and incremental Type 2 handling are a large, ongoing cost; daily batch covers most BI. Name the decision that breaks at 24-hour latency.
- **"reuse the OLTP tables directly for reporting"** — the transactional model changes shape, has no history, and analytical scans will contend with production writes. A separate model with conformed dimensions is usually worth it once reporting is recurring.

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `modeling-framework.md` in order once the gate is satisfied. In short (Kimball's four steps, plus the rest): confirm the analytical need is real and distinct from OLTP → pick the business process → **declare the grain explicitly** → identify the dimensions (mark conformed / role-playing / degenerate / junk) → identify the measures (additive / semi-additive / non-additive) → pick the schema shape → set an SCD strategy per dimension with surrogate keys → pick the fact-table type → define rollups and a refresh plan → produce the ERD and specs.

Reference files:

- `star-vs-snowflake.md` — star / snowflake / galaxy and when each; the three fact-table types; additivity of measures; degenerate dimensions; One Big Table.
- `dimensions-and-scd.md` — dimension roles (conformed, role-playing, degenerate, junk), SCD Types 1/2/3 with the Type 2 mechanics (surrogate key, effective dates, current flag), the date dimension, late-arriving data.

---

## Output

**1. In chat, a design summary:**

```
Business process:   <the process this fact table measures>
Grain:              <one fact row = exactly this — one sentence>
Fact table(s):      <name(s) and type: transaction | periodic snapshot | accumulating snapshot>
Measures:           <each measure + additive | semi-additive (over which dims it isn't) | non-additive>
Dimensions:         <list; mark conformed / role-playing (as X, as Y) / degenerate / junk>
Schema shape:       <star | snowflake (which dims, why) | galaxy (shared conformed dims)>
SCD strategy:       <per dimension: Type 1 | Type 2 (effective dates + current flag) | Type 3>
Keys:              <surrogate keys on all dimensions; business/natural keys retained>
Rollups:           <pre-aggregated tables / materialized views for which heavy reports, refreshed how>
Load plan:         <source, ELT/ETL, cadence, how Type 2 changes and late data are handled>
Tradeoffs accepted: <2–4 concrete costs: storage from denormalization, Type 2 fact-key churn, refresh lag, grain lock-in>
Not chosen because: <one line per rejected shape / approach>
```

**2. A dimensional ERD and table specs**, written to `docs/data-model/analytics/<slug>.md` (create the directory if absent). Fact table in the centre; every dimension with its attributes, surrogate key, business key, hierarchy levels, and SCD type; the explicit grain statement at the top.

Then stop. The ETL/ELT implementation is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely done the dimensional design — process chosen, grain declared, dimensions and SCD types decided — and wants a review or a tie-break rather than a walk through the framework, they say so and you give a direct assessment. Opt-in, not a default.

---

## Example invocations

> "We've got the warehouse (BigQuery, owned by the data team). I need to model support-ticket analytics. Process: a ticket moving through states. Grain: one row per ticket state-change. Questions: median time-in-state by team by week, reopen rate by product area by month, first-response SLA attainment by agent. Slice by: date, agent, team, product area, priority, channel. Agents change teams and product areas get renamed — we report historically, so we need to see who owned it *then*. Source is the app Postgres via nightly export; daily is fine. ~2M state-changes/year."

Gate satisfied. Framework: this is a **ticket state-change transaction fact** (grain = one state-change), plus arguably an **accumulating snapshot** fact per ticket for the SLA milestones. Dimensions: date (role-playing: changed_date, opened_date), agent (SCD Type 2 — team changes must be historical), team, product area (SCD Type 2 — renames), priority, channel (junk candidate with priority). Star shape, conformed date/agent dimensions. Daily batch load, Type 2 handling on agent and product-area. Rollup for the by-week/by-month medians. Write `docs/data-model/analytics/support-ticket-analytics.md`.

> "Design our reporting database."

Gate not satisfied — process, grain, questions, dimensions, history, refresh, target all missing. Response: name what's missing, ask for it, stop. Do not draw a star schema to react to.

> "One of our dashboard queries is slow, should we build a data warehouse?"

Probably the wrong skill. One slow query is a rollup table or an indexed view (`relational-modeling`) or a read replica (`data-tier-operations`), not a warehouse. Ask how many recurring reports, how many teams, and whether historical/as-of analysis is needed before treating this as a dimensional-modeling problem.

---

## Portability

Repo-agnostic. Reads the source schema and `docs/architecture/decisions/` for any warehouse ADR; writes `docs/data-model/analytics/`. Copy the `dimensional-modeling/` directory into another repo's `.claude/skills/` to use it there.
