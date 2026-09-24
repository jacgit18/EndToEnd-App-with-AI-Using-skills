# Scaling Topologies

Reference for steps 2–4 of `operations-framework.md`.

## Vertical vs horizontal

- **Vertical** (bigger instance) — no architectural change, no new failure modes, bounded by the largest instance available. Almost always the right *first* move and often buys a year. Its limits: a hard ceiling, and no redundancy — one box, one failure domain.
- **Horizontal** (more instances) — replicas, partitions, shards. Unbounded in principle, but every form adds operational surface: lag, failover, routing, cross-node queries. Earn it with a measured pressure.

## Read replicas

One primary takes writes; N replicas replicate from it and serve reads. The standard answer to a read bottleneck.

- **What it buys** — read throughput scales with replicas; a replica can be promoted on primary failure (redundancy).
- **What it costs** — **replication lag**: a replica is always some milliseconds-to-seconds behind. A read that must see a just-committed write (read-your-writes) cannot blindly hit a replica.
- **Routing** — send staleness-tolerant reads (dashboards, search, listings) to replicas; send read-your-writes flows (a user viewing what they just saved, billing, auth) to the primary, or gate them on a lag check / LSN comparison.
- **Not for** — write scaling or data-size problems. Replicas hold a full copy each; they don't reduce write load or per-node data size.

## Replication topologies

| Topology | Writes | Fits | Cost |
|---|---|---|---|
| **Single-leader** (primary + replicas; "master-slave", "primary-replica") | one node | Default. Writes fit on one node; reads scale out; read-your-writes can be routed to the primary | Replica lag; primary is the write ceiling and a failure point until promotion |
| **Multi-leader** (multi-master) | multiple nodes, often one per region | Genuine concurrent writes in multiple regions; offline-capable clients that sync | Write-write **conflict resolution** (last-write-wins loses data; CRDTs / app merge are complex). Don't use it for read scaling |
| **Leaderless** (quorum R/W; Dynamo, Cassandra) | any node | High availability and write throughput with staleness tolerance; a property of the datastore, not a bolt-on | Eventual consistency everywhere; read repair, hinted handoff, tuning R+Wquorums. Adopting it ≈ choosing a different database — loop in `database-architecture` |
| **Chain replication** | head of chain | Strong consistency + high throughput in specific systems | Latency proportional to chain length; niche |

## Table partitioning vs sharding

Both split a large table. The difference is whether it crosses machines.

| | Table partitioning | Sharding |
|---|---|---|
| Spans nodes | No — one server | Yes — many servers |
| Router needed | No | Yes (app-side or proxy) |
| Cross-piece joins / transactions | Normal, local | Hard or unavailable |
| Solves | One table too big to index / vacuum / scan efficiently | Write throughput or total data size exceeds one node |
| Reversible | Fairly | **Barely** — the shard key is a long migration to change |

**Always try partitioning before sharding.** Range partitioning by time (drop old partitions cheaply) or list partitioning by tenant handles a large fraction of "the table is too big" without distributing anything.

## Choosing a shard key

The near-irreversible decision. Against the access patterns from the gate:

- **Keeps the top queries single-shard.** Identify the 3 highest-volume queries. The shard key must be a predicate in all of them, so the router hits one shard. A query with no shard-key predicate fans out to every shard and merges — that's a scatter-gather, and too many of them erase the benefit.
- **No hotspot.**
  - Not monotonic — raw `created_at` or an auto-increment id sends every new write to the last shard. If you must shard by time, hash it or bucket it.
  - Not low-cardinality — `country` or `plan_tier` packs data unevenly and caps you at N shards.
  - Watch for a natural skew — one tenant that is 40% of the data will overload its shard regardless of key quality (needs its own shard or sub-partitioning).
- **Available at query time.** `tenant_id`, `user_id`, `account_id` — something the caller always has, so the router never guesses or looks up.
- **Partitioning function** — hash (even spread, no range scans), range (range scans work, hotspot risk), or directory/lookup (flexible, adds a lookup hop and its own scaling question).

**Resharding plan — write it now:**
- How a single shard that outgrows its node gets split (pre-hashing into more logical shards than physical nodes makes this a move, not a re-key).
- What happens if access patterns shift and the key stops keeping queries local.
- How a rebalance runs without downtime (dual-write + backfill + cutover).

## Sharding's downstream effects

- **Joins** — cross-shard joins are gone. Denormalize the joined column onto the sharded table, or join in the application. Feed this back to `relational-modeling`.
- **Pagination** — offset pagination across shards is broken (offset means nothing globally). Use **cursor / keyset pagination** on a stable sort key; the router queries each shard for `WHERE sort_key > cursor LIMIT n` and merge-sorts. Adding or splitting a shard must not scramble an in-flight paging session.
- **Unique constraints** — a `UNIQUE` that isn't the shard key isn't enforced globally. Either include the shard key in it, or accept application-level checking with a race window.
- **Aggregates** — `COUNT`, `SUM` across all data are scatter-gather; consider a rollup table maintained on write.
- **Referential integrity** — FKs don't cross shards; those invariants move to the application.
