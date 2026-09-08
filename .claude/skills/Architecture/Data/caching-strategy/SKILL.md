---
name: caching-strategy
description: A gated decision process for introducing or changing a cache in front of a data source — where the cache sits (client / HTTP / CDN / reverse-proxy / in-process / distributed Redis-Memcached / database query cache), the read/write pattern (cache-aside, read-through, write-through, write-behind, refresh-ahead), the freshness mechanism (explicit invalidation vs TTL vs both), the eviction policy and sizing (LRU / LFU / TinyLFU / FIFO), and the failure-mode handling (stampede, penetration, avalanche, cache-down). Use this skill when someone says "we should add a cache", "let's put Redis in front of X", "the product page is slow, cache it", "what TTL should we use", "cache-aside or write-through", "our cache keeps serving stale data", "how do we stop the thundering herd when a hot key expires", "should we cache at the CDN", or proposes a caching approach and wants it checked. It forces the user to state the measured pressure, the current numbers, the per-data-class staleness tolerance, and whether the cache is an optimization or load-bearing, before any cache layer or pattern is recommended, then records the outcome as an ADR. It exists to stop a cache being added to paper over a missing index, and to stop the wrong consistency window being discovered in production. Not for scaling the database itself — replicas, partitioning, sharding, isolation levels — that is `data-tier-operations` (which walks past caching as one of its cheaper options and hands the decision here). Not for the dollar sizing of the cache tier or CDN egress — that is `technical-cost-decision`. Not for query or index tuning of one slow query — that is `index-tuning` (revising/adding/auditing indexes on a deployed, populated schema), `relational-modeling` (schema-design-time index/key choice), or `problem-solving-gates` (Rubber Duck to find the cause, or Optimization if a profile / query plan is already in hand). Not for whether the hit-rate (or any cache) metric is correctly measured or alerted — that is `observability-strategy`. Not for whether an API pushes or is polled — that is `api-interface-style`. Not for request-path overload protection — rate limiting, load shedding, circuit breakers on the calls a cache miss falls through to — that is `resilience-strategy`, for which "serve a stale / cached response" is one degradation fallback whose cache this skill designs.
---

# Caching Strategy

Take a read path that is slow, expensive, or overloading its source, and decide whether a cache belongs there — and if so, which layer, which read/write pattern, how entries stay fresh, how they get evicted, and what happens when the cache is cold or down. The skill makes the user prove the pressure is real and the cheaper fixes are exhausted before any cache is on the table, because a cache is a permanent consistency problem traded for a latency win, recommends one design, and writes an ADR.

## When to use

- The user reports a **slow or expensive read path** — a page/endpoint is over its latency budget, a downstream API is rate-limited or billed per call, the database is CPU-bound on repeated reads — and wants to cache it.
- The user asks to **add a cache**: "put Redis in front of it", "add an application cache", "cache this at the edge / CDN", "in-process cache".
- The user asks about a **caching parameter**: which TTL, which eviction policy, cache-aside vs read-through vs write-through vs write-behind, key granularity (whole response vs query result vs object).
- The user reports a **cache defect**: stale reads, low hit rate, a stampede when a hot key expires, the cache filling with one-hit keys, an origin outage when the cache went cold.
- The user proposes a caching design and wants it pressure-tested ("we'll write-through so it's always consistent").

## Out of scope — hand these off

- **Scaling the data tier itself** — read replicas, partitioning, sharding, shard-key choice, isolation levels, distributed transactions, failover → `data-tier-operations`. That skill lists caching among the cheaper options it exhausts before partitioning; it defers the actual caching design here.
- **Query-level and index tuning** of one slow query — the missing index, the N+1, the unbounded scan → `index-tuning` (revising/adding/auditing indexes on a deployed, populated schema — composite column order against a real `EXPLAIN` plan, covering/partial-index trade-offs, redundant/unused-index audit, write-cost budget), `relational-modeling` (index/key design at schema-design time), or `problem-solving-gates` (Rubber Duck to find the cause; Optimization mode once a profile or `EXPLAIN` plan identifies the hot spot). This is frequently the *real* fix and framework step 1 sends you there first.
- **Where the source of truth lives** and **which store** → `database-architecture`. Caching presumes an authoritative source already chosen.
- **The dollar cost** of the cache tier — Redis/ElastiCache instance-hours, memory tier, cross-AZ transfer, CDN request and egress pricing → `technical-cost-decision`. This skill names that the design has a recurring price and hands off the line items.
- **Whether an API should push instead of being polled**, and the wire protocol / interaction model → `api-interface-style`. HTTP `Cache-Control` / `ETag` on an existing surface is in scope here as a placement option; redesigning the surface is not.
- **Request-path overload protection** — rate limiting, priority-aware load shedding, circuit breakers, retry budgets, bulkheads on the path a cache miss falls through to → `resilience-strategy`. Cache-specific overload (stampede / penetration / avalanche on a hot key) stays here; "fall back to a stale or cached response when a dependency is down" is a `resilience-strategy` degradation choice whose cache design it hands back here.
- **Implementation** — the cache client wiring, the invalidation hooks, the warmup job. The skill stops at the ADR.

