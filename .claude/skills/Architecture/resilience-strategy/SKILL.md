---
name: resilience-strategy
description: A gated decision for how a service or request path protects itself under overload and dependency failure — load shedding with priority tiers, rate limiting (per-client vs global, token-bucket / sliding-window), concurrency limiting and backpressure, circuit breakers on outbound calls, timeout + retry-budget + backoff-with-jitter policy, bulkhead / pool isolation, and graceful degradation with fallbacks — plus where each control sits (edge / API gateway / service mesh / in-process). Use when someone says "we need rate limiting", "add a circuit breaker", "the service falls over under load", "a slow dependency took everything down", "one noisy client starved everyone", "how do we degrade gracefully", "we need backpressure", "load shedding", or proposes a resilience mechanism and wants it checked. It forces the user to state the triggering incident or capacity ceiling, what resource binds first, the priority tiers of the traffic, the client model, and the downstream dependencies before any mechanism is recommended, then records the outcome as an ADR. Not for detecting or alerting on overload — that is `observability-strategy`, whose SLIs this skill consumes. Not for scaling the datastore (replicas, sharding, DB connection pooling) — that is `data-tier-operations`. Not for the cache design itself, including a cache-key stampede / thundering herd on key expiry — that is `caching-strategy`; though "fall back to a cached response" is a degradation mechanism this skill names. Not for diagnosing one endpoint that fell over last night — that is `problem-solving-gates` (Rubber Duck). Not for whether a service mesh exists at all — that is `service-mesh-adoption`; this skill assumes a mesh's presence or absence as a given fact and only decides what runs where once that's settled.
---

# Resilience Strategy

Take a service or a request path that is at risk of being overwhelmed — a traffic spike that took it down, a slow dependency that exhausted its threads, a single client that starved everyone else, or a capacity ceiling it is approaching — and decide how it defends itself: what it drops first when it can't serve everything, how it caps load per client and in aggregate, how it stops a failing dependency from taking it with it, what it returns when it can't do the real thing, and where each of those controls lives. The skill makes the user name the concrete pressure and what actually breaks first before any mechanism is on the table, recommends a coherent set, and writes an ADR.

## When to use

- The user reports an **overload or cascade incident** — "a spike took us down", "a downstream slowdown exhausted our connection pool and everything backed up", "one tenant's batch job starved the API", "retries made the outage worse".
- The user asks for a **specific mechanism** — "add rate limiting", "we need a circuit breaker", "load shedding", "backpressure on the queue", "bulkheads".
- The user is **approaching a known ceiling** — "we're at 70% of the downstream's quota", "connection count is climbing toward the limit", "peak is 3× average and growing".
- The user asks how to **degrade** — "what should we do when the recommendations service is down", "how do we stay up if the DB is slow", "graceful degradation".
- The user has a **hard availability target for critical traffic** and needs to protect it from the rest.
- The user proposes a resilience approach and wants it pressure-tested ("we'll retry 3× on every failure", "rate-limit everyone to 100 rps").

## Out of scope — hand these off

- **Detecting overload, and what to alert on** — the SLIs that define "critical traffic healthy", how load and saturation are measured, paging vs ticketing, alerting on false-positive shedding → `observability-strategy`. This skill *consumes* those SLIs (they define what the shed/degraded path must protect) and names the metrics a resilience control needs; it doesn't design the telemetry.
- **Scaling the datastore** — read replicas, partitioning, sharding, DB connection pooling and pooler placement, DB failover / RPO / RTO → `data-tier-operations`. Overlap point: "DB connections exhausted" — that skill adds a pooler; this skill adds a concurrency limit *upstream* so the service sheds before the pool is drained. Both, not either.
- **The cache design** — which layer, cache-aside vs write-through, TTL vs invalidation, eviction, and cache-specific overload (stampede / penetration / avalanche) → `caching-strategy`. This skill names "serve a cached or stale response" as a degradation fallback and hands the cache's design there.
- **Adding capacity instead of shedding it** — horizontal autoscaling policy, provisioned headroom, right-sizing. This skill frames the *shed-vs-scale* choice (shedding is the floor that protects you between the spike and the scale-up; autoscaling is the complement) but the HPA/ASG tuning is implementation, and the cost of headroom → `technical-cost-decision`.
- **Diagnosing one specific failure** — "why did this endpoint fall over at 2am" with a hypothesis → `problem-solving-gates` (Rubber Duck). This skill decides what protection should exist so the next spike is survivable; it doesn't run the post-incident investigation.
- **Projecting the ceiling and the date for a system with no instrumentation yet** — turning growth assumptions ("peak is 4× average and climbing") into which resource binds first and roughly when → `capacity-estimation`. This skill takes a *named, measured or estimated* binding resource (gate item 5) and designs the defense; it does not run the a-priori forward projection when there is no telemetry to read.
- **A proactive pass over the whole design for every way it can fail** — enumerating and ranking the failure surface before sign-off, across all nine categories, not one named pressure → `failure-mode-analysis`. This skill takes one concrete pressure — an incident, a ceiling, a hard commitment — often *from* that register's dependency / overload / cascade rows, and designs the defense for it.
- **Implementation** — the middleware, the mesh policy YAML, the circuit-breaker library wiring, tuning the actual numbers under load test. The skill stops at the ADR.

