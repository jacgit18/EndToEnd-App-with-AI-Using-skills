# dimensional-modeling skill

The analytical (OLAP) counterpart to `relational-modeling`. Where that skill designs a
normalized transactional store, this one designs the denormalized star: fact-table grain,
dimensions, SCD strategy, schema shape, rollups, load plan.

Built from the `Architecture/02. Backing Service Options/Databases/` notes — Data Warehouse,
Data Mart, Data Mart vs Data Warehouse, Star Schema, Snowflake Schema, Fact Table, Dimension
Table, Data Grain, Choosing Schema, plus Materialized Views for the rollup layer.

## Where it sits

```
database-architecture   →  WHERE the schema lives + WHICH store            (ADR)
relational-modeling      →  designs the OLTP tables (normalized)
data-tier-operations     →  scales / distributes an existing store          (ADR)
dimensional-modeling     →  designs the OLAP model (star / dimensions / SCD)  ← this skill
```

`relational-modeling` and `dimensional-modeling` are siblings with opposite defaults —
normalize for integrity vs denormalize for query speed. The routing question: is the need
**recurring analytical reporting over history, sliced many ways** (here), or a slow query /
lifecycle concern on the app database (`relational-modeling` for a rollup/view,
`data-tier-operations` for a replica)?

## The shape

A gate skill. It refuses to draw fact/dimension tables until the user supplies:

- **the business process** being measured (verb-ish, one per fact table)
- **the grain** — one fact row represents exactly what (the load-bearing, near-irreversible decision)
- **the actual questions** the business asks (a real report list)
- **the dimensions** they slice by
- **history needs** per dimension (SCD Type 1 vs 2)
- **source & refresh cadence**, and **scale & target** (warehouse / mart / reporting tables)

Then it walks Kimball's four steps (process → grain → dimensions → facts) plus schema shape,
SCD map, fact-table type, rollups, and a load plan.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The gate, challenge-the-framing, output contract. |
| `modeling-framework.md` | The 11-step process, worked once the gate is satisfied. |
| `star-vs-snowflake.md` | Star / snowflake / galaxy and when each; the three fact-table types; measure additivity; degenerate & factless facts; One Big Table. |
| `dimensions-and-scd.md` | Dimension roles (conformed, role-playing, degenerate, junk, outrigger); the date dimension; surrogate keys; SCD Types 0–6 with Type 2 mechanics; late-arriving data; bridge tables. |

## Output

1. A design summary in chat (process, grain, fact tables + type, measures + additivity,
   dimensions + roles, schema shape, SCD strategy, keys, rollups, load plan, tradeoffs).
2. A dimensional ERD + table specs written to `docs/data-model/analytics/<slug>.md`, with the
   explicit grain statement at the top.

Stops before ETL/ELT implementation.

## Deliberately out of scope

- OLTP table design → `relational-modeling`.
- Warehouse technology / ownership / source-of-truth → `database-architecture`.
- Scaling an existing warehouse (dist keys, sort keys, cluster sizing) → `data-tier-operations`;
  the warehouse bill → `technical-cost-decision`.
- The ETL/ELT pipeline code and orchestration (dbt/Airflow/Dagster/CDC) — the skill produces a
  *load plan*, not the implementation.
- BI tool / dashboard design; ML feature stores.

## Interaction with sibling skills

- **Sibling to `relational-modeling`** — opposite defaults, split on OLAP-vs-OLTP. The
  "one slow dashboard query → build a warehouse?" case routes *out* of this skill.
- **Chains from `database-architecture`** when the warehouse is a separate system needing its
  own paradigm/ownership decision.
- **Chains to `technical-cost-decision`** for warehouse compute/storage cost.
- **`learning-gate`** hands off to this skill on dimensional-modeling questions rather than
  running its own rep gate (see `learning-gate` Step 3).

Run `skill-interaction-testing` after any trigger-description change here — overlap risk is with
`relational-modeling` ("how do I model X for reporting") and `database-architecture`
("where should the warehouse live").

## Using it in another repo

Repo-agnostic. Reads the source schema and `docs/architecture/decisions/`; writes
`docs/data-model/analytics/`.

```
cp -r .claude/skills/dimensional-modeling /path/to/other-repo/.claude/skills/
```
