# resilience-strategy skill

A gated decision for **how a service or request path protects itself under overload and
dependency failure** — load shedding with priority tiers, rate limiting, concurrency limiting
and backpressure, circuit breakers, timeout / retry-budget / backoff policy, bulkheads, and
graceful degradation — plus where each control sits (edge / gateway / mesh / in-process). Not
detecting or alerting on overload (that's `observability-strategy`), not scaling the datastore
(that's `data-tier-operations`), not the cache design (that's `caching-strategy`), not
diagnosing one endpoint that fell over last night (that's `problem-solving-gates`).

Built from the `Architecture/02. Backing Service Options/` notes — `Load Shedding.md`
(priority dropping, dynamic thresholds, graceful degradation, fallbacks), `Load Shedding
Implementation.md` (traffic managers, gateways, service meshes, queueing systems, custom
logic), `Load Balancer.md` (L4/L7, where shedding and limiting attach) — plus `Rate
Limiting.md`, `Fault Tolerance.md`, and `Chaos Engineering.md`.

## Where it sits

```
microservices-decision   →  how many services, where the boundaries are
observability-strategy    →  the SLIs that define "critical traffic healthy" + alerting
reliability-math          →  quantifies a pressure from live telemetry (utilization vs. the
                             collapse curve, a Little's Law concurrency figure) — this
                             skill's item-5 "what binds first," when it's already computed
resilience-strategy       →  what the path DOES under load — shed / limit / break / degrade   (this skill)  → ADR
data-tier-operations      →  scaling the store behind it (replicas, sharding, DB pooling)
caching-strategy          →  the cache a degraded path falls back to
technical-cost-decision   →  the dollar cost of capacity headroom
service-mesh-adoption      →  whether a service mesh exists at all (this skill assumes that
                             answer as given when it lists "service mesh" as a placement)
```

`resilience-strategy` **consumes** the SLIs from `observability-strategy` (they define what
the shed/degraded path must protect) and the service topology from `microservices-decision`.
It **pairs** with `observability-strategy`: that skill decides how you *see* overload, this
one decides what you *do* about it.

## The shape

A gate skill. It refuses to recommend a mechanism until the user supplies:

- **a real pressure** — an overload/cascade incident, a capacity ceiling being approached, or
  a hard availability target for critical traffic — never "best practice" or "the SRE book"
- **what binds first** — the resource that exhausts first and at what load (load-test it if unknown)
- **priority tiers** — critical / important / sheddable, or an explicit (challenged) "it's all flat"
- **the client model** — attributable per-client or aggregate-only; trusted vs public
- **downstream dependency behaviour** — failure mode, latency, and whether each has a usable fallback
- **reject vs buffer semantics** per traffic class
- **operational capacity** — who tunes the limits, who watches for false-positive shedding

Then it layers admission controls (per-client limits → global concurrency limit → priority
shedding), dependency controls (timeouts → breakers with fallbacks → retry budgets →
bulkheads), and a per-feature degradation plan, and places each control where its signal is visible.

## Files

| File | Role |
|---|---|
| `SKILL.md` | Entry point. The gate (items 4–10 from the user), challenge-the-proposal, output contract. |
| `resilience-framework.md` | The 8-step process — pressure + what binds first → priority tiers → admission controls → dependency controls → degradation → reject vs buffer → placement → metrics & calibration. |
| `mechanisms-and-tradeoffs.md` | Each mechanism (shedding, rate limiting + algorithms, concurrency / adaptive, queue + backpressure, circuit breaker, timeout/retry/jitter, bulkhead, graceful degradation) — what it protects, costs, failure mode. The shed-vs-scale framing. Retry-storm / thundering-herd anti-patterns. A placement table. |

## Output

1. A recommendation block in chat (pressure, what binds first, priority tiers, admission
   controls, dependency controls, degradation plan, reject vs buffer, placement, shed-vs-scale,
   metrics & calibration, tradeoffs, follow-ups).
2. On approval: an ADR in `docs/architecture/decisions/` reusing `database-architecture`'s
   `adr-template.md`. "Revisit when" must be a concrete trigger (tier-2 shed rate exceeds X%,
   a new hard-required dependency with no fallback, peak-to-average ratio changes, a breaker
   flapping more than N/week).

Stops before implementation (middleware, mesh policy YAML, breaker wiring, load-test calibration).

## Interaction with sibling skills

- **Pairs with `observability-strategy`** — that skill defines the SLI for "critical traffic
  healthy" and the alerting (including alert-on-false-positive-shedding); this skill decides
  what the path does to keep that SLI green. "We can't tell we're overloaded" → observability;
  "we can tell, what do we do" → here. Reciprocal boundary note added there.
- **Distinct from `data-tier-operations`** — that skill owns DB replicas / sharding / pooler
  placement / DB failover; this skill owns app-level concurrency limits, breakers on outbound
  calls (including to the DB), and bulkheads. Overlap at "DB connections exhausted": pooler
  (there) *and* an upstream concurrency limit so you shed before the pool drains (here).
  Reciprocal note added there.
- **Defers to `caching-strategy`** — "serve a stale/cached response" is a degradation fallback
  this skill names; the cache's layer / TTL / invalidation / stampede handling is designed
  there. Reciprocal note added there.
- **Frames shed-vs-scale** — names autoscaling as the complement to shedding; the HPA/ASG
  tuning is implementation and the headroom cost → `technical-cost-decision`.
- **Defers to `problem-solving-gates`** (Rubber Duck) for diagnosing one specific failure;
  this skill decides what protection should exist for the next one.
- **Consumes `microservices-decision`** — takes the service topology as given.
- **`learning-gate`** hands off here on overload-protection / resilience questions rather than
  running its own rep gate (see `learning-gate` Step 3).

Run `skill-interaction-testing` after any trigger-description change here — the overlap risk
is with `observability-strategy` (overload detection vs response), `data-tier-operations` (DB
connection exhaustion), and `caching-strategy` (stale-serve fallback).

## Using it in another repo

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside `database-architecture`
and reuses its `adr-template.md`.

```
cp -r ".claude/skills/Architecture/resilience-strategy" /path/to/other-repo/.claude/skills/
```