---

## The gate

Before recommending any mechanism, limit, or placement, these must be answered.

**Facts you may surface from the repo / infra** (state them for confirmation):

1. **The service(s) and request path** — what handles the traffic, its runtime/concurrency model (thread-per-request, async event loop, worker pool), and where it sits (behind an LB / API gateway / service mesh / direct).
2. **Existing controls** — any rate limiting, timeouts, retries, circuit breakers, queue limits, or bulkheads already in place, and where they're configured (edge, gateway, mesh, in-app library).
3. **The downstream calls** — the services, databases, and third-party APIs this path depends on, as far as the code shows, with any known timeouts/quotas.

**Judgment calls that must come from the user, in their own words.** Do not invent these; do not design without them. If any is missing, name it and stop:

4. **The pressure** — the concrete triggering event, not a wish. One of: a specific overload/cascade incident (what happened, what fell over, in what order), a capacity ceiling being approached (which resource, current headroom, growth), or a hard availability commitment for a defined class of critical traffic that must be insulated from the rest. "We should be resilient", "best practice", "the SRE book says circuit breakers" is **not** a pressure — it is a reason to stop.
5. **What binds first** — under increasing load, which resource is exhausted first and where the service falls over: CPU, memory, worker threads / event-loop lag, its own connection pool to a downstream, a downstream's rate quota, file descriptors. A number if there is one ("falls over around 900 concurrent requests", "the payment API 429s us above 50 rps"). If `reliability-math` already computed this from live telemetry (utilization against the collapse curve, a Little's Law concurrency figure), use that number rather than re-deriving it. If unknown and unmeasured, the first task is a load test to find it, not a mechanism.
6. **Priority tiers** — which traffic is critical and must be served even under severe load (checkout, auth, payment webhooks), which is important, and which is sheddable (recommendations, related-items, analytics ingestion, non-urgent bulk jobs). Who decides the tiering. "It's all equally important" is an answer — and it means shedding degrades everyone uniformly, which is a weaker position; challenge it.
7. **Client model** — few known callers or many anonymous ones; trusted internal vs untrusted public; can load be attributed to a client (API key, tenant ID, user, IP) for per-client limits, or only shed in aggregate. Is there a known abuser pattern or is it organic growth.
8. **Downstream dependency behaviour** — for each call in fact 3: its failure mode (slow / errors / times out / returns garbage), its latency profile (p50/p99), and whether this path has a usable fallback when it's unavailable (a cache, a stale copy, a default, a degraded response, skip-and-continue) or it's hard-required (no payment service → no checkout, full stop).
9. **Semantics of the shed / degraded path** — when a request is shed or a feature degraded, is it acceptable to drop it (return 429/503, client retries later), to serve stale/partial, or must it be *accepted and processed later* (enqueue, async). Per traffic class. This decides whether the answer is "reject" or "buffer".
10. **Operational capacity** — who tunes and owns the limits, who watches for shedding that's firing when it shouldn't (false positives cost real traffic), whether there's a load-test setup to calibrate the numbers, and who's on call when a breaker trips.

"The service falls over under load, add rate limiting" with items 4–10 absent is not valid input.

**Pressure does not open the gate.** "We're going viral next week", "the incident review action item says add circuit breakers", "just give me a sensible rate limit" are reasons the user wants the gate skipped. Under real time pressure the fastest correct move is still items 4–10 in one sentence each, because a rate limit set without knowing what binds first (item 5) or the priority tiers (item 6) either fires far too late to help or sheds the checkout traffic you needed to keep.

---

## Challenge a proposed approach

If the user opens with the mechanism already chosen, put their reasoning under the gate, then test the specific claim against `mechanisms-and-tradeoffs.md`:

