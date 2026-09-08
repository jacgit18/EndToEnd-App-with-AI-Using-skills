---
name: capacity-estimation
description: An a-priori, back-of-the-envelope capacity estimate for a system that does not exist yet — turning stated assumptions into QPS (average and peak), bandwidth / egress in GB per day and peak Gbps, storage per day / per year / replicated over a retention horizon, cache working-set memory, a first-cut server count, and an explicit "what binds first" line. Use when someone says "how much storage will we need", "estimate the QPS / throughput", "how many servers", "how much bandwidth / egress", "back-of-the-envelope for X", "napkin math for this design", "will the working set fit in memory", "size this system", "capacity planning for the launch", or gives a design and asks how big it has to be. It forces the user to state the assumptions first — DAU or the traffic driver, actions per user per day by type, payload sizes, read:write ratio, peak:average ratio, retention + growth horizon, replication factor — and refuses to invent them, because stating the assumptions IS the estimation rep. It then walks storage → traffic → cache → servers and names the single ceiling that is hit soonest. Not for the dollar cost of any of those quantities (compute, storage, egress pricing, managed-service premiums) — that is `technical-cost-decision`, which consumes this skill's numbers. Not for deciding shard/replica/partition topology given the numbers — that is `data-tier-operations`. Not for a measured live bottleneck with a profile or metrics already in hand — that is `problem-solving-gates` (Rubber Duck to find a cause, Optimization for a measured-slow path); this skill is the estimate produced before the system or its telemetry exists. Hands the "what binds first" / overload-protection question to `resilience-strategy` and the volume / cardinality inputs to `observability-strategy`.
---

# Capacity Estimation

Take a system that has not been built yet and a set of assumptions about how it will be
used, and produce the first quantitative picture of its size: how many requests per second
it serves at peak, how much data it stores this year and over its retention horizon, how
much it moves over the network, how much memory a cache of the hot set needs, roughly how
many servers that implies, and — the line that makes the estimate worth doing — which of
those ceilings the system runs into first as it grows. The skill makes the user state every
assumption in their own words before any number is produced, because picking the
assumptions and defending them is the reasoning rep; the arithmetic is mechanical.

## When to use

- The user asks **how big** something has to be — "how much storage", "what QPS", "how many
  servers", "how much egress", "how much RAM for the cache".
- The user wants a **back-of-the-envelope / napkin / order-of-magnitude** number for a
  design they are sketching.
- The user is **planning a launch or a scale step** and needs a target to design against
  ("we expect 2M users in year one — what does that need").
- The user has a design and asks whether it **fits** — in memory, on one node, within a
  bandwidth budget.
- The user proposes a capacity number and wants it **checked** ("I figure ~500 GB a month,
  does that sound right").

## Out of scope — hand these off

- **The dollar cost** of the compute, storage, egress, or managed services the estimate
  implies — instance pricing, per-GB storage, egress tariffs, per-request / per-token API
  pricing, managed-service premiums, build-vs-buy → `technical-cost-decision`. This skill
  produces the physical quantities (QPS, GB/day, Gbps, server count); that skill turns them
  into a monthly bill and finds the dominant line item. Chain them: estimate here, price
  there.
- **Distribution topology given the numbers** — read replicas, single- vs multi-leader,
  partitioning vs sharding, the shard-key choice, connection pooling, isolation level →
  `data-tier-operations`. This skill may conclude "read QPS on the primary store binds
  first"; that skill decides what topology relieves it.
- **A measured, live bottleneck** — "this endpoint is slow and here is the profile", "p99
  latency regressed", "replica lag is climbing" → `problem-solving-gates` (Rubber Duck for
  an unexplained failure, Optimization when a profile or query plan is already in hand).
  Capacity estimation is explicitly the *before* picture: no running system, no telemetry,
  no profile — just assumptions.
- **What the system does when a ceiling is reached** — priority-aware load shedding, rate
  limits, concurrency limits, circuit breakers, graceful degradation → `resilience-strategy`.
  This skill names *which* resource binds first and at *what* load; that skill decides how
  the system defends that resource. Hand off the "what binds first" line.