---

## The gate

Before recommending any cache layer, pattern, TTL, or eviction policy, these must be answered.

**Facts you may surface from the repo / infra** (state them for confirmation):

1. **The read path** — the query or call being considered, and what it returns.
2. **Existing caching** — HTTP headers, CDN, any in-process or shared cache already in the path.
3. **The source** — database (which, managed or self-run), an internal service, or a third-party API.
4. **Hosting** — is there already a Redis/Memcached/ElastiCache tier, or would this add one.

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not design without them. If any is missing, name it and stop:

5. **The pressure** — what is *actually* forcing this, concretely. One of: a measured latency miss (which path, p95/p99 now vs target), a measured source load (DB CPU / connections driven by these reads, since when), a downstream limit or cost (rate cap, per-call price × volume), or a read volume that replicas/vertical scaling can't meet economically. "Make it faster", "add Redis for scale", "everyone caches this" is **not** a pressure — it is a reason to stop.
6. **Current numbers** — measured, not guessed: read QPS on this path, current p95/p99 latency and the target, the payload size, how much of the source's load is attributable to these reads, and a rough count of distinct keys / working-set size.
7. **Change rate and writer set, per data class** — how often the underlying data changes, and *who* changes it: only this application, or other services / external systems / batch jobs / direct DB edits. A value only this app writes is a different problem from one an external feed updates.
8. **Staleness tolerance, per data class** — for each thing being cached: how old may a served value be — seconds, minutes, hours, until explicitly changed — and what breaks if a stale value is served (cosmetic lag vs wrong price vs stale permissions). Not one global answer — a per-workload one.
9. **Read-your-writes** — which writes must be visible immediately to the user who made them (and/or globally), and which may propagate lazily via TTL.
10. **Optimization or load-bearing** — if the cache is empty or down and 100% of traffic hits the source, does the source survive? If yes, the cache is an optimization and a single node is acceptable. If no, the cache is a dependency and needs the HA treatment — replication, failover, cold-start protection. The user must say which.
11. **Operational capacity** — who runs this cache tier, watches hit rate and eviction rate, and handles its failover.

"This endpoint is slow, put a cache on it" with items 5–11 absent is not valid input.

**Pressure does not open the gate.** "We launch in two weeks", "the design doc already says Redis", "just tell me the TTL" are reasons the user wants the gate skipped. Under real time pressure the fastest correct move is still items 5–11 in one sentence each, because a cache added without a staleness budget or an invalidation plan becomes a stale-data incident later.

---

## Challenge a proposed approach

If the user opens with the cache already chosen, put their reasoning under the gate, then test the specific claim against `cache-placement.md` / `patterns-and-policies.md`:

- **"add Redis / add a cache"** — which read path (item 5), what is its measured latency and the source load it drives (item 6), what is the staleness budget (item 8), and what invalidates an entry on write (item 7)? Has the missing index / replica / pagination been ruled out (framework step 1)?
- **"write-through so it's always consistent"** — write-through still serves stale when *another* writer changes the row, and it adds latency to every write. Do you have external writers (item 7)? Is the write-latency cost acceptable? Would cache-aside plus a short TTL and an explicit invalidation meet the staleness budget instead?
- **"cache-aside everywhere"** (usually the right default) — how does an entry get invalidated when the underlying data changes, and how do you stop a stampede on the source when a hot key expires (framework step 7)?
- **"just set a long TTL"** — TTL is the only freshness mechanism here? What is the staleness cost when the row changes 30 seconds after it's cached (item 8)? Is there an explicit invalidation on write, or is a stale window equal to the full TTL acceptable for every field?
- **"cache the whole rendered response"** vs **"cache the query result / object"** — granularity trade: response caching has the highest hit-rate-per-byte but the widest invalidation fan-out (one row change busts every response containing it) and duplicates shared data across keys.
- **"LRU is fine"** — is the access pattern skewed to a few hot keys (LRU is fine) or scan-like / one-hit-heavy (LRU thrashes — consider LFU / TinyLFU, or negative caching for the one-hit keys)?
- **"the cache protects the database"** — then it is load-bearing (item 10). Is it replicated? Is there request coalescing so a cold start doesn't stampede the DB? Can the origin absorb the full load during a cache flush or deploy (avalanche)?
- **"cache it at the CDN"** — is the content actually cacheable: is it per-user, behind auth, or exploded across query-string permutations? How is it purged when it changes, and what is the purge propagation time?

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `caching-framework.md` in order once the gate is satisfied. In short: confirm the pressure is real and the non-cache fixes (index, replica, pagination, denormalization, HTTP headers) are exhausted → name the exact data and classify each by staleness tolerance and change source → pick the cache layer closest to the consumer that still meets the invalidation needs → pick the read/write pattern from the read:write ratio, write-latency budget, and external-writer set → set the freshness mechanism (explicit invalidation, TTL from the staleness budget, or both) and a key-namespacing scheme → set eviction policy and memory budget from the access-pattern skew → handle stampede / penetration / avalanche / cache-down explicitly → set the HA posture from optimization-vs-load-bearing → name the metrics and the revisit trigger → recommend and record.