- **"add rate limiting"** — at what value, and derived from what (item 5's ceiling, with margin)? Per client or global (item 7)? What does a limited request get — a 429 to retry (item 9), a queue slot, or a degraded response? A global limit set above your breaking point does nothing; one set blindly low sheds good traffic. Where does it run — edge, gateway, in-app?
- **"circuit breaker on everything"** — which downstream, and what does an *open* breaker return (item 8's fallback)? A breaker with no fallback just converts "slow" into "fast failure" — sometimes that's the point (fail fast, free the thread), but if there's no degraded path the user still gets an error. What are the open threshold, the half-open probe, and the reset? Breakers on calls that have no fallback and are hard-required need a different answer (capacity, or shed at the front door).
- **"retry on failure"** — retries multiply load on an already-struggling dependency; this is how a blip becomes an outage. Is there a retry *budget* (cap retries to a small % of total calls)? Exponential backoff *with jitter*? Are the operations idempotent? Retry only on transient/timeout, never on a 4xx or a circuit-open. Often the right number of retries is zero and the fix is a fallback.
- **"load shedding"** — shed *what*, based on *what* signal? Priority-aware (item 6: drop tier-3 first) beats uniform. The trigger: a queue-depth threshold, event-loop lag, CPU, a concurrency count, or an explicit health check. What does a shed request receive (item 9)? And what turns shedding *off* — the same threshold with hysteresis, or does it oscillate?
- **"we'll just autoscale"** — autoscaling adds capacity in minutes; a spike arrives in seconds. What protects the service in the gap, and what protects you when the thing you can't scale (a third-party quota, a licensed DB) is the ceiling? Shedding is the floor; autoscaling is the complement, not the substitute.
- **"put it all in the API gateway"** — the gateway is right for coarse per-client rate limits and auth-tied quotas. It can't see your event-loop lag or your downstream pool saturation — those need in-process concurrency limits and breakers. Most real designs are layered: gateway for per-client, in-app for saturation-aware shedding and per-dependency breakers.

Flag the load-bearing assumption as a question, not a correction.

---

## The process

Work `resilience-framework.md` in order once the gate is satisfied. In short: confirm the pressure is real and find what binds first (load test if unknown) → establish the priority tiers, or challenge "it's all critical" → set the **admission** controls: per-client rate limits where load is attributable, a global concurrency/admission limit tied to what binds first, priority-aware shedding above it → set the **dependency** controls: a timeout on every outbound call, circuit breakers where there's a fallback, a retry budget with jittered backoff only where safe, bulkheads to stop one slow dependency consuming all workers → design the **degradation**: per feature, what the fallback is (cache, stale, default, skip) or that it's hard-required → decide **reject vs buffer** per traffic class → place each control (edge / gateway / mesh / in-process) → name the metrics and the calibration plan → recommend and record.

Reference files:

- `mechanisms-and-tradeoffs.md` — each mechanism (load shedding, rate limiting and its algorithms, concurrency limiting / adaptive concurrency, queue + backpressure, circuit breaker states, timeout + retry budget + backoff/jitter, bulkhead, graceful degradation): what it protects, what it costs, its failure mode, and where it belongs in the stack. The shed-vs-scale framing. The retry-storm and thundering-herd anti-patterns. A placement table (edge / API gateway / service mesh / in-process).
- `resilience-framework.md` — the 8-step process, worked once the gate is satisfied.

---

## Output

**1. In chat, a recommendation block:**

```
Pressure:            <the overload/cascade incident or capacity ceiling from gate item 4>
Binds first:         <the resource that's exhausted first, and at what load — from gate item 5>
Priority tiers:      <critical / important / sheddable — with example traffic in each, or "flat — challenged, accepted">
Admission controls:  per-client <limit + key + algorithm, or "n/a — not attributable">; global <concurrency/admission limit tied to what binds first>; shedding <trigger signal + threshold + what's dropped first + hysteresis>
Dependency controls: timeouts <per call>; circuit breakers <on which calls — open/half-open/reset — and the fallback each returns>; retries <budget + backoff/jitter + which errors only, or "none">; bulkheads <which pools isolated>
Degradation:         <per feature: fallback = cache / stale / default / skip — or "hard-required, protected by admission control">
Reject vs buffer:    <per traffic class: 429/503-and-retry | enqueue-and-process-later | serve-stale>
Placement:           <edge: … | API gateway: … | service mesh: … | in-process: …>
Shed vs scale:       <what shedding covers in the gap; whether autoscaling is the complement; the ceiling that can't be scaled>
Metrics & calibration: <the signals to watch (shed rate, breaker state, queue depth, rejected-by-tier); how the numbers get load-tested>
Tradeoffs accepted:  <2–4 concrete costs: dropped sheddable traffic, added latency from queueing, false-positive shed risk, breaker-flap risk, tuning toil>
Not chosen because:  <one line per rejected mechanism>
Follow-ups:          <SLIs for the protected path → observability-strategy; cache fallback design → caching-strategy; headroom cost → technical-cost-decision>
```

**2. On approval**, write an ADR to `docs/architecture/decisions/NNN-<slug>.md` using `database-architecture`'s `adr-template.md` (same directory and numbering — this is an architecture decision). Reference any related `observability-strategy`, `data-tier-operations`, or `microservices-decision` ADR. Fill "Revisit when" with the concrete trigger that reopens this — "sustained shed rate on tier-2 traffic exceeds X% (the ceiling moved, re-tune or add capacity)", "a new hard-required downstream is added with no fallback", "peak-to-average ratio changes", "a breaker flaps more than N times a week (thresholds wrong)".

Then stop. Implementation — the middleware, the mesh policies, the breaker wiring, the load-test calibration — is a separate, explicitly-started step.

---

## Escape hatch

If the user has genuinely worked this — the pressure named, what binds first measured, priority tiers set, mechanisms chosen against real downstream behaviour, reject-vs-buffer decided per class — and wants a review or a tie-break rather than a Socratic pass, they say so and you give a direct recommendation with reasoning. Opt-in, not a default.

---

## Example invocations

> "Checkout API, Go, behind an ALB, no mesh. Last Black Friday a marketing email drove a 6× spike in 2 minutes; the service hit ~1200 concurrent requests, the Postgres connection pool (max 100) was exhausted, and *everything* — including payment callbacks — started timing out. We autoscale but it takes ~3 min to add pods. Critical: card-payment webhooks and the final 'place order' call. Sheddable: cart recommendations, 'you might also like', saving analytics events. Clients are our own web and mobile apps plus Stripe webhooks — all attributable by API key. Downstreams: Postgres (hard-required for order placement), a recommendations service (has a cached fallback), Stripe (hard-required for payment, but webhooks are retried by Stripe for 3 days). Dropping a recommendation is fine; a dropped 'place order' must come back as a 503 the app retries. One SRE owns this, we have a k6 load-test rig."

Gate satisfied. Framework: binds first = the Postgres pool at ~100. Tiers given. Admission: in-process **adaptive concurrency limit** on the handler set from the load-tested ceiling (~800, below the 1200 that broke it), with **priority-aware shedding** above it — drop tier-3 (recs, analytics) first, then tier-2, never tier-1 (payment webhooks, place-order); shed response is 503 + `Retry-After` for place-order, silent skip for recs. Per-client rate limit at the ALB/gateway on the web and mobile keys (not on Stripe's) as a coarse outer guard. Dependency: 2s timeout on Postgres calls, 500ms on recommendations with a circuit breaker → cached fallback when open; **no retries** to Postgres (idempotency isn't there and retries would deepen pool exhaustion) — rely on the client's 503 retry; Stripe calls get 1 retry with jittered backoff. **Bulkhead**: a separate small worker pool + DB connection allocation reserved for payment-webhook and place-order handlers so recommendation load can't touch it. Degradation: recs → cached or empty; analytics → drop; order path → no degradation, protected by the bulkhead + concurrency limit. Buffer vs reject: analytics events enqueue (already async); everything else rejects. Placement: per-client limits at the gateway; concurrency limit, shedding, breakers, bulkhead in-process. Shed-vs-scale: shedding holds the line for the ~3 min until pods scale; the un-scalable ceiling is the Postgres pool — raising it needs `data-tier-operations`. Metrics: shed rate by tier, breaker state, pool utilisation, 503s on the order path → `observability-strategy`. ADR; Revisit when tier-2 shedding becomes routine at peak, or the pool ceiling is raised.

> "We should add rate limiting and circuit breakers before we scale up marketing."

Gate not satisfied — item 4 (no incident or measured ceiling — "before marketing" is a schedule), item 5 (what binds first is unknown), item 6 (no priority tiers). Response: name what's missing, note that a rate limit set without knowing the breaking point either fires too late or sheds traffic you needed, and ask for either the last overload incident's failure order or a load test to find the ceiling, plus which traffic is critical vs sheddable. Do not recommend a limit or a mechanism set.

---

## Portability

Repo-agnostic. Reads and writes `docs/architecture/decisions/` alongside the other architecture skills, reusing `database-architecture`'s `adr-template.md`. Copy the `resilience-strategy/` directory into another repo's `.claude/skills/` to use it there. See `README.md` for where it sits among the sibling skills.
