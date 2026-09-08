# Caching Framework

Work these in order once the gate in `SKILL.md` is satisfied. Each step produces a written line; the collected lines become the recommendation block and then the ADR.

## 1. Confirm the pressure is real — and that a cache is the right tool

Restate gate item 5 as one sentence: the specific metric and value, or the specific downstream limit. Then judge it:

- **Measured latency miss** (p95/p99 over budget on a named path), **measured source load** (DB CPU / connection pressure from these reads), or a **downstream cap / per-call cost** → proceed.
- **"Feels slow", "add Redis for scale", "everyone caches this", "before launch"** → stop. State that a cache is a permanent consistency cost bought for a latency win, and the next step is a measurement, not a cache.

Then rule out the non-cache fixes — record which are done, which would help, which are ruled out with a reason:

1. **Index / query fix** — is the source slow because of a missing index, an N+1, or an unbounded scan? Send to `relational-modeling` or `problem-solving-gates` (Rubber Duck). A cache over a missing index hides the bug and adds an invalidation problem.
2. **Read replica / vertical scale** — if the source is read-loaded and the reads tolerate small lag, a replica removes load with no application-level consistency logic. Often simpler than a cache. (That path is `data-tier-operations`.)
3. **Pagination / payload trim / projection** — is the path slow because it returns 10× the rows or columns the consumer uses?
4. **Denormalization / materialized view** — a maintained read model in the same store keeps the consistency story inside the database's transactions instead of in application code.
5. **HTTP caching headers** — if the consumer is a browser or a CDN and the resource is already cacheable, `Cache-Control` / `ETag` may be the whole answer (see step 3, client/CDN layer).

A cache is justified when the data is read far more than it's written, the source can't cheaply serve the read volume, and a bounded staleness window is acceptable (gate item 8).

## 2. Name the data and classify each piece

List exactly what would be cached. For each distinct data class, write:

- **Change rate and writer set** (gate item 7) — changes per hour/day, and whether only this application writes it or external systems / batch jobs / direct edits also do. External writers rule out patterns that assume the app sees every write (write-through, write-behind as a freshness mechanism).
- **Staleness tolerance** (gate item 8) — seconds / minutes / until-explicitly-changed — and the concrete failure of serving stale (cosmetic vs wrong money vs stale authz). Stale permissions or prices usually mean "until explicitly changed" with an active invalidation, not a TTL.
- **Read-your-writes need** (gate item 9) — must the writer see their own change immediately.

Different fields of the same object often fall in different classes — split them rather than caching the whole object at the strictest field's TTL.

## 3. Choose the cache layer — closest to the consumer that still meets invalidation needs

From `cache-placement.md`. Cheaper and faster the closer to the consumer; harder to invalidate the closer to the consumer.

- **Client / HTTP (`Cache-Control`, `ETag`, SWR)** — for per-consumer or public GET responses a browser or app repeats. Zero server cost on a hit. Invalidation is by TTL expiry only — you cannot reach into a client cache. Use only when a fixed max-age within the staleness budget is acceptable.
- **CDN / edge** — public, cacheable-by-URL content (assets, and HTML/JSON keyed only on path + a small vary set). Massive offload and geographic latency win. Invalidation is an explicit purge with a propagation delay (seconds to minutes). Not for per-user or auth-varying responses unless keyed carefully.
- **Reverse proxy (nginx / Varnish)** — a shared HTTP cache you *do* control, in front of the app. Good middle ground for public responses when you want purge control without a CDN.
- **In-process application cache** — a map / Caffeine / `lru-cache` in the service process. Nanosecond hits, no network, no extra tier. Costs: each instance has its own copy (N stale windows, N cold starts, invalidation must fan out to every instance), and it consumes heap. Best for small, hot, read-mostly reference data with a short TTL and few instances.
- **Distributed application cache (Redis / Memcached)** — one shared cache the whole fleet reads. One invalidation clears it for everyone; survives a single app instance. Costs a network hop (~0.2–1ms), a new operational tier, and memory spend. The default when there are multiple app instances and a shared invalidation story matters. Redis vs Memcached: Redis for data structures, persistence, pub/sub, and clustering; Memcached for a pure multithreaded LRU blob cache.
- **Database query / buffer cache** — already there; tuning `shared_buffers` / the query cache is free and touches nothing. Note it, but it's rarely the lever the user is asking about.

Record the layer per data class and why that layer (not the one closer to the consumer) is the closest that still lets you hit the staleness budget.

## 4. Choose the read/write pattern

From `patterns-and-policies.md`, against the read:write ratio, the write-latency budget, and the external-writer set:

