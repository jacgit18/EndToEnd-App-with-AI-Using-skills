# Worked Examples

Three estimates worked end to end from stated assumptions, following the
`storage → traffic → cache → servers → what binds first` walk order in
`estimation-method.md`. Each lands on a *different* binding constraint, which is the point:
the estimate is worth doing because you cannot guess which ceiling arrives first.

Numbers are rounded aggressively and kept in scientific notation. `s/day = 86,400`.

---

## Example 1 — read-heavy social feed (comments + likes)

**Binds first: read QPS / cache.**

### Assumptions (the gate)

| Item | Value |
|---|---|
| Driver | 200M DAU |
| Write actions/user/day | 5 (≈ 3.3 likes, ≈ 1.7 comments) |
| Read actions/user/day | ~250 (feed + thread views) |
| Stored bytes/write | like 100 B, comment 400 B (text ~200 B × 2 for indexes + metadata) |
| Returned bytes/read | ~300 B (one object or a small count) |
| R:W ratio | 50:1 |
| Peak:average | 2×, evening |
| Retention + growth | keep 5 years; DAU grows linearly to 2× |
| Replication | 3 |

### Step 0 — base rates

```
writes/day = 200M × 5            = 1.0 × 10^9
  likes    = 200M × 3.3          = 6.7 × 10^8
  comments = 200M × 1.7          = 3.3 × 10^8
reads/day  = 50 × 1.0 × 10^9     = 5.0 × 10^10      (cross-check: 200M × 250 = 5.0 × 10^10 ✓)

avg write QPS = 1.0e9  ÷ 86,400  ≈ 1.16 × 10^4
avg read QPS  = 5.0e10 ÷ 86,400  ≈ 5.8  × 10^5
peak write QPS ≈ 2.3 × 10^4
peak read QPS  ≈ 1.16 × 10^6
```

### Step 1 — storage

```
bytes/day = 6.7e8 × 100 B  +  3.3e8 × 400 B
          = 6.7e10          +  1.33e11
          = 2.0 × 10^11 B/day   ≈ 200 GB/day
bytes/year = 200 GB × 365          ≈ 73 TB/year
5-year, growth linear to 2× → expected multiplier (1+2)/2 = 1.5
  expected   = 73 TB × 5 × 1.5     ≈ 550 TB
  end-state  = 73 TB × 5 × 2       ≈ 730 TB
provisioned  = × 3 replication     ≈ 1.6 – 2.2 PB
```

### Step 2 — traffic

```
egress/day  = 5.0e10 reads × 300 B   = 1.5 × 10^13 B/day   ≈ 15 TB/day
ingress/day = 1.0e9 writes × ~300 B  = 3.0 × 10^11 B/day   ≈ 300 GB/day
peak egress = (1.5e13 ÷ 86,400) × 2 × 8  ≈ 2.8 Tbps
```

2.8 Tbps at peak is not servable from an origin tier — most reads must hit a cache, and
hot read *responses* belong at a CDN / edge. Little of this is CDN-offloadable as static
content (it is dynamic per-user data), so the cache tier carries it.

### Step 3 — cache working set

```
hot window   ≈ last 2 days of writes carry ~90% of reads
distinct hot ≈ 2 × 1.0e9 = 2.0 × 10^9 objects
hot fraction  20%  → 4.0 × 10^8 objects
avg size ~250 B    → 1.0 × 10^11 B   ≈ 100 GB
+ overhead 1.3×    ≈ 130 GB
```

~130 GB fits in a small Redis/Memcached cluster (3–5 nodes). It is **cheap relative to the
1.16M peak read QPS it absorbs** — this is the leverage point of the whole design.
(Contrast the source-note method: `5e10 reads × 250 B × 0.2 = 2.5 TB`, then `× 3 = 7.5 TB`
— overstated ~50× by counting reads instead of distinct hot objects.)

### Step 4 — servers

Read tier, CPU-bound, ~0.5 ms service time for a cache-backed read:

```
per server = 8 cores × 0.7 ÷ 5e-4 s   ≈ 1.1 × 10^4 req/s
servers    = 1.16e6 ÷ 1.1e4           ≈ 105
× 1.5 redundancy (AZ loss)            ≈ 160  read-tier nodes
```

