# Resilience Mechanisms & Tradeoffs

Reference for `SKILL.md` and `resilience-framework.md`. Each mechanism: what it protects, what it costs, its failure mode, where it belongs.

---

## Load shedding

**What it is:** deliberately dropping or degrading a subset of work when the system can't serve all of it, to keep the rest healthy. The alternative is uniform collapse where nothing succeeds.

- **Priority-aware** (drop tier-3 first, tier-1 never) beats **uniform** (drop the next N% regardless). Requires the request to carry or imply its tier — a header, a route, a client class, an endpoint.
- **Trigger signal:** whatever binds first — queue depth, event-loop lag, active-request count, CPU, a downstream saturation signal. Prefer a signal that leads the failure (lag, queue depth) over one that lags it (error rate).
- **Hysteresis:** turn shedding *on* at threshold T_high, *off* at T_low < T_high. Without the gap it oscillates — shed, recover, shed, recover — and the flapping is its own problem.
- **Cost:** the dropped work. If tier-3 is genuinely sheddable this is nearly free; if the tiering is wrong you're dropping revenue.
- **Failure mode:** no tiering (drops critical traffic alongside the rest); trigger set so high it engages only after the service is already collapsing; no hysteresis (oscillation).
- **Where:** in-process for saturation-aware and priority-aware shedding (needs internal visibility); edge/LB for crude connection-count shedding.

## Rate limiting

**What it is:** capping the request rate, per client and/or globally, rejecting (429) or delaying excess.

| Algorithm | Behaviour | Fits |
|---|---|---|
| **Token bucket** | Refills at a steady rate, allows bursts up to the bucket size | APIs that should tolerate short bursts but bound the sustained rate |
| **Leaky bucket** | Processes at a fixed rate, queues or drops overflow | Smoothing a bursty input into a steady downstream load |
| **Fixed window** | N requests per calendar window | Simple; suffers boundary spikes (2N across a window edge) |
| **Sliding window** | N requests per rolling interval | Smoother than fixed window, slightly more state |

- **Per-client vs global:** per-client (keyed by API key / tenant / user / IP) stops one caller monopolising capacity — set well below the global limit. Global is the backstop tied to actual capacity. You usually want both.
- **Rate limit vs concurrency limit:** RPS limits assume roughly uniform request cost. If cost varies wildly, or the binding resource is threads/connections, a **concurrency limit** (max in-flight) tracks the real constraint better.
- **Cost:** rejected requests; state to track counters (in-memory per instance, or shared in Redis for a global view across a fleet).
- **Failure mode:** global limit set above the breaking point (does nothing); limit set blindly low (sheds good traffic); per-instance counters with no shared state so the effective fleet limit is N× the intended one.
- **Where:** API gateway (per-client, auth-tied), edge (per-IP), in-process (fine-grained, cost-aware).

## Concurrency limiting / adaptive concurrency

**What it is:** cap the number of requests processed simultaneously; excess is queued (briefly) or shed. **Adaptive** variants tune the limit automatically from observed latency (AIMD, like TCP congestion control — e.g. Netflix's concurrency-limits library, Envoy's adaptive concurrency).

- **Why it beats a static RPS cap for saturation:** it tracks the resource that actually runs out (workers, connections) and self-adjusts as request mix and downstream latency change, so it doesn't need a human retuning it after every dependency slowdown.
- **Cost:** a small added latency for limit computation; some tail requests shed during adaptation.
- **Failure mode:** queue in front of the limit is unbounded (memory blows up instead of shedding); adaptation window too slow to react to a fast spike.
- **Where:** in-process, or a mesh sidecar.

## Queue + backpressure

**What it is:** absorb bursts in a bounded buffer and process at a sustainable rate; when the buffer is full, *push back* — reject at the producer, or signal upstream to slow down.

- **Bounded, always.** An unbounded queue doesn't solve overload — it hides it, adds latency (old items), and adds memory exhaustion as a fresh failure mode. The bound is the point: full queue → backpressure.
- **Backpressure signal:** synchronous callers get a 429/503; internal producers get an explicit slow-down (reactive streams, blocking put with timeout, credit-based flow control).
- **Fits:** work that must not be lost and tolerates delay (analytics, webhook processing, jobs).
- **Failure mode:** unbounded queue; queue that accepts faster than any possible drain rate (permanent backlog); no dead-letter path for poison items.
- **Where:** in-process for in-memory work queues; a broker (SQS, Kafka, RabbitMQ) for cross-service async — with `data-tier-operations` if the broker itself needs scaling.

## Circuit breaker

**What it is:** a wrapper around an outbound call that tracks failures and, past a threshold, **opens** — failing calls instantly without attempting them — then periodically **half-opens** to test recovery, and **closes** on success.