- **What to measure once it is running** — the SLIs, the metric label cardinality budget,
  the log volume, sampling → `observability-strategy`, which takes this skill's request and
  event volumes as an input.
- **Precise sizing** — the estimate is an order-of-magnitude floor. The real numbers come
  from a load test against a built system. The skill says so and stops.
- **Scoping a brand-new system that has no scope statement yet** — when the user asks for
  the sizing half of a system whose purpose, functional boundaries, and constraints are not
  yet established → `design-scoping` first, which sequences back here as its first
  specialist step. This skill needs the usage assumptions; `design-scoping` is where the
  system gets defined enough to state them.

---

## The gate

Before producing any number, these must be stated. **Do not invent them.** If any is
missing, name it and stop — a made-up assumption produces a made-up estimate that then gets
designed against as if it were real.

**Facts you may surface from the repo / design doc** (state them for confirmation):

1. **The system and the workload shape** — what is being built, and the handful of
   operations that dominate its load (the writes that create stored data, the reads that
   dominate traffic). Ignore the long tail; an estimate is built from the 2–4 operations
   that move the needle.
2. **Any given numbers** — a target user count, a launch date, a retention requirement, a
   bandwidth or memory budget already written down.

**Judgment calls that must come from the user, in their own words:**

3. **The traffic driver** — DAU (daily active users) is the usual one; state it as a round,
   easy number. If the load is not user-driven, the equivalent: events ingested per day,
   devices reporting, jobs enqueued, requests per day from a partner. One primary driver.
4. **Actions per user (or per driver) per day, by type** — how many times a day the average
   user performs each dominant operation. Split writes from reads. "Posts 2 photos, scrolls
   past 300" — not "uses the app a lot".
5. **Payload sizes, by type** — the bytes of what gets *stored* per write (a record, a row,
   an object) and what gets *returned* per read (one object, a page of N). Include a
   realistic size, not the text-only size — a "comment" is not 40 bytes once you count IDs,
   timestamps, and indexes. The request (ingress) size is also needed, but it is optional
   when the read:write ratio is above ~10:1 — ingress is noise next to egress there, so a
   rough "≈ stored size" is fine and does not hold the gate.
6. **Read:write ratio** — the whole-system ratio of read operations to write operations.
   Most systems are read-heavy (10:1 to 1000:1); a few (telemetry ingest, logging,
   event capture) are write-heavy. State which, with a number.
7. **Peak:average ratio** — how much higher the busiest window runs than the daily average,
   and when that window is (evening, business hours, a scheduled event, a launch spike).
   Common range 2×–10×; a viral or event-driven system can be far higher. Every capacity
   number is sized off the **peak**, so this ratio is load-bearing.
8. **Retention and growth horizon** — how long data is kept (30 days / 1 year / 7 years /
   forever), and how the driver grows over that horizon (flat, linear to N×, doubling
   yearly). Storage is `rate × time`, so both the rate *and* the time window are needed.
9. **Replication factor** — how many copies of stored data are kept for durability and
   availability (typically 3; sometimes 2, or 5 across regions). Multiplies the storage
   number and, if the read path fans out, affects the server count.

"Estimate the storage for a chat app" with items 3–9 absent is not valid input. The reply
is the list of what is missing, phrased as the assumptions the user needs to commit to.

