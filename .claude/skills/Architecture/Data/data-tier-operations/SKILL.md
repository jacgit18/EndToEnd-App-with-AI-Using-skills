---
name: data-tier-operations
description: A gated decision process for scaling and distributing an existing database — read replicas and replication topology (single-leader / multi-leader / leaderless), table partitioning vs sharding and the shard-key choice, transaction isolation level, distributed-transaction pattern (2PC / Saga / outbox / eventual), failover and RPO/RTO, and connection pooling. Use this skill when someone says "we need to shard", "the database is the bottleneck", "should we add read replicas", "which isolation level", "how do we handle transactions across services/shards", "we need multi-region writes", "which distribution / sort key" or "the warehouse queries are slow" (physical tuning of an analytical store — the dimensional model itself is `dimensional-modeling`), or proposes a topology and wants it checked. It forces the pressure (a measured bottleneck or a hard requirement — not "web scale someday"), the current numbers, and the per-operation consistency needs to be stated by the user before any topology is recommended, then records the outcome as an ADR. It exists to stop distribution being adopted prematurely (the shard key is near-irreversible) or the wrong consistency model being discovered in production. Not for whether the alerting or metrics on replica lag / failover are any good — that is `observability-strategy`. Not for executing a live move to the new topology (backfill + cutover + rollback window) — that is `migration-cutover`, which this skill hands the move to once the target topology is chosen. Not for app-level overload protection in front of the store (a concurrency limit so the service sheds before the connection pool drains, circuit breakers on DB calls) — that is `resilience-strategy`, which leads when the reported symptom is requests timing out or a cascade under load, and complements the pooler here. Not for a poll-based consumer (Lambda on DynamoDB Streams or Kinesis) stuck on one bad record — that is `serverless-execution-model`'s consumer-side retry/skip/redrive contract; this skill only leads once failures trace to a genuinely hot partition/shard key concentrating traffic, not a one-off poison-pill record. Not for whether a database credential should rotate at all, or where it's stored — that is `config-and-secrets-management`; this skill only owns the datastore-side mechanics (e.g., RDS-managed rotation, connection-pool behavior during a rotation) once that decision is made.
---

# Data-Tier Operations

Take an existing database that is hitting — or is credibly about to hit — a wall, and decide how it scales and distributes: replicas, partitioning, sharding, isolation, distributed transactions, failover. The skill makes the user prove there is a real pressure and produce real numbers before any topology is on the table, recommends one path with the cheaper options exhausted first, and writes an ADR.

## When to use

- The user reports a **bottleneck** — the database is slow, at capacity, running out of disk, or maxing connections — and wants to scale it.
- The user asks for a **topology**: read replicas, master-slave / primary-replica, multi-leader, leaderless, sharding, table partitioning.
- The user asks about **consistency or concurrency at scale**: isolation level, lock contention, `SELECT FOR UPDATE`, read-your-writes on replicas.
- The user needs **transactions across a boundary** — multiple shards, or multiple services with their own databases — and asks about 2PC / Saga / outbox / eventual consistency.
- The user proposes a distribution plan and wants it pressure-tested ("we're going to shard by customer_id").
- The user asks about **failover, replication lag, backups, RPO/RTO**, or **connection pooling / pooler placement**.

## Out of scope — hand these off

