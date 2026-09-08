# caching-strategy skill

The fifth skill in the database family, and the second "operations" skill alongside
`data-tier-operations`. `database-architecture` decides where the source of truth lives and
which store; `relational-modeling` / `dimensional-modeling` design the tables;
`data-tier-operations` scales and distributes the store itself; this one decides whether a
**cache** belongs in front of a read path, and if so how it stays correct.

Built from the `Architecture/Library/Memory/` notes — `Caches.md` (cache types, strategies,
policies, SPOF) and `Content Delivery Network.md` — plus the caching step that
`data-tier-operations` deliberately defers.

## Where it sits

```
database-architecture   →  WHERE the schema lives + WHICH store            (ADR)
relational-modeling      →  designs the tables for a relational store
dimensional-modeling     →  star / snowflake / fact / dimension / warehouse
data-tier-operations     →  scales / distributes an existing store          (ADR)
caching-strategy         →  cache layer + pattern + freshness + eviction    (ADR)  ← this skill
```

## The shape

A gate skill, like the rest of the family. It refuses to recommend a cache until the user
supplies:

- **a measured pressure** — a latency miss, a source-load number, or a downstream limit/cost;
  never "make it faster" or "add Redis for scale"
- **current numbers** — read QPS on the path, p95/p99 vs target, payload size, source load
  attributable to the reads, rough key cardinality
- **change rate + writer set, per data class** — how often it changes and whether external
  systems also write it
- **staleness tolerance, per data class** — the acceptable age of a served value and the
  concrete cost of serving stale
- **optimization vs load-bearing** — does the source survive a 100% miss; this sets the HA bar

Then it makes the user rule out the non-cache fixes first (index, replica, pagination,
denormalization, HTTP headers), because a cache is a permanent consistency cost traded for a
latency win.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The gate, challenge-the-proposal, output contract. |
| `caching-framework.md` | The 10-step process, worked once the gate is satisfied. |
| `cache-placement.md` | The layers from client to DB — client/HTTP, CDN/edge, reverse proxy, in-process, distributed (Redis/Memcached), DB query cache — what each solves, costs, and how invalidation works there. |
| `patterns-and-policies.md` | Read/write patterns (cache-aside / read-through / write-through / write-behind / refresh-ahead), invalidation vs TTL vs versioned keys, eviction policies (LRU/LFU/TinyLFU/FIFO), sizing, and the failure modes (stampede / penetration / avalanche / cache-down) with mitigations. |

## Output

1. A recommendation block in chat (pressure, cheaper options ruled out, data + staleness class,
   placement, read/write pattern, freshness mechanism, eviction/size, failure handling, HA
   posture, metrics, tradeoffs, cost follow-up).
2. On approval: an ADR in `docs/architecture/decisions/` reusing `database-architecture`'s
   `adr-template.md` — same directory and numbering. The "Revisit when" line must be a concrete
   threshold (hit-rate floor, change-rate ceiling, "source can serve this uncached").

Stops before implementation (cache client wiring, invalidation hooks, warmup job).

## Interaction with sibling skills

- **Chains from `data-tier-operations`** — that skill lists caching among the cheaper options it
  exhausts before partitioning/sharding, and hands the actual caching design here. This skill,
  in turn, bounces a "load-bearing cache" case back to `data-tier-operations` when the real
  problem is source capacity.
- **Chains to `technical-cost-decision`** — the cache tier and CDN have a recurring price (Redis
  instance-hours, memory tier, cross-AZ transfer, CDN requests/egress); the recommendation block
  hands off the line items.
- **Defers to `relational-modeling` / `problem-solving-gates`** for query and index tuning of one
  slow query — framework step 1 sends you there first, because a cache over a missing index
  hides the bug.
- **Defers to `database-architecture`** for source-of-truth and store choice; caching presumes
  those are settled.
- **Defers to `api-interface-style`** for whether a surface should push vs be polled and the wire
  protocol; `Cache-Control` / `ETag` on an existing surface is in scope here as a placement
  option, redesigning the surface is not.
- **`learning-gate`** should hand off to this skill on caching-design questions rather than
  running its own rep gate (see `learning-gate` Step 3 — Database design row).

Run `skill-interaction-testing` after any trigger-description change here — the overlap risk is
with `data-tier-operations` (read-scaling questions), `technical-cost-decision` (volume-stated
system questions), and `api-interface-style` (HTTP caching on an API surface).

## Using it in another repo

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside `database-architecture`
and `data-tier-operations`, reusing `database-architecture`'s `adr-template.md`.

```
cp -r .claude/skills/Data/caching-strategy /path/to/other-repo/.claude/skills/Data/
```
