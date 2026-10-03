# data-tier-operations skill

The third skill in the database family. `database-architecture` decides where the source of
truth lives and which store; `relational-modeling` designs the tables; this one scales and
distributes an existing store when it hits a wall.

Covers sharding and pagination, replication strategies (single-leader, leaderless),
distributed transactions and Saga (choreography vs orchestration, compensating transactions —
in `consistency-and-transactions.md`), locking, connection pooling, points of failure, and
hosting.

## Where it sits

```
database-architecture   →  WHERE the schema lives + WHICH store            (ADR)
relational-modeling      →  designs the tables for a relational store
data-tier-operations     →  scales / distributes an existing store          (ADR)  ← this skill
dimensional-modeling     →  star / snowflake / fact / dimension / warehouse
caching-strategy         →  cache layer + pattern + freshness + eviction    (ADR)
```

## The shape

A gate skill, like `database-architecture`. It refuses to recommend a topology until the user
supplies:

- **a real pressure** — a measured bottleneck or a hard requirement, never "scale someday"
- **current numbers** — data size, read/write QPS, p95 latency, connection headroom, growth
- **per-operation consistency needs** — which writes need read-your-writes, which tolerate lag
- **RPO / RTO** and **operational capacity**

Then it walks the cheaper options first (vertical, tuning, caching, pooling, replicas) and only
reaches sharding when writes or data size genuinely exceed one node — with the shard-key choice
treated as near-irreversible and requiring a written resharding plan.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The gate, challenge-the-proposal, output contract. |
| `operations-framework.md` | The 8-step process, worked once the gate is satisfied. |
| `scaling-topologies.md` | Vertical vs horizontal, read replicas, replication topologies, partitioning vs sharding, shard-key selection, sharding's effect on joins/pagination/uniqueness. |
| `consistency-and-transactions.md` | Isolation levels and their anomalies, optimistic vs pessimistic locking, distributed-transaction patterns (2PC / Saga / outbox / eventual), replication lag & read-your-writes, connection pooling. |

## Output

1. A recommendation block in chat (pressure, cheaper options ruled out, scaling move, topology,
   shard key, isolation per workload, cross-boundary write pattern, failover, pooling,
   tradeoffs, cost follow-up).
2. On approval: an ADR in `docs/architecture/decisions/` reusing `database-architecture`'s
   `adr-template.md` — same directory and numbering, because this is an architecture decision.
   The "Revisit when" line must be a concrete threshold.

Stops before implementation (replication config, shard router, backfill).

## Interaction with sibling skills

- **Chains from `database-architecture`** — the persistence/ownership ADR is context; if a store
  is shared across services, that shapes the distributed-transaction choice.
- **Chains to `technical-cost-decision`** — every topology has a recurring price (replica
  instance-hours, cross-AZ transfer, managed-proxy fees); the recommendation block hands off the
  line items to price.
- **Defers to `relational-modeling`** for key/denormalization work and the first-cut index list,
  and back to it when sharding forces denormalization.
- **Defers to `index-tuning`** for tuning or auditing the index set on a deployed, populated
  schema — composite column order against a real `EXPLAIN` plan, covering/partial-index
  trade-offs, redundant/unused-index cleanup, the write-cost budget (framework step 2 sends
  index-shaped query tuning there before any topology change).
- **Defers to `caching-strategy`** for the design of a cache in front of the store — framework
  step 2 lists caching as a cheaper option than partitioning and hands the layer/pattern/TTL/
  eviction decision there. `caching-strategy` bounces back here when a cache turns out to be
  load-bearing because the source lacks capacity.
- **Defers to `microservices-decision`** on whether services should exist; handles data *across*
  services only once they do.
- **Defers to `problem-solving-gates`** (Rubber Duck) for debugging one slow query.
- **`learning-gate`** hands off to this skill on scaling/distribution questions rather than
  running its own rep gate.
- **Hands off to `data-access-layer`** for how app code behaves under the chosen topology
  (read/write splitting in the ORM, pool config, retry on failover).

On a trigger-description change, the overlap risk is with `technical-cost-decision` (volume-stated system questions) and `microservices-decision`
(cross-service data).

## Dependencies

Needs no repo setup. Writes an ADR to `docs/architecture/decisions/` by default (use the
repo's own convention if it has one), in `database-architecture`'s ADR format; if that skill
isn't installed, `SKILL.md` carries an inline skeleton. Hands off to `database-architecture`,
`relational-modeling`, `index-tuning`, `caching-strategy`, `technical-cost-decision`,
`microservices-decision`, `resilience-strategy`, `problem-solving-gates`,
`data-access-layer`. If a named sibling isn't installed, `SKILL.md` says what to do inline.