**Partially-missing inputs.** If one dominant operation the user stated is really two for
sizing purposes (a "post or comment" that stores at different sizes), or a sub-split inside
a stated number is unspecified, judge by what it feeds: if it only moves a **non-binding**
quantity, assume a value, flag it inline, and proceed; block only when the missing piece
feeds a **candidate binding ceiling** (the thing that might turn out to be "what binds
first"). Don't hold the whole gate for a number that changes nothing that matters.

**Pressure does not open the gate.** "Just give me a rough number", "ballpark it", "I don't
know the exact figures, guess" are requests to skip the rep. The correct fast path is items
3–9 as one sentence each — a round DAU, actions per day, a payload size, a ratio, a peak
factor, a horizon, a replication factor — not Claude inventing seven numbers the user will
then treat as analysis.

---

## Challenge a proposed number

If the user opens with an estimate already in hand, put their assumptions under the gate,
then check the arithmetic and the method against `estimation-method.md`:

- **"about X GB per month"** — derived from write volume only? Reads do not add stored
  bytes. Does X include replication (×3) and the index / row-overhead multiplier (~1.3–2×
  raw field bytes)? Is it `rate × retention`, or just one month with no horizon?
- **"we'll need N servers"** — N from peak QPS or average? Peak is the one that has to be
  survived. Is per-server capacity `cores × utilization ÷ per-request service time`, or the
  cores-over-a-constant shortcut (which ignores utilization headroom and assumes a fixed
  service time)? Does N include redundancy for node / AZ loss?
- **"it'll fit in memory / one Redis node"** — is the working set `distinct hot objects ×
  size`, or `reads/day × size`? The second double-counts every repeat read of the same
  object and overstates the cache by 10–100×. The cache holds one copy per hot object.
- **"total traffic = users × (reads + writes)"** — DAU is already inside reads/day and
  writes/day. Multiplying by the user count a second time is a common error that inflates
  traffic by ~10^7. Total traffic in bytes is just `reads/day + writes/day`, each already
  `driver × actions × size`.
- **"peak is roughly average"** — almost never. A flat profile is a claim about the user
  base (a global system with no timezone concentration, or machine-driven steady load);
  challenge it, because a 1× peak factor under-sizes everything.

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `estimation-method.md` in order once the gate is satisfied. The walk order is
**storage → traffic → cache → servers → what binds first**, because each stage feeds the
next: stored-object counts and sizes drive the cache working set; the read rate drives both
egress and the server count; and the four ceilings are only comparable once all four are
computed.

In short: fix the base rates (writes/day, reads/day, then average and peak QPS per type) →
**storage** (`write bytes/day × retention × growth × replication`, with the overhead
multiplier) → **traffic** (egress = `reads/day × response size`; ingress = `writes/day ×
request size`; peak Gbps from the peak factor) → **cache** (`distinct hot objects × size`,
hot set from the 80/20 rule or a recent-writes window) → **servers** (`peak QPS ÷ (cores ×
utilization ÷ service time)`, then redundancy) → **what binds first** (line up storage-growth
vs disk, peak read QPS vs per-node capacity, peak egress vs uplink, working set vs
affordable RAM, peak compute QPS vs server budget; name the one hit soonest).

Reference files:

- `estimation-method.md` — the cleaned-up method: the byte and time-conversion tables (and
  why powers of 10, not 2, for an estimate), the per-stage formulas with the corrections
  applied, the overhead and redundancy multipliers, the sanity-check rules, and the
  anti-patterns (the errors carried in the source notes: multiplying traffic by DAU twice,
  sizing the cache off total reads, cores-over-a-constant server math, ignoring the peak
  factor).
- `worked-examples.md` — three estimates worked end to end from their assumptions: a
  read-heavy social feed (binds on read QPS / cache), a media-streaming service (binds on
  egress bandwidth), and a write-heavy telemetry pipeline (binds on storage growth). Each
  shows the walk order and the "what binds first" reasoning.

---

## Output

**1. In chat, an estimate block:**

```
Assumptions:        DAU <n> · actions/user/day <writes: … / reads: …> · sizes <stored/write, returned/read> · R:W <ratio> · peak:avg <ratio, window> · retention <period> + growth <shape> · replication <factor>
Base rates:         writes/day <n> · reads/day <n> · avg QPS <write / read> · peak QPS <write / read>
Storage:            <GB/day> · <TB/year> · <TB over horizon, expected & end-state> · <× replication = TB>
Traffic:            egress <GB/day, peak Gbps> · ingress <GB/day, peak Gbps> · <note on CDN-offloadable fraction>
Cache:              working set <n hot objects × size = GB> · +overhead <GB> · <replicated? y/n>
Servers:            per-server capacity <req/s, from cores×util÷service-time> · peak / capacity = <n> · × redundancy = <n> (compute tier)
What binds first:   <the single ceiling hit soonest — resource, the load/date it binds at, and why the other three have more headroom>
Confidence:         <which 1–2 assumptions the result is most sensitive to; what a load test would pin down>
Follow-ups:         dollar sizing → technical-cost-decision · <if a store binds> topology → data-tier-operations · defending the binding resource → resilience-strategy · request/event volume → observability-strategy
```

**2. On approval**, if the estimate is going to be designed against (not a throwaway),
write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `database-architecture`'s
`adr-template.md` (same directory and numbering). The **Decision** section records the
committed assumptions and the resulting targets; **Revisit when** is the concrete trigger
that invalidates the estimate — "DAU exceeds <n> (rerun)", "the peak:average ratio moves
past <r>", "a new dominant operation is added", "retention requirement changes",
"measured production numbers land more than 2× off this estimate". A quick napkin number
for a discussion does not need an ADR; say so.

Then stop. Choosing the store topology, pricing the bill, and designing the overload
defense are separate, explicitly-started steps.

---

## Escape hatch

If the user has genuinely done the estimate — every assumption stated and defended, the
walk order followed, the arithmetic shown — and wants a review or a second opinion rather
than a Socratic pass, they say so and you check their numbers directly against
`estimation-method.md` and give a verdict. Opt-in, not the default.

---

## Example invocations

> "Photo-sharing app. ~5M DAU, each uploads 2 photos/day at ~3 MB after compression and
> views ~200 photos/day. Keep photos forever. Expecting to grow to ~15M DAU over 3 years.
> Store 3 copies. Reads are served from a CDN but I want the origin numbers. Peak is about
> 3× average, in the evening."

Gate satisfied. Base rates: writes 10M/day (~115/s avg, ~350/s peak); reads 1B/day
(~11.6K/s avg, ~35K/s peak). Storage: 10M × 3 MB = 30 TB/day of originals; ×~1.4 for
thumbnails and metadata ≈ 42 TB/day; over 3 years with linear growth to 3× DAU, expected
multiplier ~2 → ~92 PB, end-state ceiling ~138 PB; × 3 replication → ~275–415 PB. Traffic:
origin egress if the CDN offloads 95% of the 1B reads/day at 300 KB each ≈ 15 TB/day to
edge, peak ~4 Gbps origin fill; user-facing edge egress ~300 TB/day. Cache/CDN working set:
hot 20% of ~30 days of uploads ≈ 180M objects × 300 KB ≈ 54 TB across the CDN. Servers: the
upload tier is I/O-bound on object storage, not CPU — a handful; the metadata/API tier
sized off 35K/s peak reads. **What binds first: storage growth** — tens of PB per year,
compounding, is the ceiling that arrives first and hardest; read QPS and egress are large
but flat per-user and CDN-absorbed. Follow-ups: storage cost → technical-cost-decision;
object-store tiering / lifecycle → data-tier-operations.

> "Roughly how much storage and bandwidth does a Twitter-like service need?"

Gate not satisfied — items 3–9 all absent. Response: this needs assumptions before it can
produce a number, and choosing them is the exercise. Ask for: DAU (a round number);
tweets posted per user per day and timeline reads per user per day; bytes stored per tweet
(with IDs, media pointers, indexes) and bytes returned per timeline page; the read:write
ratio; the peak:average ratio and when peak is; how long tweets are retained and how fast
the user base grows; the replication factor. Do not fill any of these in.

> "I estimated our event pipeline at about 200 GB/month. Sanity-check me: 50M events/day,
> 400 bytes each, kept 90 days."

Escape hatch — they did the rep. Check it: 50M × 400 B = 20 GB/day raw. Over 90 days
retention = 1.8 TB resident, not 200 GB — the "/month" framing dropped the retention
window. Add index/overhead ~1.5× → ~2.7 TB, × replication 3 → ~8 TB provisioned. Their
per-day figure is right; the resident total is ~9× their number because retention wasn't
multiplied through. No peak factor needed for storage, but the ingest tier should be sized
off peak events/s, not the 580/s average.

---

## Portability

Repo-agnostic. Writes an ADR to `docs/architecture/decisions/` only when the estimate will
be designed against, reusing `database-architecture`'s `adr-template.md`. Copy the
`capacity-estimation/` directory into another repo's `.claude/skills/` to use it there. See
`README.md` for where it sits among the sibling skills.