Write tier, ~2 ms service time: `8 × 0.7 ÷ 2e-3 ≈ 2,800 req/s`; `2.3e4 ÷ 2,800 ≈ 9`,
`× 1.5 ≈ 14` nodes.

### Step 5 — what binds first

**Read QPS / cache-and-fan-out.** At 5.8 × 10^5 average (1.16M peak) read QPS the primary
store cannot serve reads directly; the design lives or dies on cache hit rate and read
fan-out. The good news the estimate surfaces: the hot working set is only ~130 GB, so a
high hit rate is affordable. Storage (73 TB/year) and the write path (11.6K QPS) have years
of headroom by comparison. Egress at multi-Tbps peak says edge caching of hot responses is
mandatory, not an optimization.
→ topology for the read store / replicas: `data-tier-operations`.
→ protecting the cache and store under a hit-rate miss storm: `resilience-strategy`.

---

## Example 2 — media-streaming service

**Binds first: egress bandwidth.**

### Assumptions

| Item | Value |
|---|---|
| Driver | 10M DAU |
| Play actions/user/day | 60 songs (20/hr × 3 hr) |
| Bytes streamed/play | 128 kbps × 180 s ÷ 8 = 2.88 × 10^6 B ≈ 2.9 MB |
| Play-event write/play | ~120 B (song id, user id, ts, context — for royalties + recs) |
| Catalog | 1 × 10^8 songs, 3 bitrates |
| R:W ratio | plays are reads of the catalog; writes are only the play events |
| Peak:average | 3×, evening |
| Retention + growth | play events kept 2 years; catalog grows ~10%/year; DAU flat |
| Replication | 3 |

### Step 0 — base rates

```
plays/day       = 10M × 60          = 6.0 × 10^8
avg play QPS     = 6.0e8 ÷ 86,400   ≈ 6.9 × 10^3
peak play QPS    ≈ 2.1 × 10^4       (play-starts/s)
play-events/day  = 6.0 × 10^8       (1 per play)
```

### Step 1 — storage

**Catalog** (dominates resident storage, but it is near-static):
```
per song, 3 bitrates ≈ 3 × 2.9 MB = 8.7 MB   (use the 128 kbps size as the mid)
catalog = 1e8 × 8.7 MB   = 8.7 × 10^14 B   ≈ 870 TB
× 3 replication          ≈ 2.6 PB
grows ~10%/year → ~3.5 PB in 2 years
```

**Play events** (grow with usage, small):
```
6.0e8/day × 120 B = 7.2 × 10^10 B/day  ≈ 72 GB/day
× 365 × 2 years    ≈ 53 TB
× 1.5 index overhead × 3 replication ≈ 240 TB
```

### Step 2 — traffic

```
egress/day  = 6.0e8 plays × 2.9 MB = 1.74 × 10^15 B/day   ≈ 1.74 PB/day
peak egress = (1.74e15 ÷ 86,400) × 3 × 8  ≈ 4.8 × 10^11 bps  ≈ 480 Gbps sustained at peak
ingress/day = 6.0e8 × 120 B  ≈ 72 GB/day   (negligible)
```

Audio is immutable and cacheable → **CDN-offloadable fraction is ~95%+**. Origin egress is
only cache-fill: `~5% × 1.74 PB/day ≈ 87 TB/day`, peak ~24 Gbps. The 480 Gbps is what the
CDN edge serves to users.

### Step 3 — cache working set

```
top 20% of catalog serves ~80% of plays
hot = 2e7 songs × 2.9 MB (one bitrate, the popular one) = 5.8 × 10^13 B  ≈ 58 TB
```

Distributed across CDN PoPs, not one box — ~58 TB of edge cache capacity, spread over
dozens of locations.

### Step 4 — servers

The streaming path is **I/O / bandwidth bound**, not CPU bound — sized by egress capacity
and object-store read throughput, not `peak QPS ÷ service time`. The control-plane API
(auth, playlists, play-event ingest) is CPU-bound and small: 2.1e4 peak play-starts/s at
~3 ms ≈ `8 × 0.7 ÷ 3e-3 ≈ 1,870/s per node` → ~12 nodes × 1.5 ≈ 18.

### Step 5 — what binds first

