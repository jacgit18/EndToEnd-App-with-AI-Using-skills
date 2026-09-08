# capacity-estimation skill

An **a-priori, back-of-the-envelope capacity estimate for a system that does not exist
yet** — stated assumptions in, and out comes QPS (average + peak), bandwidth / egress
(GB/day + peak Gbps), storage (per day / per year / replicated over a retention horizon),
cache working-set memory, a first-cut server count, and an explicit **"what binds first"**
line. Not the dollar cost of any of it (that's `technical-cost-decision`), not the shard /
replica topology given the numbers (that's `data-tier-operations`), not a measured live
bottleneck (that's `problem-solving-gates`). It is the estimate produced *before* the
system or its telemetry exists.

Built from the `Architecture/01. System Design/` notes — `Bandwidth Estimation.md`,
`Questions/Capacity Estimation.md` (DAU, storage/traffic/cache/server walk, unit tables),
`Questions/Music Streaming Service Estimation.md` — with the self-flagged arithmetic errors
in those notes (`#todo Double check calculations`) corrected in `estimation-method.md`.

## Where it sits

```
design-scoping           →  purpose, scale targets, the 1–2 features to design deep
capacity-estimation       →  the numbers those targets imply + what binds first   (this skill)  → estimate block (+ ADR if designed against)
technical-cost-decision   →  those numbers priced into a monthly bill
data-tier-operations      →  the store topology that relieves a binding store ceiling
resilience-strategy       →  how the system defends the resource that binds first
observability-strategy    →  what to measure once it's running (volume / cardinality inputs)
```

`capacity-estimation` is the quantitative front-half of an architecture pass: it produces
the physical numbers that `technical-cost-decision` prices, `data-tier-operations` designs a
topology for, and `resilience-strategy` defends. It **consumes** the scale targets from
`design-scoping` and **feeds** all three of those. It decides *how big*, not *how much it
costs*, *what topology*, or *what to do when it's full*.

## The shape

A gate skill. It refuses to produce a number until the user supplies:

- **the traffic driver** — DAU, or events/day, devices reporting, jobs/day
- **actions per driver per day, by type** — writes split from reads
- **payload sizes** — bytes stored per write, bytes returned per read
- **read:write ratio**
- **peak:average ratio** and the peak window
- **retention + growth horizon** — how long data is kept, how the driver grows
- **replication factor**

Stating and defending those seven is the estimation rep; the walk
(`storage → traffic → cache → servers → what binds first`) is mechanical arithmetic once
they exist.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The gate (items 3–9 from the user), challenge-a-proposed-number, the estimate-block output contract. |
| `estimation-method.md` | The cleaned-up method — byte / time tables (powers of 10, not 2), per-stage formulas with corrections, overhead + redundancy + growth multipliers, sanity checks, and the anti-patterns carried in the source notes (traffic × DAU twice, cache off total reads, `cores ÷ 0.5` server math, dropped retention window, no peak factor). |
| `worked-examples.md` | Three estimates worked end to end, each landing on a different binding constraint — a social feed (read QPS / cache), a media-streaming service (egress bandwidth), a telemetry pipeline (storage growth). |

## Output

1. An estimate block in chat — assumptions, base rates, storage, traffic, cache, servers,
   **what binds first**, confidence (which assumptions the result is most sensitive to),
   and follow-ups.
2. When the estimate will be designed against (not a throwaway): an ADR in
   `docs/architecture/decisions/` reusing `database-architecture`'s `adr-template.md`, with
   a concrete "Revisit when" trigger (DAU exceeds N, peak ratio moves, a new dominant
   operation, measured numbers land >2× off).

Stops before pricing, topology, and overload design.

## Interaction with sibling skills

- **Chains into `technical-cost-decision`** — this skill produces QPS / GB / Gbps / server
  count; that skill turns them into dollars and finds the dominant line item. The reciprocal
  note there scopes "sizing a system against a stated volume" to the *dollar* sizing, with
  the *physical* quantities produced here.
- **Feeds `data-tier-operations`** — when "what binds first" is a store ceiling (read QPS on
  the primary, storage growth rate), that skill picks the replica / partition / shard
  topology. It already requires a measured bottleneck or hard requirement; this skill's
  a-priori estimate is the "hard requirement" input for a system not yet built.
- **Feeds `resilience-strategy`** — the "what binds first" line is exactly that skill's
  "what binds first" gate input; it decides the shedding / limiting / degradation that
  defends that resource.
- **Feeds `observability-strategy`** — request and event volumes here are inputs to that
  skill's cardinality and retention budgeting.
- **Distinct from `problem-solving-gates` (Optimization / Rubber Duck)** — those need a
  profile or a measurement of a *running* system. This skill is pre-system, pre-telemetry,
  pre-profile. "How big should we build it" → here; "it's built and slow, here's the
  profile" → there.
- **Consumes `design-scoping`** — takes the non-functional scale targets (RPS ceiling,
  concurrency, growth) as the assumption set to estimate from.

Run `skill-interaction-testing` after any trigger-description change here — the overlap risk
is with `technical-cost-decision` (volume sizing — physical vs dollar) and
`problem-solving-gates` (a-priori estimate vs measured bottleneck).

## Using it in another repo

Repo-agnostic. Writes an ADR to `docs/architecture/decisions/` only when the estimate will
be designed against, reusing `database-architecture`'s `adr-template.md`.

```
cp -r ".claude/skills/Architecture/capacity-estimation" /path/to/other-repo/.claude/skills/
```
