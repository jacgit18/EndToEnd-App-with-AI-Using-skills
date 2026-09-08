# Patterns and Policies

Read/write patterns, freshness mechanisms, eviction policies, sizing, and the failure modes — the material behind `caching-framework.md` steps 4–8.

## Read/write patterns

### Cache-aside (lazy loading) — the default

Application logic:

```
read(key):
  v = cache.get(key)
  if v is not None: return v          # hit
  v = source.load(key)                # miss
  cache.set(key, v, ttl)
  return v

write(key, value):
  source.save(key, value)
  cache.delete(key)                   # or cache.set(key, value, ttl)
```

- **Pros** — cache holds only what's actually requested; the cache being down only costs latency, not correctness; works no matter who else writes the source.
- **Cons** — every miss pays the source latency; you own the invalidation on write; a write-then-read race can repopulate a stale value (mitigate: delete *after* the source commit; optionally delayed double-delete, or write a version number).
- **Delete vs update on write** — deleting is safer (next read repopulates from the source of truth); updating the cache directly risks writing a value that loses a concurrent source write.

### Read-through

The cache library sits in front of the source and loads on a miss itself; the app only ever calls `cache.get`. Same consistency profile as cache-aside, with the load path centralized in the cache layer. Needs provider support (e.g. a `CacheLoader`).

### Write-through

Every write goes synchronously to cache and source:

```
write(key, value):
  source.save(key, value)
  cache.set(key, value, ttl)
```

- **Pros** — reads always reflect *this application's* writes; no miss penalty for recently-written keys.
- **Cons** — adds cache-write latency to every write; caches data that may never be read; **still stale** when an external system writes the source (so pair with a TTL); a failure between the two writes needs handling.
- **Use when** — read-after-write consistency matters, write volume is modest, and this app is effectively the only writer.

### Write-behind (write-back)

Write to cache, acknowledge, flush to the source asynchronously (batched/coalesced).

- **Pros** — very fast writes; absorbs bursts; coalesces repeated writes to the same key.
- **Cons** — data loss if the cache dies before the flush; the source is transiently behind; reads from elsewhere (or after a cache loss) see old data; ordering/retry logic on the flush queue.
- **Use when** — high-volume, loss-tolerant writes: counters, metrics, "last seen", activity feeds — backed by a durable-enough cache.

### Refresh-ahead