- **Physical table and index design** — normalization, key strategy, constraint placement, the first-cut index list → `relational-modeling`. **Tuning or auditing the index set on a deployed, populated schema** — composite column order against a real `EXPLAIN` plan, covering/partial-index trade-offs, redundant/unused-index cleanup, the write-cost budget → `index-tuning`. Finding *whether* a slow query is even the bottleneck → `problem-solving-gates` (Rubber Duck to find the cause, or Optimization if a query plan / profile is in hand). Those are often the *actual* fix and this skill will send you there first (framework step 2).
- **Where the source of truth lives** (database-first / code-first / contract-first) and **which database paradigm** (SQL vs NoSQL vs graph vs time-series) → `database-architecture`. If that isn't settled, distribution is premature.
- **Projected numbers for a store that does not exist yet** — turning "we expect ~500k reads/sec" or "~2M DAU" into write QPS, per-node capacity, storage growth, and what binds first → `capacity-estimation`. This skill needs *measured* current numbers (gate item 5); for a not-yet-built store it consumes that skill's a-priori estimate and then picks the topology.
- **Whether to split the system into services** → `microservices-decision`. This skill handles data across services *once the services exist*; it does not decide that they should.
- **The dollar cost** of a topology (replica instance-hours, cross-AZ transfer, managed-service premium) → `technical-cost-decision`. This skill names that a topology has a cost and chains to that skill for the number.
- **The design of a cache in front of the store** — which layer, cache-aside vs write-through, TTL vs explicit invalidation, eviction policy, stampede handling → `caching-strategy`. This skill names caching as one of the cheaper options to try before partitioning (framework step 2) and hands the design there.
- **Executing a live move to a new topology** — when the chosen target requires copying a running store and flipping traffic (a re-key, a new shard layout on live data, an engine change) → `migration-cutover`. This skill picks the *target topology*; that skill runs the backfill / dual-write / verification / rollback of getting there.
- **App-level overload protection in front of the store** — a concurrency or admission limit so the service sheds load before the DB connection pool is exhausted, circuit breakers and timeouts on DB calls, bulkheading tier-1 queries → `resilience-strategy`. This skill's pooler (framework step 2 / step 7) and that skill's upstream limit are complementary, not alternatives.
- **Implementation** — replication config, shard router code, migration/backfill scripts. The skill stops at the ADR.

---

## The gate

Before recommending any topology, isolation level, or transaction pattern, these must be answered.

**Facts you may surface from the repo / infra** (state them for confirmation):

1. **Current database** — technology and version.
2. **Current topology** — single node, or already has replicas / partitions / shards.
3. **Hosting** — managed service (RDS, Cloud SQL, Atlas, …) or self-operated.

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not model without them. If any is missing, name it and stop:

4. **The pressure** — what is *actually* forcing this, concretely. One of: a measured bottleneck (which metric, what value, since when), a hard near-term scale requirement (a stated volume — rows, QPS, users, GB), an availability target (an uptime SLA / RTO), or a compliance/geo requirement (data residency, regional latency). "We want to scale", "be ready for growth", "web-scale" is **not** a pressure — it is a reason to stop.
5. **Current numbers** — measured, not guessed: data size and largest table, read QPS and write QPS, p95 query latency, connection count vs limit, growth rate. If the user doesn't have these, the first task is to get them, not to pick a topology.
6. **Read/write shape** — the ratio, and whether reads can tolerate staleness: can a given read be served by a replica that is seconds (or more) behind the primary, or must it see the latest write.
7. **Consistency needs, per operation** — which writes need read-your-writes or strong consistency (money, inventory, auth), and which operations tolerate eventual consistency. Not a global answer — a per-workload one.
8. **Failure tolerance** — RPO (how much recently-written data may be lost in a failure) and RTO (how long the tier may be unavailable). A number or a range, not "none" — "none" is not achievable and forces the conversation.
9. **Operational capacity** — who operates this, and can the team run the thing being proposed. A self-hosted sharded cluster with manual failover is a staffing decision.

"The DB is slow, make it scale" with items 4–9 absent is not valid input.

**Pressure does not open the gate.** "We're launching in two weeks", "the CTO already said we're sharding", "just tell me the shard key" are reasons the user wants the gate skipped. Under real time pressure the fastest correct move is still items 4–9 in one sentence each, because the wrong shard key is a months-long migration.

---

## Challenge a proposed approach

If the user opens with the topology already chosen, put their reasoning under the gate, then test the specific claim against `scaling-topologies.md` / `consistency-and-transactions.md`:

- **"we need to shard"** — what is the measured bottleneck (item 5)? Have you exhausted vertical scaling, query/index tuning, caching, and read replicas (framework step 2)? What is the shard key, and does it keep your top 3 queries single-shard? How do you avoid a hotspot? What is the resharding plan when the key stops working?
- **"we need multi-leader / multi-master"** — do you have genuine concurrent writes in multiple regions, or is one primary with read replicas enough? How are write-write conflicts resolved, and is that acceptable for this data?
- **"leaderless / Dynamo-style"** — are you accepting eventual consistency for *all* of this data? Which operations in item 7 does that break?
- **"Serializable everywhere"** — which specific transactions have the anomaly you're protecting against (write skew, phantom)? What is the throughput and retry cost at that level? Would `REPEATABLE READ` plus a targeted `SELECT FOR UPDATE` do it?
- **"each microservice has its own DB, so we need 2PC"** — do you need cross-service *atomicity*, or is eventual consistency with a Saga / transactional outbox acceptable? 2PC couples availability across all participants — is that the trade you mean to make?
- **"add read replicas"** (the usually-right one) — which reads move to the replica, and do all of them tolerate replication lag? What happens to a read-your-writes flow that lands on a lagging replica?

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `operations-framework.md` in order once the gate is satisfied. In short: confirm the pressure is real → exhaust the cheaper options (vertical, tuning, caching, pooling, replicas) before partitioning → if reads are the wall, pick a replication topology from the consistency and geo needs → if writes/size are the wall, partition then shard, and choose the shard key against the access patterns → set isolation per workload and a distributed-transaction pattern for cross-boundary writes → design failover and backups to the RPO/RTO → place the connection pooler → recommend and record.