Reference files:

- `cache-placement.md` — the layers from client to database (browser/HTTP, CDN/edge, reverse-proxy, in-process application, distributed application (Redis / Memcached), database query & buffer cache), what each one solves, what it costs, how invalidation works at that layer, and when in-process beats distributed.
- `patterns-and-policies.md` — read/write patterns (cache-aside, read-through, write-through, write-behind, refresh-ahead) and what each does to consistency and write latency; invalidation vs TTL vs versioned keys; eviction policies (LRU, LFU, TinyLFU, FIFO, random) and the access patterns each suits; sizing and `maxmemory` policy; the failure modes — stampede/dogpile, penetration, avalanche — and their mitigations; SPOF and HA for a load-bearing cache.

---

## Output

**1. In chat, a recommendation block:**

```
Pressure:            <measured latency miss / source load / downstream limit-cost from gate item 5>
Cheaper options:     <index / replica / pagination / denormalization / HTTP headers — which were ruled out and why>
Data cached:         <what it is> — staleness class: <seconds | minutes | until-changed>, changed by: <this app only | external writers>
Placement:           <client/HTTP | CDN | reverse-proxy | app in-process | app distributed (Redis/Memcached) | DB cache> — <why this layer>
Read/write pattern:  <cache-aside | read-through | write-through | write-behind | refresh-ahead> — <why>
Freshness:           <explicit invalidation on write | TTL = <value, from the staleness budget> | both>; key namespacing: <scheme for bulk invalidation>
Eviction / size:     <LRU | LFU | TinyLFU | FIFO>, memory budget <x + headroom>, maxmemory-policy <y>
Failure handling:    stampede: <lock / coalesce / early-recompute> | penetration: <negative cache / bloom> | avalanche: <TTL jitter / staggered warmup> | cache-down: <origin sized for it? fallback?>
HA posture:          <optimization → single node + hit-rate alarm | load-bearing → replicated, multi-node, failover>
Metrics:             <hit rate target, eviction rate, p99 with/without, origin load delta>
Tradeoffs accepted:  <2–4 concrete costs: stale window per data class, invalidation complexity, new operational tier, memory spend>
Not chosen because:  <one line per rejected placement / pattern>
Cost follow-up:      <hand to technical-cost-decision: cache instance-hours, memory tier, cross-AZ, CDN requests/egress>
```

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `database-architecture`'s `adr-template.md` (same directory and numbering — this is an architecture decision). If `database-architecture` or `data-tier-operations` produced a related ADR, reference it. Fill the "Revisit when" section with the concrete trigger that reopens this — "hit rate falls below X%", "the data's change rate makes any acceptable TTL a cache miss", "the origin can no longer absorb a cold-cache event", "read QPS on this path drops and the cache no longer pays for its operational cost".

Then stop. Implementation is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked this — numbers gathered, non-cache fixes ruled out with reasons, a layer and pattern chosen against a stated staleness budget and a stated optimization-vs-load-bearing call — and wants a review or a tie-break rather than a Socratic pass, they say so and you give a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "Product detail page. p99 is 900ms against a 300ms budget; the query is already indexed and hits a read replica. It's ~1,200 req/s, ~40k distinct products, the hot 2k are ~80% of traffic. Product data changes when merchandising edits it in the admin — a few hundred edits a day — and a stale price for up to a minute is fine, but a stale 'in stock / out of stock' flag for more than ~10s causes oversells. The DB is comfortably sized to serve this uncached if the cache is empty. Small team, already on ElastiCache. We're thinking Redis with a 5-minute TTL."

Gate satisfied. Framework: split the data class — price/description/images tolerate a minute (cache-aside in Redis, TTL 60s, plus explicit bust on the admin save), stock flag does not (either exclude it from the cached object and read it live, or cache it separately with a 5–10s TTL and bust on inventory events). 5-minute blanket TTL fails item 8 for stock. Placement: distributed (multi-instance web tier, 40k keys, shared invalidation) — in-process would fan the admin bust out across nodes. Eviction: `allkeys-lfu`, budget for the 40k working set with headroom. Stampede: per-key lock or `SETNX` recompute guard on the hot 2k. Cache-down: acceptable (origin sized — item 10), so single primary with a replica for failover, alarm on hit rate. Cost follow-up → `technical-cost-decision` for the node size. Write the ADR; Revisit when edit volume rises enough that bust traffic dominates, or hit rate drops below ~85%.

> "The API feels slow, we should add Redis before launch."

Gate not satisfied — item 5 (no measured pressure; "feels slow" and "before launch" are not a bottleneck), item 6 (no numbers), item 8 (no staleness budget). Response: name what's missing, note that a cache is a permanent consistency cost and the first move is to measure the path and rule out an index or a replica, and ask for a measured latency or source-load number and a per-field staleness tolerance. Do not recommend a cache.

---

## Portability

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside `database-architecture` and `data-tier-operations`, reusing `database-architecture`'s `adr-template.md`. Copy the `caching-strategy/` directory into another repo's `.claude/skills/` to use it there.