Proactively reload an entry before its TTL expires (e.g. when it's read and within the last X% of its life). Hides miss latency for predictably-hot keys; wastes work on keys that have gone cold. Layer on top of cache-aside for a known hot set.

### Pattern selection

| Need | Pattern |
|---|---|
| General read scaling, cache-down must not break correctness | Cache-aside |
| Same, load logic centralized in the cache layer | Read-through |
| Reads must see this app's writes immediately, app is sole writer | Write-through (+ TTL) |
| Fast/bursty writes, loss-tolerant data | Write-behind |
| Known hot keys, want to hide miss latency | Refresh-ahead over cache-aside |

## Freshness: invalidation vs TTL vs versioned keys

- **Explicit invalidation on write** — delete/update the entry in the same flow that writes the source. The only correct choice for "must be fresh until explicitly changed" data (prices, permissions, publish state). Cross-instance/service: broadcast via pub/sub or bump a shared generation number.
- **TTL** — a time bound on staleness. Set it *from the staleness budget*, not a habit number. It's also the backstop for writes you didn't see (external systems) and invalidations you missed (bugs, network).
- **Both** — the common production answer: explicit invalidation for correctness + a modest TTL as a safety net.
- **Versioned / namespaced keys** — embed a version or per-entity generation in the key (`catalog:v7:product:42`). Invalidate a whole class by bumping the version — O(1), no `SCAN`/`KEYS`. Old entries age out by eviction/TTL.
- **Tag / surrogate-key purge** — at CDN/proxy layers, attach tags to responses and purge by tag so one entity change busts every response containing it.

## Eviction policies

Eviction bounds **memory**; TTL bounds **staleness**; you need both.

- **LRU (Least Recently Used)** — evict the entry unused for the longest. Good default for skewed web traffic (a stable hot set). Weakness: a large scan (batch job, crawler) can flush the hot set.
- **LFU (Least Frequently Used)** — evict the least-accessed. Keeps a genuinely hot set resident against scans. Weakness: naive LFU lets stale-but-once-popular keys linger; needs aging.
- **TinyLFU / W-TinyLFU** (Caffeine, and Redis LFU is frequency-with-decay) — frequency estimate with decay + a small LRU admission window. Best general-purpose modern choice; scan-resistant.
- **FIFO** — evict oldest-inserted regardless of use. Simple; ignores access pattern; usually worse than LRU for caches.
- **Random / sampled** — Redis approximates LRU/LFU by sampling N keys and evicting the best candidate (`maxmemory-samples`). Cheap; slightly less accurate than true LRU.
- **Redis `maxmemory-policy`** — `allkeys-lru` / `allkeys-lfu` (evict from all keys), `volatile-lru` / `volatile-lfu` / `volatile-ttl` (evict only keys with a TTL), `noeviction` (reject writes when full — turns a full cache into write errors; only for a dataset you'd rather alarm on than silently shrink).

**Pick from the access pattern**: skewed hot set → LRU or LFU/TinyLFU; scan-heavy or one-hit-heavy → TinyLFU + negative caching, or reconsider caching it; eviction order truly doesn't matter → FIFO/random.

## Sizing

- Budget for the **working set** (distinct hot keys × average entry size), not the whole keyspace.
- **Headroom** — Redis needs room above `maxmemory` for replication/output buffers, COW during persistence, and allocator fragmentation. Plan ~25–30% above the working set; watch `mem_fragmentation_ratio`.
- **Per-entry overhead** — Redis keys/values carry tens of bytes of overhead each; millions of tiny keys cost more than the payload suggests. Consider hashing related fields into one key.
- **Eviction rate is the signal** — a healthy cache evicts near zero. Sustained eviction means undersized or TTL too long; alarm on it.

## Failure modes

### Stampede / dogpile / thundering herd

A hot key expires; many concurrent requests miss and hammer the source simultaneously.

- **Per-key recompute lock** — first miss takes a lock (`SET key.lock val NX PX <short>`), recomputes, and repopulates; others briefly serve the last stale value or wait-and-retry.
- **Single-flight / request coalescing** — in-process, collapse concurrent misses for the same key into one source call.
- **Probabilistic early recomputation** — refresh before expiry with a probability that rises as the TTL approaches (XFetch), so one request refreshes ahead of the crowd.

### Penetration

Requests for keys that don't exist in the source miss every time and always hit it (scanning attacks, bad IDs).

- **Negative caching** — cache the "not found" result with a short TTL.
- **Bloom filter** of valid keys in front of the cache — a definite "not present" answer without touching the source.

### Avalanche

Many keys expire together (uniform TTL set during a warmup/deploy), or the cache restarts/flushes, dropping full load on the source at once.

- **TTL jitter** — `ttl = base ± random(spread)` so expiries spread out.
- **Staggered warmup** — populate gradually, not all at once.
- **Cold-start protection** — persistence (RDB/AOF) so a restart isn't a cold cache; or coalescing + a source that can survive the cold window (gate item 10).

### Cache-down

- **Optimization cache** — fall through to the source on error, wrapped in a timeout + circuit breaker so a slow cache doesn't *add* latency.
- **Load-bearing cache** — this is an outage; see HA below.

## SPOF and HA for a load-bearing cache

If the source cannot absorb 100% of the read traffic (gate item 10), the cache is infrastructure, not an optimization:

- **Replication + failover** — Redis replica(s) + Sentinel for automatic promotion, or Redis Cluster for sharding + failover. Managed (ElastiCache, MemoryDB) does this for you; MemoryDB adds durability.
- **Multi-node / sharding** — spread keys so one node's loss is a fraction of capacity, not all of it.
- **Persistence** — AOF (per-second fsync typical) or RDB snapshots so a restart reloads warm rather than cold.
- **`maxmemory` headroom + `noeviction` consideration** — decide whether a full load-bearing cache should evict (lose coverage) or reject writes (alarm).
- **Reconsider the design** — a load-bearing cache is often a sign the *source* needs the replica/scaling work (`data-tier-operations`), with the cache demoted back to latency optimization.
