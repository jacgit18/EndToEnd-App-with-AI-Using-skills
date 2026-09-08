# Estimation Method

The cleaned-up method for `SKILL.md`. The source notes (`Bandwidth Estimation.md`,
`Capacity Estimation.md`, `Music Streaming Service Estimation.md`) carry the right shape but
several self-flagged arithmetic errors (`#todo Double check calculations`). This file fixes
the method; the anti-patterns section at the end lists the specific errors so they are not
reintroduced.

---

## Numbers you work in

### Bytes — use powers of 10, not 2

| Unit | Bytes (estimation) | Exact (2^n) |
|---|---|---|
| 1 KB | 1,000 | 1,024 |
| 1 MB | 1,000,000 (10^6) | 1,048,576 |
| 1 GB | 1,000,000,000 (10^9) | 1,073,741,824 |
| 1 TB | 10^12 | ~1.1 × 10^12 |
| 1 PB | 10^15 | ~1.13 × 10^15 |

For an a-priori estimate, `1 KB = 1,000 bytes`. The 2.4% error from ignoring the binary
prefix is noise next to the ±2× uncertainty in the assumptions themselves. Keep everything
in scientific notation (`5 × 10^10`), not comma-grouped integers — it makes the arithmetic
checkable and stops zero-counting mistakes.

### Time

| Span | Seconds | Estimation shortcut |
|---|---|---|
| 1 hour | 3,600 | — |
| 1 day | 86,400 | use as-is; if you must round for mental math, round *down* to 80,000 (biases the rate high — safe) |
| 1 month (30 d) | 2,592,000 | ~2.5 × 10^6 |
| 1 year (365 d) | 31,536,000 | ~3 × 10^7 |

Simplest is to divide by 86,400 directly. Rounding it *up* to 100,000 under-states QPS by
~15%; rounding *down* to 80,000 biases it high. Either way, size the final capacity off the
**peak** rate (average × peak factor), so the rounding direction on the average is not what
the design hangs on.

---

## The walk order

`storage → traffic → cache → servers → what binds first`. Each stage needs outputs of the
previous one, and the final comparison needs all four ceilings computed.

### Step 0 — base rates

From gate items 3–7:

```
writes/day        = driver × write-actions per driver per day        (sum over write types)
reads/day         = writes/day × (R:W ratio)      — OR —  driver × read-actions per driver per day
```

Compute reads/day both ways when the user gave both the ratio *and* per-user read actions;
if they disagree by more than ~2×, that is a flag to resolve before continuing.

```
avg write QPS     = writes/day ÷ seconds per day
avg read QPS      = reads/day  ÷ seconds per day
peak QPS (type)   = avg QPS (type) × peak:average ratio
```

Carry average **and** peak for both reads and writes. Everything downstream that is a
*rate* (bandwidth, server count) is sized off peak; everything that is a *volume* (storage)
is sized off the daily total.

### Step 1 — storage (writes only)

Reads never add stored bytes. For each write type:

```
stored bytes per record  = raw field bytes × overhead multiplier
```

**Overhead multiplier ~1.3–2×** covers row headers, null bitmaps, per-row metadata, and —
usually the biggest part — secondary indexes. A 40-byte comment with a primary key, a
`(user_id, created_at)` index, and a `(video_id, created_at)` index is realistically
150–250 stored bytes. Use 1.5× as a default, 2× if the record is heavily indexed or small.

```
bytes/day          = Σ (writes/day of type × stored bytes per record of type)
bytes/year         = bytes/day × 365
bytes over horizon = bytes/day × 365 × horizon_years × growth_multiplier
provisioned        = bytes over horizon × replication_factor
```

**Growth multiplier** from gate item 8:

| Growth shape over N years | Expected multiplier | End-state ceiling |
|---|---|---|
| Flat | 1 | 1 |
| Linear to G× | (1 + G) / 2 | G |
| Doubling yearly (2^N over N years) | ~ (2^N − 1) / (N ln 2) | 2^N |

Report both the **expected** (use the expected multiplier) and the **end-state ceiling**
(use the ceiling multiplier) — provision toward the ceiling, budget toward the expected.

### Step 2 — traffic / bandwidth

```
egress bytes/day   = reads/day  × response payload bytes      (bytes leaving the system)
ingress bytes/day  = writes/day × request payload bytes       (bytes entering)
```

Egress almost always dominates: the system is read-heavy and a response is larger than a
write acknowledgement.

**"Returned bytes per read" is the content / API payload**, not the page weight. For a
browser-facing system the HTML + JS + CSS + fonts + images on the wire are separate and
usually 10–100× the API payload — but they are typically immutable and CDN-offloadable, so
they inflate the *user-facing* egress total, not the *origin* egress. Report both when the
system serves a web UI: origin egress ≈ `(1 − CDN offload) ×` the full number.

Convert to a peak line rate in **bits** per second:

```
peak egress (bps)  = (egress bytes/day ÷ seconds per day) × peak:average ratio × 8
```

Report GB/day and peak Gbps. Note the **CDN-offloadable fraction** — cacheable static
responses (media, immutable assets) can be served from edge, so origin egress is
`(1 − offload) × egress`; the user-facing total is still the full number. The CDN *decision*
is not this skill's, but the split changes which egress number binds.

### Step 3 — cache working set

A cache holds **one copy per hot object**, not one per read. The working set is the size of
the hot set, independent of how many times each hot object is read.

```
hot object count   = distinct objects served in the window × hot fraction
cache bytes        = hot object count × object size in cache
+ overhead ~1.2–1.3×  (slab/fragmentation, key overhead, metadata)
```