Reference files:

- `scaling-topologies.md` — vertical vs horizontal, read replicas, replication topologies (single-leader / multi-leader / leaderless) and what each costs, table partitioning vs sharding, shard-key selection and hotspots, sharding's interaction with pagination and joins.
- `consistency-and-transactions.md` — isolation levels and the anomalies each prevents, optimistic vs pessimistic locking, distributed-transaction patterns (2PC, Saga, transactional outbox, eventual), replication lag and read-your-writes, connection pooling.

---

## Output

**1. In chat, a recommendation block:**

```
Pressure:            <the measured bottleneck or hard requirement from gate item 4>
Cheaper options:     <vertical / tuning / caching / pooling / replicas — which were ruled out and why>
Scaling move:        <read replicas | table partitioning | sharding | none yet>
Replication topology: <single-leader | multi-leader | leaderless | n/a> — <why>
Shard key:           <the key + why it keeps hot queries single-shard, or "n/a">
Isolation:           <level per workload, e.g. "Read Committed default; SELECT FOR UPDATE on the ledger write">
Cross-boundary writes: <2PC | Saga | outbox | eventual | none> — <why>
Failover / backups:  <automatic promotion? backup cadence? — meeting RPO <x> / RTO <y>>
Connection pooling:  <pooler + placement>
Tradeoffs accepted:  <2–4 concrete costs: operational load, lag windows, resharding debt, lost cross-entity atomicity>
Not chosen because:  <one line per rejected topology>
Cost follow-up:      <hand to technical-cost-decision: which line items to price>
```

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `database-architecture`'s `adr-template.md` (same directory and numbering — this is an architecture decision). If `database-architecture` produced a persistence/source-of-truth ADR, reference it. Fill the "Revisit when" section with the concrete trigger that reopens this — "write QPS on the primary passes X", "replication lag p95 exceeds the read-your-writes budget", "the shard key stops keeping query Y single-shard".

Then stop. Implementation is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked this — numbers gathered, cheaper options ruled out with reasons, a topology chosen against stated consistency needs — and wants a review or a tie-break rather than a Socratic pass, they say so and you give a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "Postgres on RDS, single instance. Primary is at 80% CPU sustained, p95 read latency has gone from 20ms to 300ms over two months, ~95% of queries are reads, write QPS is ~40. Most reads are 'load this dashboard' and can be a few seconds stale; the exception is the billing pages, which must read-your-writes. We can lose ~5s of data in a failover, need to be back within a minute. Small team, staying on RDS. We think we need to shard."

Gate satisfied. Framework: this is a **read** bottleneck with staleness-tolerant reads — sharding is the wrong tool. Recommend one or two RDS read replicas, route dashboards to replicas, keep billing on the primary (or route it to the primary explicitly for read-your-writes), single-leader topology, RDS Multi-AZ for the RPO/RTO, PgBouncer in transaction mode. Tradeoffs: replica lag window on dashboards, cost of replica instances (→ `technical-cost-decision`). Not sharding: no write or data-size pressure, and it would add a shard key and a router for a problem replicas solve. Write the ADR; Revisit when write QPS or data size becomes the wall.

> "We need to make the database scalable before launch."

Gate not satisfied — item 4 (no pressure, "before launch" is not a bottleneck) and item 5 (no numbers). Response: name what's missing, explain that the cheapest scale is the one not built, and ask for a measured pressure or a hard volume requirement. Do not recommend a topology.

---

## Portability

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside `database-architecture`, reusing its `adr-template.md`. Copy the `data-tier-operations/` directory into another repo's `.claude/skills/` to use it there.
