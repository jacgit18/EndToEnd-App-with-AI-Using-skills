# Observability Framework

Work these in order once the gate in `SKILL.md` is satisfied. Each step produces a written line; the collected lines become the recommendation block and the ADR's Context and Decision.

## 1. Confirm the pressure, name the unanswerable questions

Restate the gate's pressure (item 4) in one sentence. Then write the **specific production questions the current setup cannot answer** — these are the acceptance criteria for the whole design.

- "When a charge fails, which of the 5 dependencies caused it, without reading 5 log streams by hand."
- "Is the p99 regression from last Tuesday's deploy still present, and on which route."
- "Are we inside our error budget this month."

If the only questions are vague ("is it healthy?"), push back to the gate — you cannot design signals for an undefined question.

## 2. Define SLIs, then decide on SLOs

**SLIs** — for each thing a user or calling system depends on (gate item 5), pick the indicator and the measurement point:

| Workload type | SLIs | Method |
|---|---|---|
| Request/response (API, page) | request rate, error rate, duration (p50/p95/p99) | **RED** — measured at the service edge, per critical route |
| Resource / infrastructure | utilization, saturation, errors | **USE** — per resource (CPU, memory, disk, connection pool) |
| Batch / async job | completion time, success/failure, records processed, lag | job-level, not per-request |
| Pipeline / stream | end-to-end lag, throughput, drop/DLQ rate | per stage |

Measure SLIs where the user experiences them (the edge), not deep in the stack where the number looks better.

For the concrete measurements that fill each method bucket — TTFB vs latency vs response time, throughput, request rate, error rate, concurrent connections, cache hit ratio, MTBF/MTTR, SLA compliance — see the service-metric menu in `signals-and-slos.md`. Pick the few that map to something a user feels; chart the rest.

**SLOs** — set an objective + error budget **only** where gate item 6 gave a real commitment (a customer SLA, an internal target with teeth). Format: "99.9% of charges succeed over a rolling 28 days" → 0.1% monthly error budget → burn-rate alerts. Where nothing depends on a number, skip the SLO and just chart the SLI. Setting SLOs nobody is accountable to trains the team to ignore them.

## 3. Choose signal investment against the architecture

From gate item 7 (hop count, sync/async) and `signals-and-slos.md`:

| Signal | Default | Add / skip based on |
|---|---|---|
| **Metrics** | always | the SLIs from step 2 drive which; add USE metrics for the constrained resources |
| **Structured logs** | always | convert text logs to structured; a request/trace ID field is mandatory. This is the floor. |
| **Distributed tracing** | **add when** a typical request crosses ~3+ services or significant queue-based async or a fan-out | skip for a monolith or a 2-hop path — a propagated request ID in structured logs answers the same questions far cheaper |
| **Continuous profiling** | off by default | add only for a known CPU- or memory-bound hot path where step 1's question is "why is this function slow in prod" |
| **Events / audit stream** | off by default | add when there's a discrete-fact record need (state changes, security-relevant actions) that logs handle badly |

Write which signals are in, which are out, and the one-line reason for each — tied to step 1's questions and the hop count.

## 4. Instrumentation approach

- **Default: OpenTelemetry SDK + auto-instrumentation** for the language, for vendor neutrality and one pipeline for all three signals. Manual spans/attributes where the auto coverage misses something that matters (a specific external call, a business-meaningful unit of work).
- **Vendor agent** is a reasonable *first* step when the team (gate item 10) can't yet own an OTel collector — but name OTel as the migration target so instrumentation isn't rewritten later.
- **Collector topology** — agent/sidecar per host or task (collect + batch + enrich), optionally a gateway tier for central processing (tail sampling, redaction, routing). State which.
- **Redaction** — if gate item 9 named PII, the collector (or SDK processors) strips it before export; name where that happens.

## 5. Sampling and cardinality budget

**Sampling** (from gate item 8 volume):

- **Traces** — *tail-based* (decide after the trace completes: keep all errors, all slow outliers, all of specific routes, plus a small % of the rest) is the high-value default above trivial volume. *Head-based* at a fixed low rate is simpler but discards the interesting tails. 100% is only sane at very low RPS.
- **Logs** — level policy: INFO+ retained, DEBUG on-demand or short-TTL; sample high-volume repetitive lines (health checks, retries).

**Cardinality budget** — this is the hidden cost driver (a metric with a `user_id` label becomes N time series). Write:

- The **allow-list** of metric labels (route, method, status class, dependency name — bounded sets).
- The dimensions deliberately kept OUT of metrics (user/tenant/merchant/device ID, full URL, error message) — these live on **traces and logs**, where they're queryable without multiplying series.
- Log-field discipline: a named set of structured fields, not arbitrary per-call keys.

## 6. Alerting policy

- **Page a human** on *symptoms the user feels*: SLO burn rate (fast-burn and slow-burn windows), error-rate spike on a critical path, availability drop, hard latency-budget breach.
- **Ticket / dashboard** for *causes*: CPU, memory, disk, queue depth, connection-pool saturation, elevated dependency latency that hasn't yet moved an SLI.
- Every alert names an **owner** and links a **runbook** (even a stub). An alert with no runbook is a 3am puzzle.
- State the target signal-to-noise: e.g. "if fewer than ~1 in 3 pages is actionable, the policy is wrong — revisit."

## 7. Retention tiers per signal

From how far back gate item 9 said investigations and audits actually look:

| Signal | Typical shape | Driven by |
|---|---|---|
| Metrics | full resolution days → downsampled 13–15 months | trend comparison, capacity planning |
| Logs | 2–30 days hot (searchable) → cold/archive months–years | incident window; audit/chargeback/regulatory hold |
| Traces | 3–14 days | incidents are investigated fresh; traces age out fast |

Longer retention is a linear storage cost — justify each tier against a real lookback need, not "just in case".

## 8. Placement — self-hosted vs managed

- **Managed** (Datadog, New Relic, Honeycomb, Grafana Cloud, Chronosphere, …) — the default when the team is small, there's no platform group, or an SLA makes "our monitoring is also down" unacceptable. Cost scales with ingest/hosts/series.
- **Self-hosted** (OTel Collector + Prometheus/Mimir + Grafana + Loki + Tempo/Jaeger) — justified at scale where managed ingest pricing dominates, or when data residency / air-gap (gate item 9) forbids a third party, *and* there is capacity (gate item 10) to run it HA.
- Data residency from gate item 9 can force in-region managed or self-hosted outright.

State the choice and the components; hand the **dollar comparison** (ingest GB/day, active series, spans/day, host count × each option's pricing) to `technical-cost-decision`.

## 9. Observe the observability, set the revisit trigger

- Metrics on the pipeline itself: ingest volume/day, active series count, trace sampling effective rate, dropped-spans, log bill trend, alert-to-incident ratio.
- The **revisit trigger** for the ADR — the concrete condition that reopens this decision (a new service in the critical path, a cost threshold, an SLO introduction, a volume step-change, a paging-noise threshold).

## 10. Recommend and record

Produce the recommendation block from `SKILL.md`. On approval, write the ADR from `database-architecture`'s `adr-template.md` to `docs/architecture/decisions/NNN-<slug>.md`, referencing any related `microservices-decision` / `technical-cost-decision` ADR.