**Egress bandwidth.** ~1.74 PB/day, ~480 Gbps at peak, is the ceiling that arrives first
and dominates the cost. The entire architecture is organized around CDN offload; without it
the origin needs half a terabit of uplink. Catalog storage (~3 PB) is large but static and
solved by object storage tiers. Compute is a rounding error. Play-event storage (~240 TB
over 2 years) is comfortable.
→ CDN vs origin egress **cost**: `technical-cost-decision`.
→ object-store read throughput for cache-fill: `data-tier-operations`.

---

## Example 3 — write-heavy telemetry / event pipeline

**Binds first: storage growth rate.**

### Assumptions

| Item | Value |
|---|---|
| Driver | 2M devices reporting |
| Write actions/device/day | 1,440 (one metric batch per minute) |
| Stored bytes/write | 800 B (batch of ~10 metrics + tags, after light compression, incl. index) |
| Read actions/day | dashboards + alert evals ≈ 5 × 10^6 queries/day, each scanning ~2 MB |
| R:W ratio | write-heavy — reads are ~0.2% of writes by count |
| Peak:average | 1.5× (machine-driven, mostly steady; mild batching alignment) |
| Retention + growth | 30 days hot, 13 months cold; devices grow linearly to 3× over 2 years |
| Replication | 3 (hot), 2 (cold) |

### Step 0 — base rates

```
writes/day    = 2e6 × 1,440         = 2.88 × 10^9
avg write QPS  = 2.88e9 ÷ 86,400    ≈ 3.3 × 10^4
peak write QPS ≈ 5.0 × 10^4
reads/day     = 5 × 10^6
avg read QPS   ≈ 58
```

### Step 1 — storage

```
bytes/day = 2.88e9 × 800 B          = 2.3 × 10^12 B/day   ≈ 2.3 TB/day
hot (30 d) = 2.3 TB × 30            ≈ 69 TB   × 3 repl     ≈ 207 TB
cold (13 mo ≈ 400 d) = 2.3 TB × 400 ≈ 920 TB × 2 repl     ≈ 1.84 PB
growth to 3× devices, linear, over 2 years → expected multiplier (1+3)/2 = 2
  expected resident in 2 years ≈ (207 TB + 1.84 PB) × 2   ≈ 4.1 PB
  end-state ceiling            ≈ × 3                        ≈ 6.2 PB
write byte-rate = 2.3 TB/day ≈ 27 MB/s sustained, ~40 MB/s peak — well within a
  distributed store, but it never stops, and it compounds with device growth
```

### Step 2 — traffic

```
ingress/day = 2.88e9 × 800 B ≈ 2.3 TB/day     (peak ~40 MB/s = 0.32 Gbps — small)
egress/day  = 5e6 queries × 2 MB result-scan ≈ 10 TB/day internal read bandwidth
              user-facing egress (rendered dashboards) ≈ 5e6 × 50 KB ≈ 250 GB/day — trivial
```

### Step 3 — cache working set

Query cache over recent windows: dashboards mostly hit the **last 1 hour** of data plus
pre-computed rollups. Last hour ≈ `2.88e9 ÷ 24 × 800 B ≈ 96 GB`; cache 100% of it + rollup
tables (~a few GB) → ~110 GB, + overhead ≈ 140 GB. Modest.

### Step 4 — servers

Ingest tier is CPU-bound on parse + compress + index at ~0.2 ms/write:
`8 × 0.7 ÷ 2e-4 ≈ 28,000/s per node`; `5.0e4 peak ÷ 28,000 ≈ 2`, `× 2 redundancy ≈ 4–6`
ingest nodes. Small. Query tier sized off ~58 read QPS — a handful.

### Step 5 — what binds first

**Storage growth rate.** ~2.3 TB/day today, compounding to ~2× that as devices grow,
retained for 13 months, replicated — multiple petabytes resident within two years, growing
without pause. Nothing else is close: ingest compute is ~5 nodes, ingress is sub-Gbps,
reads are trivial. The design questions the estimate forces are all storage-shaped:
retention policy, hot/cold tiering, compression ratio, downsampling of old data,
partition-by-time.
→ tiering / partitioning / retention mechanics: `data-tier-operations`.
→ the storage bill and whether cold belongs in object storage: `technical-cost-decision`.
→ shedding / sampling ingest if the write rate outpaces the store: `resilience-strategy`.
