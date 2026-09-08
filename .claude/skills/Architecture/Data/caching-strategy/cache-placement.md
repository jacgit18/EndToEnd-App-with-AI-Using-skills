# Cache Placement

The layers a cache can sit at, from closest to the consumer to closest to the source. General rule: **the closer to the consumer, the cheaper and faster the hit — and the harder it is to invalidate.** Pick the closest layer that still lets you meet the staleness budget from `caching-framework.md` step 2.

## Client / browser (HTTP caching)

**What it is** — `Cache-Control`, `Expires`, `ETag` / `If-None-Match`, `Last-Modified` / `If-Modified-Since`, and stale-while-revalidate on responses the client repeats. Also app-level client caches (a mobile app's local store, a SPA's query cache like React Query / SWR).

**Solves** — eliminates the request entirely on a hit; zero server cost; best possible latency.

**Costs / limits** — you cannot invalidate a client cache you've already populated; freshness is whatever `max-age` you committed to. `ETag` gives revalidation (a cheap 304) but still a round trip. Only safe when a fixed staleness window is acceptable, or when revalidation cost is fine.

**Invalidation** — TTL expiry, or content-hashed URLs (`app.a1b2c3.js`) so a new version is a new key. For revalidation, `ETag`.

**Use when** — public or per-user GET responses, static assets, API responses with a tolerable fixed max-age.

## CDN / edge

**What it is** — a distributed network of edge caches (CloudFront, Cloudflare, Fastly, Akamai) keyed on URL plus a configured `Vary` set, serving from the POP nearest the user.

**Solves** — huge origin offload for popular content; geographic latency; absorbs traffic spikes and some DDoS.

**Costs / limits** — per-request and egress pricing (→ `technical-cost-decision`). Only content that's identical for many users caches well; per-user or auth-varying responses need careful cache-key design (or `private` + skip). Query-string permutations can shatter the hit rate. Purge is explicit and propagates with a delay (seconds to minutes); some providers bill per purge.

**Invalidation** — TTL, explicit purge (by URL, by tag/surrogate-key, or purge-all), or versioned URLs. Surrogate-key/tag purge (Fastly, Cloudflare) lets one entity change bust every response tagged with it.

**Use when** — assets always; HTML/JSON when it's public, keyed only on path + a small vary set, and a short TTL or tag-purge meets the budget.

## Reverse proxy (nginx, Varnish, Apache Traffic Server)

**What it is** — a shared HTTP cache you run, in front of the application, in your own infrastructure.

**Solves** — CDN-style offload for the origin without a third party; full control over purge and cache keys; can cache internal service-to-service HTTP too.

**Costs / limits** — another hop and another thing to operate and scale; a single proxy is a SPOF unless itself redundant; no geographic distribution.

**Invalidation** — Varnish has a rich purge/ban API; nginx `proxy_cache` supports `proxy_cache_purge` (with a module) or key-based cache bypass.

**Use when** — public or cacheable responses where you want purge control and don't want (or can't use) a CDN; or as an origin shield behind a CDN.

## In-process application cache

**What it is** — an in-memory structure inside the service process: a plain map, Guava/Caffeine (JVM), `lru-cache` (Node), `functools.lru_cache` / `cachetools` (Python), `MemoryCache` (.NET).

**Solves** — nanosecond hits, no network, no serialization, no extra infrastructure. Ideal for tiny hot reference data.

**Costs / limits** — **per-instance**: each process has its own copy, so with N instances you get N independent stale windows, N cold starts, and an invalidation must be broadcast to every instance (pub/sub, a shared "generation" counter, or just a short TTL and acceptance of the skew). Consumes the service's own heap/RAM — competes with request handling. Lost on every deploy/restart.

**Use when** — small (fits comfortably in heap), hot, read-mostly data; few instances; a short TTL is acceptable so cross-instance skew is bounded; e.g. feature flags, config, a small lookup table, per-request memoization.

## Distributed application cache (Redis, Memcached, ElastiCache, Hazelcast)

**What it is** — a separate cache tier the whole fleet shares over the network.

**Solves** — one logical cache: a single write/invalidation is seen by every app instance; survives individual app restarts; sized independently of the app; can hold a large working set.

**Costs / limits** — a network hop per access (~0.2–1ms in-AZ, more cross-AZ); a new tier to run, monitor, secure, and pay for (instance-hours + memory + possibly cross-AZ transfer → `technical-cost-decision`); itself a potential SPOF (→ replication/failover for a load-bearing cache).

**Redis vs Memcached** — Redis: rich data types, optional persistence, pub/sub, Lua, single-threaded core (per-shard), Cluster for sharding, replica + Sentinel for HA. Memcached: multithreaded, pure key→blob LRU, trivially simple, scales by adding nodes with client-side hashing; no persistence, no replication. Default to Redis unless you specifically want Memcached's simplicity and multithreaded throughput for a plain blob cache.

**Use when** — multiple app instances; a shared invalidation story matters; the working set is too big for in-process; you need TTL + eviction managed centrally.

## Database query / buffer cache

**What it is** — the database's own caching: the buffer pool / `shared_buffers` (hot pages in RAM), the plan cache, and (where it exists) a result cache. Materialized views are an explicit, query-able form.

**Solves** — already present; enlarging the buffer pool so the working set fits in RAM is often a large, free latency win with zero application change or consistency cost.

**Costs / limits** — bounded by the DB instance's memory; doesn't reduce connection or CPU load the way an external cache does; MySQL's old query cache is removed in 8.0 (it serialized writes). Materialized views need a refresh strategy (their own staleness decision).

**Use when** — always worth checking first (`caching-framework.md` step 1); a materialized view is the answer when you want a maintained read model inside the database's transactional guarantees rather than an external cache's eventual ones.

## Choosing between layers — quick heuristic

| Situation | Layer |
|---|---|
| Static assets, public content | CDN (+ content-hashed URLs) |
| Public API GET, short staleness OK, want purge control | Reverse proxy or CDN with tag purge |
| Per-user response the client re-requests | Client / HTTP `Cache-Control: private` + `ETag` |
| Small hot reference data, 1–3 app instances | In-process, short TTL |
| Shared hot data, many app instances, need coordinated invalidation | Distributed (Redis) |
| "One query is slow and the box has spare RAM" | Enlarge the DB buffer pool; consider a materialized view |
| Need a maintained read model with transactional freshness | Materialized view (not a cache) |

Multiple layers can coexist (CDN in front of a reverse proxy in front of an app that reads Redis) — but every added layer is another staleness window and another invalidation path. Add the fewest that meet the pressure.