- **States:** closed (normal), open (fail fast, don't call), half-open (let one/few through to probe).
- **Parameters:** failure threshold (count or rate, over a window), open duration before half-open, success count to close, what counts as a failure (timeouts and 5xx yes; 4xx no).
- **The point:** stop pouring requests (and holding threads) into a dependency that's already down — give it room to recover, and free your own resources to serve traffic that doesn't need it.
- **Only as good as the fallback.** Open breaker + a cached/default/skip fallback = graceful degradation. Open breaker + no fallback = the user gets an error faster. Still worth it to free resources, but it's not "resilience" from the user's side — that needs capacity or front-door shedding.
- **Failure mode:** thresholds so tight it flaps (open/close/open) on normal variance; wrapping a hard-required call and calling the fast-failure "handled"; per-instance state so the breaker opens unevenly across the fleet.
- **Where:** in-process (with the real fallback), or a mesh via outlier detection (ejects bad endpoints — breaker-like, no fallback logic).

## Timeout + retry budget + backoff/jitter

- **Timeout on every outbound call** — non-negotiable. Base it on the dependency's p99 plus headroom, not its p50. No timeout = one slow dependency blocks every worker = cascade.
- **Retry budget** — cap retries to a small fraction of total calls (e.g. 10%). Uncapped retries against a struggling dependency are a load multiplier — the retry storm that turns a 2-second blip into a 20-minute outage.
- **Backoff with jitter** — exponential backoff spaces retries out; **jitter** (randomised delay) stops every client that failed at the same instant retrying in the same instant (the thundering herd / retry synchronisation).
- **Retry only:** transient errors, timeouts, connection failures — and only for **idempotent** operations. Never retry a 4xx, never retry a circuit-open, never retry a non-idempotent write without an idempotency key.
- **Often: zero retries.** A fallback plus a client-side 503 retry is frequently more robust than server-side retries.

## Bulkhead

**What it is:** partition resources (thread pools, connection pools, queues) so failure or saturation in one partition can't consume the resources another partition needs. Named after ship compartments.

- **Typical use:** a dedicated worker pool + DB connection allocation for tier-1 paths, separate from tier-2/3. A slow recommendations dependency saturating its pool then cannot starve checkout.
- **Cost:** lower peak utilisation — reserved capacity sits idle when its partition is quiet. That idle capacity *is* the insurance.
- **Failure mode:** partitions sized without headroom (tier-1 bulkhead too small for a tier-1 spike); shared resource sneaks in below the partition (one connection pool behind both).
- **Where:** in-process (pools), or separate deployments/instances for hard isolation.

## Graceful degradation

**What it is:** the composed result of fallbacks — the system does less, but stays up and keeps serving its core function. Recommendations vanish, personalisation goes generic, search falls back to a simpler index, the page renders without the live inventory badge — but the user can still complete the core task.

- **Design it per feature, ahead of time.** "What does this page do when service X is down?" answered in design, not discovered in an incident.
- **Make it visible in tests** — a test suite that runs with each dependency forced down and asserts the core path still completes.

---

## Not here: failover and replication

Automatic **failover** (primary → standby promotion, multi-AZ database HA) and **data replication / backup** are infrastructure-HA controls, not app-request-path protection. They live with the store: `data-tier-operations` owns DB replica topology, failover, and RPO/RTO. This skill's job starts at the app boundary — timeouts and breakers on the *call* to a store or dependency, bulkheads around it, and a degradation plan for when it's gone regardless of whether failover eventually recovers it. `Fault Tolerance.md`'s "isolation / containment" maps to **bulkhead** above; its "monitoring / alerting" is `observability-strategy`.

---

## Shed vs scale

They solve different halves of the same problem:

| | Load shedding / admission control | Autoscaling / capacity |
|---|---|---|
| **Reaction time** | Immediate (milliseconds) | Minutes (provision, boot, warm, join pool) |
| **Covers** | The gap between a spike arriving and capacity catching up; ceilings you *can't* scale (third-party quotas, licensed DB cores, a single-writer DB) | Sustained higher load; growth |
| **Cost** | Dropped/delayed sheddable traffic | The headroom bill → `technical-cost-decision` |

Shedding is the floor that keeps tier-1 alive no matter what. Autoscaling is how you stop shedding once the load is understood to be real. You need both; a design that names only one has a hole.

---

## Placement table

The "Service mesh" column only applies if one exists — whether to adopt one at all is `service-mesh-adoption`'s decision, not this file's. If there's no mesh, that column's controls fall to API gateway or in-process instead.

| Control | Edge / CDN / L7 LB | API gateway | Service mesh | In-process |
|---|---|---|---|---|
| Global rate limit | ✔ (crude) | ✔ | | ✔ (cost-aware) |
| Per-client / per-key rate limit | | ✔ (best fit) | ✔ (per pair) | ✔ |
| Concurrency / adaptive concurrency | | | ✔ | ✔ (best fit) |
| Priority-aware shedding | | | | ✔ (needs internal signal) |
| Circuit breaker **with fallback** | | | partial (outlier detection, no fallback) | ✔ (best fit) |
| Timeouts | | ✔ | ✔ | ✔ |
| Retry budget + jitter | | ✔ | ✔ | ✔ |
| Bulkhead | | | partial | ✔ (best fit) |
| Queue + backpressure | | | | ✔ / broker |
| IP blocking / connection limits | ✔ (best fit) | ✔ | | |

Rule: a control belongs where the signal it reacts to is visible and where it can act cheaply. Layer them — coarse and client-attributable at the gateway/edge, saturation-aware and dependency-specific in-process.