**Hot fraction** — the 80/20 rule as a starting point: ~20% of objects serve ~80% of
reads; cache that 20%. Adjust from the access pattern (a recency-dominated feed might have
5% hot; a small reference dataset, 100%).

**Estimating "distinct objects served in the window"** when it is not given, pick the model
that matches the access pattern:

- **Recency-driven** (feeds, timelines, chat): bound by recent writes — "reads concentrate
  on the last 2 days" → distinct hot objects ≈ 2 × writes/day.
- **Structure-driven** (a link aggregator's front page + top-N threads, a storefront's
  category pages, a leaderboard): size the *structure* — the number of listing pages, top-N
  entries, or featured objects that actually get served — not a time window. A recency
  window will land in the right order of magnitude but hands you the wrong mental model.
- **Fixed dataset** (reference data, a product catalog): the hot fraction of the whole set.

A cache is usually **not** replicated for durability (it is a cache); if it is replicated
for read throughput or HA, multiply, but say so.

### Step 4 — server count (compute tier)

First classify the bind (see `Request Resource Bound` in the notes): **CPU-bound**,
**memory-bound**, or **I/O-bound**. Server math only makes sense for the CPU-bound case;
I/O-bound tiers are sized by the downstream (object store, DB) and memory-bound tiers by
`working set ÷ RAM per node`.

CPU-bound:

```
per-server capacity (req/s) = (cores × target_utilization) ÷ per-request service time (s)
servers                     = peak QPS ÷ per-server capacity
provisioned servers         = servers × (1 + redundancy)     — round UP
```

- `target_utilization` ~0.6–0.7 (headroom for GC pauses, bursts, and the tail).
- `per-request service time` is CPU-seconds per request — estimate from the work (a cached
  read: 0.1–1 ms; a templated page render: 5–50 ms; a heavy aggregation: 100 ms+).
- `redundancy`: `+2` nodes to tolerate two failures, or `×1.5` to tolerate losing an
  availability zone. Whichever is larger.

This replaces the source note's `cores ÷ 0.5` shortcut, which fixes service time at 500 ms
and applies no utilization headroom.

### Step 5 — what binds first

Line up the five ceilings and their headroom at the stated growth:

| Ceiling | Binds when |
|---|---|
| Storage growth rate | provisioned bytes over horizon approaches affordable / rack-able disk, **or** the write byte-rate approaches the store's sustained write throughput |
| Peak read QPS | peak read QPS approaches per-node read capacity × node budget for the primary store |
| Peak egress | peak Gbps approaches the uplink / NIC / CDN-origin budget |
| Cache working set | hot-set bytes exceed the RAM you would pay for (the point where hit rate must drop) |
| Peak compute QPS | provisioned servers exceed the server budget, or a single-tier limit (connection count, port range) |

Name the **one** that is reached soonest at the stated growth, the load or the date at
which it binds, and one line on why the other four have more headroom. That line is the
handoff: a store ceiling → `data-tier-operations`; an overload / defense question →
`resilience-strategy`; the dollar consequence → `technical-cost-decision`.

---

## Sanity checks

Run these before reporting:

- **Order-of-magnitude smell test.** A per-user number should be human-plausible: a person
  does not generate 10 GB of text a day. A global system is not 100 Tbps unless it is a
  video CDN. If a result is absurd, an assumption is wrong or a unit slipped.
- **Reads vs writes.** For a read-heavy system, egress ≫ ingress and read QPS ≫ write QPS.
  If not, re-check the R:W ratio was applied.
- **Storage vs traffic independence.** Storage is driven by writes and retention; traffic
  is driven by reads and payload size. They should not be equal unless coincidence.
- **Peak ≥ average, always.** If peak QPS came out equal to average, the peak factor was 1
  or was dropped.
- **Units carried through.** bytes vs bits (×8 for line rate), per-day vs per-second,
  per-user vs total. Write the unit next to every number.

---

## Anti-patterns (errors carried in the source notes — do not reproduce)

1. **Multiplying total traffic by DAU a second time.** The source note computes
   `Overall Traffic = DAU × (reads/day + writes/day in bytes)`, producing `~10^24 bytes`.
   DAU is *already inside* `reads/day` and `writes/day`. Total traffic in bytes is just
   `reads/day + writes/day`. This error inflates the result by ~10^7.
2. **Sizing the cache off total reads.** The source note uses
   `cache memory = reads/day × object size × 20%`. That counts every repeat read of the
   same object as a separate cached copy. The cache holds **one copy per distinct hot
   object**: `distinct hot objects × size`. Overstates the cache by 10–100×.
3. **`cores ÷ 0.5` for per-server request rate.** Fixes per-request service time at 500 ms
   and applies zero utilization headroom. Use `cores × utilization ÷ service time`, with
   service time estimated from the actual work.
4. **Dropping the retention window from storage.** Quoting storage "per month" and stopping
   there. Resident storage is `byte rate × retention period`, then × replication. A 90-day
   retention on a 20 GB/day rate is 1.8 TB resident, not 20 GB.
5. **No peak factor.** Sizing servers or bandwidth off the daily average. The system has to
   survive the busy hour, not the mean.
6. **Ignoring index / row overhead on stored size.** Treating a record as its raw field
   bytes. Real stored size is 1.3–2× that once indexes and row metadata are counted.
7. **Rounding seconds/day up to 100,000 without noticing it lowers the rate.** ~15%
   under-estimate on every QPS number. Round down (80,000) or use 86,400; always size off
   peak.
