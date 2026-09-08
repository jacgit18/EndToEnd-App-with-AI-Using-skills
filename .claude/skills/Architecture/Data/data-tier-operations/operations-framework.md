# Operations Framework

Work these in order once the gate in `SKILL.md` is satisfied. Each step produces a written line; the collected lines become the ADR.

## 1. Confirm the pressure is real

Restate gate item 4 as one sentence: the specific metric and value, or the specific hard requirement. Then judge it:

- **Measured bottleneck** (CPU sustained high, latency climbing, disk filling, connections maxed) → proceed.
- **Hard near-term requirement** (a contracted volume, a launch with a known user count, a residency law) → proceed.
- **"Growth", "scale", "be ready", "web-scale", "the CTO said so"** → stop. State that the cheapest scaling is the scaling you don't build, that a premature shard key is a months-long migration to undo, and that the next step is a measured pressure or a hard number — not a topology.

If item 5 (numbers) is absent, the deliverable is "go measure these five things", not a recommendation.

## 2. Exhaust the cheaper options first

Distribution is the last resort, not the first. Walk these in order and record which are already done, which would help, and which are ruled out with a reason:

1. **Vertical scale** — is the instance near the top of its class? One size up buys time and zero architectural debt. Cheap first move unless already maxed.
2. **Query and index tuning** — is the bottleneck a handful of bad queries or missing/wrong indexes? Send to `index-tuning` (revise/add/audit indexes on the live schema against a real `EXPLAIN` plan and write profile) or `problem-solving-gates` (whether one slow query is even the bottleneck). A single missing or badly-ordered index has been mistaken for "we need to shard" many times.
3. **Caching** — are the hot reads cacheable (read-mostly, tolerate short staleness)? An application or edge cache in front of the DB removes read load without touching the tier. If this is the lever, hand the design (layer, pattern, TTL vs invalidation, eviction, stampede handling) to `caching-strategy`.
4. **Connection pooling** — if the wall is connection count, a pooler (PgBouncer, RDS Proxy) is the fix, not more database. See `consistency-and-transactions.md`.
5. **Read replicas** — if reads dominate and tolerate lag, replicas are the standard next step and far simpler than sharding. This is step 3 below.

Only when reads past replicas, or writes, or raw data size are the wall do you continue to partitioning.

## 3. If reads are the wall — replication topology

Reads exceed what one node (plus cache) can serve, and gate item 6 says they tolerate lag.

Pick the topology from `scaling-topologies.md` against gate items 6, 7, 8:

- **Single-leader (primary + read replicas)** — default. One node takes writes, replicas serve reads. Fits when writes fit on one node and you can route read-your-writes flows to the primary. Lowest complexity.
- **Multi-leader** — only for genuine concurrent writes in multiple regions or offline-capable clients. Buys write availability across regions at the cost of write-write conflict resolution. Do not choose it for read scaling.
- **Leaderless (quorum)** — a property of the datastore (Cassandra, Dynamo), not a bolt-on. Fits high-availability, write-heavy, staleness-tolerant workloads. Choosing it is usually choosing a different database — coordinate with `database-architecture`.

Record: which reads move to replicas, how read-your-writes flows are kept correct (route to primary, or a lag check), the expected lag window, and the failover behavior.

## 4. If writes or data size are the wall — partition, then shard

In order:

1. **Table partitioning (single node)** — split one huge table by range or list (time, tenant) on the same server. Keeps queries and transactions local, no router, no cross-node joins. Solves "one table is too big to index/vacuum/scan" without distributing. Try this first.
2. **Sharding (multiple nodes)** — only when write throughput or total data size genuinely exceeds one node.

If sharding: choose the **shard key** — the near-irreversible decision. From `scaling-topologies.md`:

- It must keep the **top 3 queries single-shard**. A query that must fan out to every shard loses most of sharding's benefit.
- It must **not create a hotspot** — no monotonic key (raw timestamp, auto-increment id) that routes all new writes to one shard; no low-cardinality key that packs tenants unevenly.
- Prefer a key the application always has at query time (tenant_id, user_id) so the router never has to guess.
- Write down the **resharding plan** — how you split a shard that outgrows its node, and how the key changes if access patterns change. "We'll figure it out later" is the answer that makes this a crisis later.

Record: the key, the partitioning function (hash / range / directory), how cross-shard queries and pagination are handled (`scaling-topologies.md` covers cursor-based pagination across shards), and what joins are lost.

## 5. Isolation and cross-boundary transactions

From `consistency-and-transactions.md`:

- **Isolation level, per workload** — not one global setting. Name the default (usually Read Committed) and the specific transactions that need more: `SELECT FOR UPDATE` on a balance decrement, `REPEATABLE READ` or `SERIALIZABLE` on a booking that has write skew. Note the throughput/retry cost of the stricter ones.
- **Cross-shard or cross-service writes** — pick one:
  - **None needed** — the write touches one shard / one service. Best case; confirm it's true.
  - **Transactional outbox + events** — the default for "update my data and tell others". Local transaction writes the row and an outbox record; a relay publishes the event; consumers converge. Eventual consistency, no distributed lock.
  - **Saga** — a sequence of local transactions with compensating actions on failure. For multi-step workflows (order → payment → shipment) that can tolerate visible intermediate states and need explicit rollback logic.
  - **2PC** — strong atomicity across participants, at the cost of coupling their availability (a slow or down participant blocks the commit). Only when a partial outcome is genuinely unacceptable and the participants are few and reliable.

Record the choice and the anomaly / failure it accepts.

## 6. Failure design

To gate item 8 (RPO / RTO):

- **Failover** — automatic promotion of a replica (managed services do this; self-hosted needs Patroni / repmgr / equivalent) vs manual. Manual failover rarely meets an RTO under a few minutes.
- **Replication mode** — asynchronous (some data loss on failover, lower write latency) vs synchronous (zero loss to the synchronous replica, higher write latency). Pick against the RPO.
- **Backups** — cadence and retention, and whether point-in-time recovery is on. Confirm a restore has actually been tested.
- **Multi-AZ / multi-region** — AZ redundancy for availability; region redundancy only if item 4 named a regional requirement.

## 7. Connection pooling

- A pooler (PgBouncer, RDS Proxy, pgcat) between app and database if connection count is or will be a constraint — serverless / many app instances make this near-mandatory.
- **Placement** — client-side, sidecar, or central. Central pooler is a single point of failure unless itself redundant.
- **Mode** — transaction pooling gives the best reuse but disallows session-level features (prepared statements caveats, `SET`, advisory locks held across statements). Note anything in the app that breaks under transaction mode.

## 8. Recommend and record

Produce the recommendation block from `SKILL.md`. On approval, write the ADR using `database-architecture`'s `adr-template.md` in `docs/architecture/decisions/`. The **Revisit when** line is the point of the document — make it a concrete threshold (a QPS number, a lag budget, a data-size ceiling, "the shard key stops keeping query Y local"), not "when it gets slow again".

Then stop. Configuring replication, writing the shard router, and running the backfill are a separate step.
