# Resilience Framework

Work these in order once the gate in `SKILL.md` is satisfied. Each step produces a written line; the collected lines become the ADR.

## 1. Confirm the pressure and find what binds first

Restate gate item 4 as one sentence. Then judge it:

- **An overload / cascade incident** — describe the failure *order*: what saturated, what that starved, what timed out as a result. The order is the design input; resilience controls are placed to break that chain at its first link.
- **A capacity ceiling being approached** — which resource, current headroom (as a %), growth rate. Proceed; the mechanism is sized from the ceiling.
- **A hard availability commitment for critical traffic** — the class of traffic and the target. Proceed; the whole design is "insulate this class from everything else".
- **"Be resilient", "the incident action item said circuit breakers", "best practice"** → stop. Every control has a cost (dropped traffic, added latency, false-positive risk, tuning toil). Name what actually breaks, and in what order, first.

Then pin **gate item 5 — what binds first**. If the user doesn't know, the deliverable is a **load test**: ramp concurrency until the service degrades, and record which resource hit its limit (CPU %, memory, worker-pool / event-loop lag, its own downstream connection pool, a downstream 429, FDs) and at what load. Every admission limit below is set as a fraction of that number. A resilience design built without this number is guesswork.

## 2. Establish priority tiers

From gate item 6. Sort the traffic:

- **Tier 1 — critical** — must be served under all but total failure: auth, payment capture, order placement, safety-relevant calls, inbound webhooks that won't be redelivered.
- **Tier 2 — important** — degrade before dropping: core reads, search.
- **Tier 3 — sheddable** — drop first, silently if possible: recommendations, "related items", non-urgent analytics ingestion, prefetch, bulk/batch jobs, nice-to-have enrichment.

If the user says **"it's all critical"**, challenge it once: under a 5× spike with a fixed ceiling, *something* gives — either you choose what (tiering) or the system chooses randomly (uniform collapse) and takes tier-1 with it. Almost every system has analytics, recommendations, or batch work that can yield. If it truly is flat, record that and accept that shedding will be uniform and the only lever is the global limit.

Record the tiers with example traffic in each, and who owns the classification.

## 3. Set the admission controls (the front door)

These decide what gets *in*. Layer them:

1. **Per-client rate limits** — where load is attributable (gate item 7: API key, tenant, user, IP). Protects against one caller monopolising capacity and against a single abuser. Choose the algorithm from `mechanisms-and-tradeoffs.md` (token bucket for burst-tolerant, sliding window for smoothness). Set per-client ceilings well below the global one so no single client can consume it all. Usually lives at the API gateway or edge.
2. **A global admission / concurrency limit** — tied directly to gate item 5. If threads/pool exhaustion is the binding constraint, an in-process **concurrency limit** (max in-flight requests) is more direct than an RPS limit — it tracks the actual resource. Consider **adaptive concurrency** (the limit self-tunes from observed latency, like TCP congestion control) so it doesn't need constant manual retuning. Set below the load-tested breaking point with margin.
3. **Priority-aware shedding above the limit** — when admission is at its ceiling, don't reject FIFO; reject **tier 3 first, then tier 2, never tier 1**. The trigger signal is whatever binds first (queue depth, event-loop lag, concurrency count, CPU) with a threshold *and hysteresis* (turn shedding off at a lower mark than it turned on) so it doesn't oscillate.

Record: the per-client limit + key + algorithm (or "not attributable"), the global limit + what it's tied to, the shed trigger + threshold + drop order + hysteresis.

## 4. Set the dependency controls (the outbound calls)

From gate items 3 and 8. For each downstream call:

- **Timeout — always.** Every outbound call has an explicit, short timeout (informed by the dependency's p99, not its p50). A missing timeout is the single most common cause of cascade: one slow dependency holds every worker until the whole service is blocked.
- **Circuit breaker — where there's a fallback.** If gate item 8 gives a usable fallback (cache, stale, default, skip), wrap the call in a breaker: after N failures/timeouts in a window it *opens* (calls fail instantly, freeing threads and giving the dependency room to recover), periodically *half-opens* to probe, *closes* when the probe succeeds. If there's **no fallback and the call is hard-required**, a breaker only converts slow-error into fast-error — still useful to free resources and shed at the front door, but the user still fails; the real levers are capacity and tier-1 protection.
- **Retry — only with a budget, and often not at all.** Retries add load to a struggling dependency — the retry storm that turns a blip into an outage. If retrying: cap total retries to a small % of calls (a *retry budget*), use exponential backoff *with jitter*, retry only transient errors and timeouts (never 4xx, never circuit-open), and only for idempotent operations. Frequently the right answer is zero retries plus a fallback or a client-side retry on a 503.
- **Bulkhead — isolate the pools.** Give critical (tier-1) call paths their own worker pool / thread pool / connection allocation, separate from tier-2/3. Then a slow tier-3 dependency saturating its bulkhead cannot consume the workers that tier-1 needs. This is what makes "insulate critical traffic" concrete.

Record per call: timeout value, breaker (thresholds + fallback) or none, retry (budget + backoff) or none, and which paths are bulkheaded.

## 5. Design the degradation

From gate item 8, per user-visible feature. For each, the fallback when its dependency is unavailable:

- **Serve from cache / stale** — acceptable staleness stated. Hand the cache's design (layer, TTL, invalidation) to `caching-strategy`; this skill just names that stale-serve is the degradation path.
- **Default / empty** — recommendations become "popular items" or nothing; a personalisation block renders generic.
- **Skip and continue** — drop the enrichment, render the page without it, log that it was skipped.
- **Hard-required — no degradation** — checkout without payment is not a degraded checkout, it's a failed one. These features are protected by admission control and bulkheads (steps 3–4), not by a fallback.

Record the per-feature fallback, or "hard-required — protected upstream".

## 6. Decide reject vs buffer, per traffic class

From gate item 9. When a request can't be served now:

- **Reject** — return 429 (rate limited, retry later) or 503 (overloaded) with `Retry-After`; the client retries. Correct for synchronous, user-facing requests where a later result is fine and the client can hold the retry.
- **Buffer** — enqueue and process when capacity returns. Correct for work that must not be lost and doesn't need an immediate result (analytics events, webhook processing, async jobs). Needs a bounded queue with its *own* backpressure — an unbounded queue just moves the overload downstream and adds memory exhaustion as a new failure mode.
- **Serve stale** — return a known-slightly-old result immediately. Correct for reads with a staleness tolerance.

Record the choice per class. Most designs are mixed: async work buffers, user reads serve stale, user writes reject-and-retry.

## 7. Place each control

From `mechanisms-and-tradeoffs.md`'s placement table. Match each control to the layer that can actually see the signal it needs:

- **Edge / CDN / L7 LB** — coarse global rate limits, IP-based blocking, connection limits, basic request validation.
- **API gateway** — per-client / per-API-key rate limits and quotas, auth-tied limits, coarse per-route limits.
- **Service mesh** (if present) — per-service-pair concurrency limits, retries with budgets, outlier detection (breaker-like), timeouts — applied uniformly without app changes.
- **In-process (library / middleware)** — saturation-aware shedding (needs event-loop/pool visibility), per-dependency circuit breakers with real fallbacks, bulkheads, adaptive concurrency, business-priority tiering.

The rule: a control belongs where the signal it reacts to is visible. The gateway can't see your event-loop lag; your app can't efficiently rate-limit a million IPs. Real designs are layered — record which control sits where.

## 8. Metrics, calibration, and record

- **Metrics to expose** — shed rate (by tier), rejected/429 count (by client and tier), circuit-breaker state changes, queue depth and age, concurrency-limit utilisation, per-dependency timeout rate. Hand the SLI/alerting design (including "alert when tier-1 shed rate > 0" and "alert on breaker flapping") to `observability-strategy`.
- **Calibration** — the numbers (concurrency limit, rate limits, breaker thresholds, timeouts) are set from step 1's load test and then *verified under a load test that reproduces the incident shape* (the 6× spike in 2 minutes, not a gentle ramp). Untested limits are guesses that fire wrong.

Produce the recommendation block from `SKILL.md`. On approval, write the ADR using `database-architecture`'s `adr-template.md` in `docs/architecture/decisions/`. The **Revisit when** line is a concrete trigger: a shed-rate threshold on tier-2 traffic (the ceiling moved), a new hard-required dependency with no fallback, a change in peak-to-average ratio, or a breaker that flaps more than N times a week (thresholds are wrong).

Then stop. Wiring the middleware, writing the mesh policies, and tuning under load are a separate, explicitly-started step.