- **Cache-aside (lazy)** — app checks cache, on miss reads source and populates. The default. Cache only holds what's been asked for; a miss is a slow path; you own invalidation on write. Works regardless of who else writes the source (they just make entries stale until TTL / invalidation).
- **Read-through** — the cache library loads from the source on a miss. Same shape as cache-aside with the load logic moved into the cache layer. Needs library/provider support.
- **Write-through** — every write goes to cache and source synchronously. Cache is never stale *from this app's writes*; adds latency to every write; still stale if an external system writes the source. Choose when reads must reflect this app's writes instantly and write volume is modest.
- **Write-behind (write-back)** — write to cache, flush to source asynchronously. Fast writes, absorbs write bursts; risks data loss if the cache dies before flush, and the source is transiently behind. Only for tolerant data (counters, metrics, activity) with a durable-enough cache.
- **Refresh-ahead** — proactively refresh hot entries before they expire. Hides miss latency for predictably-hot keys; wastes refreshes on keys that go cold. Layer it on cache-aside for a known hot set.

Record the pattern and the specific consistency behavior it accepts.

## 5. Set the freshness mechanism

- **Explicit invalidation on write** — the app deletes (or updates) the cache entry in the same flow that writes the source. Required when the staleness class is "until explicitly changed" (prices, permissions, published/unpublished). Handle the write-then-invalidate race (delete after the source commit; consider a short "delete again" or versioned write to beat a concurrent repopulate).
- **TTL** — set it *from the staleness budget in step 2*, not a round number. 60s because a minute of staleness is acceptable — not "5 minutes" by habit. Add jitter (see step 7).
- **Both** — the common answer: explicit invalidation for correctness, a modest TTL as a backstop against missed invalidations and unknown external writes.
- **Key namespacing / versioning** — prefix keys with a version or a per-entity generation number so a whole class can be invalidated by bumping the prefix (`user:{id}:v3:...`), avoiding a scan-and-delete. Design the key scheme now.

## 6. Set eviction policy and size

From `patterns-and-policies.md` and gate items 6–7:

- **Access pattern skewed to a hot set** (typical web traffic) → **LRU** or **LFU/TinyLFU** (LFU/TinyLFU resist a scan flushing the hot set). Redis `allkeys-lru` / `allkeys-lfu`.
- **Scan-like / one-hit-heavy** → LRU thrashes; add **negative caching** for the misses and consider **TinyLFU**; or reconsider whether this data should be cached at all.
- **FIFO / random** — only when eviction order barely matters and simplicity wins.
- **Size** — budget for the working set (gate item 6) plus headroom (Redis needs room above `maxmemory` for replication buffers and fragmentation — plan ~25–30%). Set the `maxmemory-policy` explicitly; decide whether eviction or an OOM error is the safer failure for this data (`noeviction` turns a full cache into write errors — usually wrong for a cache, sometimes right for a load-bearing dataset you'd rather alarm on).
- **TTL vs eviction** — TTL bounds staleness; eviction bounds memory. You need both.

## 7. Handle the failure modes explicitly

- **Stampede / dogpile / thundering herd** — a hot key expires and N concurrent requests all miss and hit the source together. Mitigate with a per-key recompute lock (`SETNX` + short TTL, others briefly serve stale or wait), request coalescing (single-flight), or probabilistic early recomputation before expiry.
- **Penetration** — requests for keys that don't exist in the source (scans, bad IDs) miss every time and always hit the source. Mitigate with **negative caching** (cache the "not found" with a short TTL) and/or a bloom filter of valid keys.
- **Avalanche** — many keys expire at once (same TTL set during a warmup or deploy), or the whole cache is flushed/restarted, dumping full load on the source. Mitigate with **TTL jitter** (`ttl ± rand`), staggered warmup, and confirming step 8's cold-start answer.
- **Cache-down** — from gate item 10: if the cache is an optimization, the app should fall through to the source on a cache error (with a timeout and a circuit breaker so a slow cache doesn't add latency). If it's load-bearing, this is an outage — which forces the HA posture in step 8.

## 8. Set the HA posture

From gate item 10:

- **Optimization** (origin survives 100% miss) — a single cache node is acceptable. Alarm on hit rate and eviction rate so a silently-dead cache is noticed. Fall-through on error (step 7).
- **Load-bearing** (origin cannot take the full load) — treat the cache like a database: replication (Redis replica + Sentinel, or Cluster), automatic failover, `maxmemory` headroom, persistence (RDB/AOF) if a cold restart would take down the origin, and request coalescing so a failover's cold window doesn't stampede. Also: reconsider step 1 — a load-bearing cache often means the *source* needs the replica/scaling work (`data-tier-operations`), with the cache as latency optimization rather than capacity crutch.

## 9. Name the metrics and the revisit trigger

- **Metrics**: hit rate (target and floor), eviction rate, p99 with and without the cache, and the measured drop in source load. Without these you can't tell later whether the cache still earns its operational cost.
- **Revisit when**: a concrete threshold — "hit rate below X%", "the data's change rate makes any TTL within budget a near-certain miss", "the source can now serve this uncached", "read QPS on this path fell below the level that justifies the tier".

## 10. Recommend and record

Produce the recommendation block from `SKILL.md`. On approval, write the ADR using `database-architecture`'s `adr-template.md` in `docs/architecture/decisions/`. The **Revisit when** line is the point of the document — make it the step 9 threshold, not "when it's slow again".

Then stop. Wiring the cache client, the invalidation hooks, and the warmup job are a separate, explicitly-started step.
